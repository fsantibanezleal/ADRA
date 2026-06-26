# 03 · The shared, typed rubric

`adra/rubric.py` is the **single source of the adversarial criteria**. Each criterion is a frozen
`RubricItem` — data, not code — and it is consumed in two places so "what we check" can never
diverge between the code and the prompt (ADR-0004; inspired by Constitutional AI's critique against
written principles).

Read order: 02 → **03** → 04. Landing: [methodologies.md](./methodologies.md).

## The `RubricItem` shape

```python
@dataclass(frozen=True)
class RubricItem:
    id: str            # stable id, e.g. "stale_merge_base"
    title: str
    severity: Severity # BLOCKER | MAJOR | MINOR | NIT
    category: str      # machine label shared with Finding
    kind: str          # "deterministic" (a tool/critic settles it) | "semantic" (LLM judges it)
    applies_to: tuple  # skills it applies to; empty == all skills (cross-cutting)
    method: str        # the operational check — also shown to the LLM
    incident: str      # the (anonymized, illustrative) incident case it encodes
```

Each item is **tied to an illustrative incident case** (`incident`), which keeps the rubric grounded in
concrete failures rather than abstract style preferences.

## Two consumers, one source (no drift)

![Shared rubric — checks and prompts](../images/rubric_sources.svg)

- **`deterministic_findings` / the critic's hard floor** — items with `kind == "deterministic"`
  are enforced **mechanically** (by a tool or by `critic.deterministic_attacks`). A tool builds
  its `Finding` text from the rubric (`RubricItem.to_finding`), so messages are single-sourced.
- **`prompt_block(skill)`** — renders the items applicable to a skill into the critic's system
  prompt, tagged `MUST-BLOCK` (blocking severity) or `FLAG`, with the learned incident. So the LLM
  pass attacks the *same* criteria the deterministic pass enforces.

`for_skill(skill, kind=None)` selects the applicable items (cross-cutting items — empty
`applies_to` — always included). This is the mechanism that makes "code and prompt can't drift" a
structural guarantee, not a discipline.

## The criteria (id → where it bites)

| id | severity · kind | applies to |
|---|---|---|
| `stale_merge_base` | MAJOR · deterministic | pr_eval |
| `destructive_deletions` | BLOCKER · deterministic | pr_eval, code_review |
| `dropped_bundle_resource` | BLOCKER · deterministic | pr_eval |
| `bundle_validate` | BLOCKER · deterministic | pr_eval |
| `exact_ci_repro` | MAJOR · deterministic | code_review, pr_eval |
| `zero_tests_no_data` | BLOCKER · deterministic | code_review |
| `test_discoverability` | MAJOR · deterministic | code_review |
| `unverified_claim` | MAJOR · deterministic | all |
| `unverifiable_no_access` | MAJOR · deterministic | experiment |
| `conclusion_beyond_evidence` | MAJOR · semantic | experiment |
| `convention_conformance` | MAJOR · semantic | pr_eval, improve |
| `contract_drift` | MAJOR · semantic | code_review, pr_eval |
| `swallowed_error` | MAJOR · semantic | code_review |
| `minimum_functional` | MINOR · semantic | improve, code_review |
| `blast_radius` | MAJOR · semantic | decide, pr_eval |
| `language_leak` | BLOCKER · deterministic | all |
| `overclaim_language` | MAJOR · semantic | document, code_review, experiment |

## Rubric ↔ client standards

Each item's `incident` references a **client standard** (`ADR-xxxx` / `CASE-xxxx`) in the active
client governance suite. The rubric references them by id; the prompts cite them. **Retargeting a
client** is `ADRA_CLIENT_DIR` + updating the incident references — no engine code changes
(ADR-0007). See [../use-cases/use-cases.md](../use-cases/use-cases.md) and
[../guides/04_retarget-a-client.md](../guides/04_retarget-a-client.md).

## What this IS and is NOT

- **IS** one typed, incident-grounded source of the criteria, consumed by both the deterministic
  checks and the critic prompt.
- **IS NOT** a static linter config. Deterministic items are enforced mechanically; semantic items
  are adversarially judged; both come from the same list.

## Extending

Add a `RubricItem` to `RUBRIC`. Semantic items are auto-injected into the critic prompt; for a
`deterministic` item, wire its check in `critic.deterministic_attacks` or a tool.

## References

Constitutional AI (Bai 2022, `arXiv:2212.08073`) — critiquing against an explicit written set of
principles. See [../../refs/README.md](../../refs/README.md) §2.

## See also

- [01_adversarial-spine.md](./01_adversarial-spine.md) · [04_deterministic-first.md](./04_deterministic-first.md)
- [../adr/ADR-0004-shared-typed-rubric.md](../adr/ADR-0004-shared-typed-rubric.md)
- [../data-contract/04_missing-and-outlier-data.md](../data-contract/04_missing-and-outlier-data.md)
  — how the gating items handle missing/outlier inputs.
