# The emulator — a real, self-contained platform offline

`adra/connectors/emulator.py` is a self-contained platform that implements the **same connector
Protocol** as the real adapters, so the full ADRA flow runs offline with no external dependency —
**not a toy** (ADR-0008). It is two classes:

- `EmulatorRepo` — a synthetic `RepoProvider` over `SYNTHETIC_PRS`.
- `EmulatorData` — a real, seeded **SQLite** `DataProvider` (`sqlite3`, `:memory:`).

Landing: [05_stdlib-emulator.md](./05_stdlib-emulator.md).

## The synthetic PRs (`SYNTHETIC_PRS`)

Four multi-industry pull requests, each carrying a **real failure mode the deterministic floor
catches even offline**:

| PR | Industry | Planted flaw | Caught by |
|---|---|---|---|
| 101 | fintech | `# Co-Authored-By: Claude` (AI-leak) + a `*_test.py` suffix (CI never collects) + a swallowed `except Exception: pass` + `Ran 0 tests / No data was collected` | `lang_scan` (BLOCKER) · `test_discovery` (MAJOR) · `ci_command` (BLOCKER) · semantic critic (swallowed error) |
| 102 | ecommerce | stale base (8 behind) + a notebook deletion + a `.yml → .yml.t` rename + failing `bundle validate` | `merge_base_health` (MAJOR + BLOCKER + BLOCKER) · `bundle_validate` (BLOCKER) |
| 103 | healthtech | Spanish comment (`# esta funcion exporta sin validar…`) + a consent `TODO` | `lang_scan` (MAJOR) · semantic critic (contract / consent) |
| 104 | logistics | a downstream-consumed schema column added (`contract change`) | semantic critic (contract drift) |

The fixtures (`git_state` / `ci`) reproduce the failure modes deterministically — same decision
logic as a live repo (see [../../data-contract/04_missing-and-outlier-data.md](../../data-contract/04_missing-and-outlier-data.md)).

`EmulatorRepo` implements `list_pull_requests`, `get_pull_request(number)`, and the gated
writes (`create_issue`, `comment_on_pull_request`) as no-op stubs returning `emulator://…` URLs.

## The seeded warehouse (`EmulatorData`)

A real SQLite database built from `SEED_SQL` on construction (one small table per industry:
`payments_settlement`, `catalog_items`, `telemetry_routes`). `run_sql(sql)` executes the SQL and
returns `{"columns", "rows"}` — the same `DataProvider` shape as Databricks/Azure, so the
`experiment` skill's probe runner works unchanged.

## Driving it from the CLI

```bash
adra emu list                 # list the 4 synthetic PRs
adra emu review 102           # run pr_eval over the stale-base PR (blocked + escalated)
adra emu review 101 --skill code_review
```

`cli/__main__.py` wires the emulator via `get_repo_provider({"provider": "emulator"})` and the
intake builders, exactly as the GitHub path does.

## Why this matters

The emulator is what makes the offline claim real: the public demo and the test fixtures use it,
so there is **no external dependency and no toy** — the deterministic floor produces genuine
adversarial outcomes (blocks + escalations) against synthetic-but-realistic artifacts. Add an
industry by appending to `SYNTHETIC_PRS` / `SEED_SQL`.

## What this IS and is NOT

- **IS** a Protocol-conformant, offline stand-in for a real platform, with planted, catchable
  flaws and a real (seeded) SQL warehouse.
- **IS NOT** a mock that fakes verdicts — the verdicts come from the deterministic tools running
  against the fixtures.

## See also

- [../../architecture/04_run-sequence.md](../../architecture/04_run-sequence.md) — the same loop
  the emulator drives.
- [../../data-contract/02_connector-shapes.md](../../data-contract/02_connector-shapes.md) — the
  Protocol it implements.
- [../../guides/02_the-cli.md](../../guides/02_the-cli.md) — `adra emu`.
