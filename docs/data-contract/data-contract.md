# Data contract

The exact shapes that cross ADRA's boundaries: the **intake** a caller supplies per skill, the
**connector** shapes (`PullRequest` / `Issue` / `DataProvider`), the immutable **`RunRecord`**
(provenance), and — critically — **how missing / outlier data is handled** (degrade lanes, gating).

## Read in order

1. [01_intake-contracts.md](./01_intake-contracts.md) — the per-skill intake dicts (diff / PR /
   experiment / improve / document / decide), required vs optional fields, units.
2. [02_connector-shapes.md](./02_connector-shapes.md) — the `RepoProvider` / `DataProvider`
   Protocols and the `PullRequest` / `Issue` dataclasses; the intake builders.
3. [03_run-record.md](./03_run-record.md) — the immutable `RunRecord` schema (the deep
   change-history / evidence layer) and the typed domain model it serializes.
4. [04_missing-and-outlier-data.md](./04_missing-and-outlier-data.md) — degrade lanes
   (`ran=False`), NaN-safe predicates, the access preflight, fixtures, and the gating that turns a
   data gap into an honest "unknown" instead of a fabricated answer.

## The one contract

Everything internal is a dataclass from `adra/state.py` — `Severity`, `Finding`, `ToolResult`,
`CriticVerdict`, `RunState` — and all of them are JSON-serializable. The **intake** is the only
loosely-typed boundary (a `dict` the caller supplies); each skill documents exactly which keys it
reads. Output **artifacts** are markdown strings keyed by filename in `state.artifacts`.

| Boundary | Shape | Page |
|---|---|---|
| caller → engine | `intake: dict` (per skill) | [01](./01_intake-contracts.md) |
| platform → engine | `PullRequest` / `Issue` / `{"columns","rows"}` | [02](./02_connector-shapes.md) |
| tool → critic / record | `ToolResult` (+ `Finding`) | [03](./03_run-record.md) · [../architecture/03_data-flow.md](../architecture/03_data-flow.md) |
| engine → disk | `RunRecord` → `runs/<id>.json` | [03](./03_run-record.md) |

## What this section IS and is NOT

- **IS** a field-level spec of every input and output, verified against the dataclasses and skill
  code.
- **IS NOT** an API reference for a service. ADRA is a library/CLI; the "contract" is the function
  inputs/outputs and the persisted record.

## See also

- [../architecture/03_data-flow.md](../architecture/03_data-flow.md) — the same contracts in motion.
- [../use-cases/use-cases.md](../use-cases/use-cases.md) — each skill's input/output in context.
- [../security/03_untrusted-content.md](../security/03_untrusted-content.md) — the intake is
  untrusted; how that's handled.
