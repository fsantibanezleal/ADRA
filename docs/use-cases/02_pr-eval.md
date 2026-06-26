# 02 · `pr_eval`

Evaluate a PR: the **first** grounding step is *merge-base health* (a common destructive failure
mode), then `bundle validate` and a language scan. The model produces a verdict and a
structured PR body; **any deterministic blocker forces `changes-requested`** regardless of the
model.

Landing: [use-cases.md](./use-cases.md). Code: `adra/skills/pr_eval.py`,
prompt `adra/prompts/pr_eval.md`.

## Input → grounding → output

| Stage | Detail |
|---|---|
| **Input** (intake) | `source_branch`, `target_branch` (default `develop`/`main`), `objective`; optional `git_fixture`, `bundle_target`, `bundle_fixture`, `pr_body_draft`, `work_item` |
| **plan** | declares tools: `merge_base_health`, `bundle_validate`, `lang_scan` |
| **ground** (deterministic) | `git_tools.merge_base_health(repo, source, target, fixture)` · `bundle_tools.bundle_validate(repo, target, …)` · `lang_tools.scan_language(pr_body_draft)` |
| **generate** | model returns `{verdict:'approve'\|'changes-requested', summary, objective, changes, not_touched, validation, risks, test_plan, work_item}` |
| **enforcement** | `has_blocker = any(r.blocking for r in grounding.values())` → forces `verdict = "changes-requested"` |
| **output** | `pr_verdict.md` + `pr_body.md` (the house PR-body template: Objective / Changes / What is NOT touched / Validation / Risks / Test plan / Work Item) |

## The rubric items it enforces

| id | severity · kind | what it catches |
|---|---|---|
| `stale_merge_base` | MAJOR · deterministic | branch behind a fresh target (`behind`) — rebase/recreate first |
| `destructive_deletions` | BLOCKER · deterministic | a stale-base diff silently removing notebooks/resources |
| `dropped_bundle_resource` | BLOCKER · deterministic | `.yml → .yml.t` rename dropping a DAB resource |
| `bundle_validate` | BLOCKER · deterministic | `databricks bundle validate` not returning `Validation OK` |
| `exact_ci_repro` | MAJOR · deterministic | green requires the exact CI command |
| `convention_conformance` | MAJOR · semantic | a change defensible only against an existing precedent |
| `contract_drift` | MAJOR · semantic | widened/narrowed public contract |
| `blast_radius` | MAJOR · semantic | shared CI templates / cross-domain libs / prod data |
| `unverified_claim` / `language_leak` / `overclaim_language` | cross-cutting | as in [code_review](./01_code-review.md) |

## Worked example (offline demo / emulator PR 102)

A branch 8–12 commits behind `main`, deleting a notebook, renaming a resource `.yml → .yml.t`, with
a failing `bundle validate`. Grounding raises MAJOR stale-base + BLOCKER deletion + BLOCKER dropped
resource + BLOCKER bundle. Verdict forced to `changes-requested`; blockers survive `max_rounds`;
decision **escalate**. This is the reference run traced in
[../architecture/04_run-sequence.md](../architecture/04_run-sequence.md).

## Invoke

```bash
adra pr-eval --source task/NDP-1487/x --target main --repo /path/to/repo   # +--external for live git/bundle
adra emu review 102                                                         # the synthetic stale-base PR
adra github-review owner/repo 42 --skill pr_eval                            # a real GitHub PR (read-only)
```

## What this IS and is NOT

- **IS** a destructive-merge guard with an evidence-backed verdict and a structured PR body.
- **IS NOT** a model deciding merge-readiness. The deterministic floor forces the verdict; the body
  is documentation.

## See also

- [01_code-review.md](./01_code-review.md) · [05_document.md](./05_document.md)
- [../frameworks/02_httpx/01_github.md](../frameworks/02_httpx/01_github.md) — fetching a real PR.
- [../data-contract/01_intake-contracts.md](../data-contract/01_intake-contracts.md)
