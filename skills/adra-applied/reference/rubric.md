# Rubric — the portable checks (ADR/CASE-referenced)

Apply these in the critic step. Every `BLOCKER` and `MAJOR` is blocking: if one
survives, the artifact is not clean. Each check cites the architecture decision it
enforces and the incident it was learned from. The checks are portable; client
tokens (catalogs, branches, CI command) are configuration.

## Contents

- Deterministic checks (tools decide)
- Semantic checks (you add, tools cannot settle)
- Severity and verdict rules

## Deterministic checks (tools decide, you may not contradict)

| id | Severity | Check | How | ADR / CASE |
|---|---|---|---|---|
| stale_merge_base | MAJOR | branch behind the production ref | `merge_base_health.py` commits-behind > 0 → rebase/recreate before review | ADR-0002 / 031 |
| destructive_deletions | BLOCKER | files deleted vs merge-base | `merge_base_health.py` flags `D` lines; block until confirmed | ADR-0002 / 031 |
| dropped_bundle_resource | BLOCKER | DAB resource renamed off `.yml` | `merge_base_health.py` flags `.yml`→`.yml.t` (or any non-`.yml`) | ADR-0003 / 031 |
| bundle_validate | BLOCKER | `resources/` changed without a passing validate | `bundle_validate.py` must print `Validation OK!` | ADR-0003 |
| exact_ci_repro | MAJOR | CI not reproduced (approximated) | `run_ci.py` with the repo's exact command | ADR-0001 / 047 |
| zero_tests_no_data | BLOCKER | `Ran 0 tests` / "No data was collected" | `run_ci.py` parse | ADR-0004 / 047 |
| test_discoverability | MAJOR | `*_test.py` suffix, missing `__init__.py`, or logic only in a notebook | discovery in `run_ci.py` / inspect the diff | ADR-0004 / 047 |
| unverified_claim | MAJOR | hedging language in the draft ("probably", "I assume", "should be fine", "no access", "must be because") | `lang_scan.py` / self-review; replace with a probe or "unknown" | ADR-0001 |
| unverifiable_no_access | MAJOR | "no access" claimed without the preflight | `preflight.py` 8/8 before any such claim | ADR-0005 / 052 |
| language_leak | BLOCKER | non-English on disk, or an authoring-tool/vendor mention, or "co-authored-by" / "generated with AI" | `lang_scan.py` | conventions / ADR-0006 |

## Semantic checks (you add; the tools cannot encode these)

| id | Severity | Check | ADR / CASE |
|---|---|---|---|
| conclusion_beyond_evidence | MAJOR | a conclusion the persisted rows do not support | ADR-0001 / 058 |
| convention_conformance | MAJOR | naming / branch / PR-body / medallion conventions violated | ADR-0008 / 061 |
| contract_drift | MAJOR | a published table/column contract widened or changed silently | ADR-0006 |
| swallowed_error | MAJOR | an exception caught and dropped (`except: pass`), a silent fallback | recurring |
| minimum_functional | MINOR→MAJOR | copied filler / speculative scaffolding; dead code removed without proof it is dead | ADR-0008 / 047 |
| blast_radius | MAJOR | a change to shared CI templates / cross-domain libs / prod data without the smallest-scope route considered | ADR-0008 / 061 |
| geoscience_language | BLOCKER | geoscience output framed as event "detection"/"prediction" rather than risk patterns / vulnerability / prioritization | ADR-0007 |

## Severity and verdict rules

- `BLOCKER` and `MAJOR` both block. `MINOR`/`NIT` are advisory.
- Any blocking finding → verdict is **changes requested** (for a PR) or **escalate**
  (for a run), regardless of opinion. Blockers beat opinions.
- The deterministic floor is ground truth: never re-litigate what a tool settled;
  add only what the tools cannot encode.
- Record confirmed and discarded findings with numbers. When you cannot verify,
  write "unknown" — do not assert.

The narrative behind each id (the real incidents) lives in the client governance
suite — `adra/clients/synthetic/northwind/adr/` and `.../cases/` — which
`adra/rubric.py` binds to these ids (single source). Retarget to a different client
by swapping the suite (`ADRA_CLIENT_DIR`), not these ids.
