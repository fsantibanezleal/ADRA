# 01 · `code_review`

Review a diff: deterministic-first (language/leak scan + test-discoverability + the exact CI
command), then the model adds semantic findings on top of that grounded floor. Output is a
structured findings report.

Landing: [use-cases.md](./use-cases.md). Code: `adra/skills/code_review.py`,
prompt `adra/prompts/code_review.md`.

## Input → grounding → output

| Stage | Detail |
|---|---|
| **Input** (intake) | `diff` (required); optional `ci_command` + `ci_fixture` |
| **plan** | declares tools: `lang_scan`, `test_discovery`, `ci_command` |
| **ground** (deterministic) | `lang_tools.scan_language(diff)` · `discovery_tools.check_test_discovery(added_paths(diff))` · `ci_tools.run_ci_command(ci_command, …)` when a command is given |
| **generate** | model returns `{summary, semantic_findings:[{severity,category,message,location}]}` — *only* findings the tools cannot settle |
| **output** | `review.md` — deterministic findings (tool-grounded, with evidence) then semantic findings (model) |

## The rubric items it enforces

From `rubric.for_skill("code_review")` (cross-cutting items included):

| id | severity · kind | what it catches |
|---|---|---|
| `destructive_deletions` | BLOCKER · deterministic | file deletions in the diff that must be confirmed |
| `exact_ci_repro` | MAJOR · deterministic | a "green" verdict requires reproducing the **exact** CI command |
| `zero_tests_no_data` | BLOCKER · deterministic | 0 collected tests → coverage "no data" |
| `test_discoverability` | MAJOR · deterministic | a `*_test.py` suffix the `test*.py` glob never collects (dead code) |
| `contract_drift` | MAJOR · semantic | a change that widens/narrows a public contract |
| `swallowed_error` | MAJOR · semantic | silently swallowed exceptions/timeouts a caller relies on |
| `minimum_functional` | MINOR · semantic | filler beyond what advances the result |
| `unverified_claim` | MAJOR · deterministic (cross-cutting) | a cause/outcome asserted without a second method |
| `language_leak` | BLOCKER · deterministic (cross-cutting) | Spanish content (MAJOR) + AI-session leak (BLOCKER) |
| `overclaim_language` | MAJOR · semantic | "detect/predict/guarantee/prevent" framing |

The critic also forces the **exact-CI** check: in a `code_review`, if `ci_command` did not run
(dry-run), `exact_ci_repro` blocks (`critic.deterministic_attacks`).

## Worked example (offline demo)

The demo feeds a diff with a `*_test.py` suffix, a `# Co-Authored-By: Claude` line, a Spanish
identifier, and a CI fixture of `Ran 0 tests / No data was collected`. Result: **blocked** —
BLOCKER session-leak, MAJOR language, MAJOR test-discoverability, BLOCKER 0-tests/no-data — and
the run escalates.

## Invoke

```bash
adra review my.diff --ci-command 'python -m coverage run -m unittest discover -s . -p "test*.py"'
# add --external (global) to actually run the CI command
```

## What this IS and is NOT

- **IS** a grounded review whose blockers are tool-measured facts; the model only adds semantic
  findings.
- **IS NOT** a model-prose verdict. A deterministic blocker stands regardless of the model.

## See also

- [02_pr-eval.md](./02_pr-eval.md) — the PR-level sibling (adds merge-base + bundle).
- [../methodologies/04_deterministic-first.md](../methodologies/04_deterministic-first.md)
- [../data-contract/01_intake-contracts.md](../data-contract/01_intake-contracts.md) — the `diff` /
  `ci_*` intake.
