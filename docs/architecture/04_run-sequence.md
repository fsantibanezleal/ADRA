# 04 · A run, step by step (`pr_eval`)

This traces one concrete run from intake to the written `RunRecord`, using the `pr_eval` skill on
the stale-base PR that the offline demo (`scripts/demo_offline.py`) exercises. It is the same
sequence for every skill — only the grounding tools and the prompt differ.

Read order: 03 → **04** → 05. Landing: [architecture.md](./architecture.md).

## The sequence

![pr_eval run, step by step](../images/run_sequence.svg)

### 0 · Intake

```json
{
  "source_branch": "task/NDP-1487/current-state-table",
  "target_branch": "main",
  "objective": "Split current-state table creation into its own parallel task.",
  "git_fixture": {"behind": 12,
                  "deletions": ["refined/nb-priority-coverage.py"],
                  "renames": ["R100\trefs.yml\trefs.yml.t"]},
  "bundle_fixture": {"stdout": "Error: schema resource not found", "returncode": 1},
  "pr_body_draft": "Objective: split task. Validation: looks fine."
}
```

The `*_fixture` keys let the deterministic tools exercise the **exact same decision logic**
offline as they would against a live repo (see
[data-contract/04_missing-and-outlier-data.md](../data-contract/04_missing-and-outlier-data.md)).

### 1 · `plan`

`PrEvalSkill.plan` declares the tools: `merge_base_health`, `bundle_validate`, `lang_scan`. The
orchestrator records a `plan` event with the resolved plan model id.

### 2 · `ground` (deterministic — no LLM)

| Tool | Reads | Produces |
|---|---|---|
| `git_tools.merge_base_health` | the `git_fixture` (or a real repo) | MAJOR *stale merge-base* (`behind=12`), BLOCKER *destructive deletion*, BLOCKER *dropped bundle resource* (`.yml → .yml.t`). |
| `bundle_tools.bundle_validate` | the `bundle_fixture` | BLOCKER — `databricks bundle validate` did not return `Validation OK`. |
| `lang_tools.scan_language` | `pr_body_draft` | clean here (English, no leak). |

These `ToolResult`s land in `state.grounding` and are logged as a `ground` event.

### 3 · `generate`

`PrEvalSkill.generate` asks the model for a verdict + a structured PR body, given the grounding.
**The model cannot override the floor:** the skill forces `verdict = "changes-requested"`
whenever any grounding tool reports a blocker, regardless of what the model returned. Offline,
the mock returns a thin "see deterministic grounding for blockers" body.

### 4 · `CRITIC` (blocking)

`critic.criticize` runs:
- **deterministic_attacks** — collects the blocking findings already in `state.grounding`
  (stale base, deletion, dropped resource, failed `bundle validate`) plus critic-level rubric
  checks, and scans the draft text for AI-leak / unverified-claim language.
- **llm_critique** — semantic attacks the deterministic pass cannot encode.

Blocking findings are deduped by `(category, message)`. Because blockers survive, `verdict.clean
== False`.

### 5 · `revise` ↔ CRITIC, bounded by `max_rounds`

The loop revises and re-criticizes. The default `revise` records the unresolved blockers on the
draft (it cannot mask them); with the offline mock the blockers cannot actually be fixed, so the
loop exhausts `max_rounds` (default 3).

### 6 · `decide` + finalize + write

`state.rounds >= max_rounds` with surviving blockers → `decision = "escalate"`.
`PrEvalSkill.finalize` renders `pr_verdict.md` (`changes-requested (escalate)`) and `pr_body.md`.
The `RunRecord` is written to `runs/<run_id>.json` with every step's payload.

## The clean-path contrast

Run the same skill on a fresh branch with a passing `bundle_fixture` and an English body: the
grounding tools raise no blockers, the critic's deterministic pass is empty, the LLM pass returns
clean, and `decision = "accepted"` on the first critic pass. The decision branch is the whole
point — **escalation is correct behaviour, not failure** (ADR-0005).

## See also

- [05_why-deterministic-first.md](./05_why-deterministic-first.md) — why the floor, not the
  model, decided this run.
- [use-cases/02_pr-eval.md](../use-cases/02_pr-eval.md) — the `pr_eval` skill in depth.
- [guides/02_the-cli.md](../guides/02_the-cli.md) — reproduce this with `python scripts/demo_offline.py`.
