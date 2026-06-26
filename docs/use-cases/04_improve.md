# 04 · `improve`

Propose a **minimum-functional** change: keep only what advances the result, prune filler even when
it came from a team standard, and require validation with the **exact CI command**. Output is a
rationale plus the minimal change (a diff sketch).

Landing: [use-cases.md](./use-cases.md). Code: `adra/skills/improve.py`,
prompt `adra/prompts/improve.md`.

## Input → grounding → output

| Stage | Detail |
|---|---|
| **Input** (intake) | `context` (what to improve, as text) |
| **plan** | declares tool: `lang_scan` |
| **ground** (deterministic) | `lang_tools.scan_language(context)` |
| **generate** | model returns `{proposal, rationale, minimal_change, dead_code_removed:[…], validation_command}` — justify every kept element; drop anything that doesn't change a CI result |
| **output** | `proposal.md` — Proposal / Rationale (minimum functional) / Minimal change / Dead code removed / Validation command |

## The rubric items it enforces

| id | severity · kind | what it catches |
|---|---|---|
| `minimum_functional` | MINOR · semantic | filler beyond minimum-functional; **prove** removed code is dead (not collected/unreferenced) rather than asserting it |
| `convention_conformance` | MAJOR · semantic | a change defensible only against an existing precedent |
| `unverified_claim` | MAJOR · deterministic (cross-cutting) | claims (e.g. "this is dead") asserted without a second method |
| `language_leak` | BLOCKER · deterministic (cross-cutting) | English-only + no AI-session leak |

The minimum-functional discipline is grounded in an illustrative incident case (Northwind `CASE-2024-047` / `ADR-0008`): a dead
`*_test.py` suffix file was removed **once proven uncollected**, not on assertion.

## Worked example (offline demo)

Context: "Remove a redundant test file CI never collects." → proposal to remove the file, with the
rationale that it is uncollectable (provable via the test-discovery glob), validated by the exact CI
command → **accepted**.

## Invoke

```bash
adra improve "Remove a redundant test file CI never collects."
```

## What this IS and is NOT

- **IS** the smallest safe diff with every kept element justified and removals proven dead.
- **IS NOT** a refactor-for-its-own-sake proposal. "Prune filler even from a standard" is the
  point; assertions of deadness are rejected without proof.

## See also

- [01_code-review.md](./01_code-review.md) — shares `minimum_functional` / `convention_conformance`.
- [../methodologies/03_shared-rubric.md](../methodologies/03_shared-rubric.md) — the rubric.
- [../data-contract/01_intake-contracts.md](../data-contract/01_intake-contracts.md)
