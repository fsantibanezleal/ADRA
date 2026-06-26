# databricks-sdk — usage & safety

`adra/connectors/databricks.py` defines `DatabricksData`, a read-only `DataProvider` over the
Databricks SQL **Statement Execution API**.

Landing: [03_databricks-sdk.md](./03_databricks-sdk.md).

## Construction & auth

```python
DatabricksData(warehouse_id=None, *, host=None, token=None,
               catalog=None, schema=None, wait_timeout="30s", allow_external=False)
```

- `from databricks.sdk import WorkspaceClient` is inside `__init__`; missing →
  `RuntimeError("... pip install adra[databricks] (databricks-sdk).")`.
- **Warehouse id is required**: `warehouse_id=` or `DATABRICKS_WAREHOUSE_ID`; absent →
  `RuntimeError`.
- **Auth chain**: `host` / `token` from args or `DATABRICKS_HOST` / `DATABRICKS_TOKEN`; the SDK's
  unified config then resolves the rest (profile, OAuth, Azure CLI…). Construction failure →
  `RuntimeError(f"Databricks auth failed (no usable credentials): {exc}")`.

## The read path

```python
provider.run_sql("SELECT count(*) FROM prod_orders_fulfilment.refined.order_stream")
# -> {"columns": [...], "rows": [[...]]}
```

`run_sql` calls `statement_execution.execute_statement(statement=, warehouse_id=, catalog=,
schema=, wait_timeout=)`, checks `status.state` (raises on `StatementState.FAILED` with the error
message), and maps the response with `_to_table` (schema column names + `result.data_array` →
`{"columns", "rows"}`).

## Read-only, defended in depth

ADRA never writes to the warehouse. Two layers enforce it (ADR-0008 / security doctrine):

1. **Grant-level (recommended, deterministic):** back the connector with a **SELECT-only service
   principal**. This is the real boundary — RBAC, not agent logic.
2. **In-loop guard (defence in depth):** `_guard` rejects statements whose first token is in
   `_FORBIDDEN_PREFIXES` (`insert, update, delete, merge, drop, truncate, alter, create, replace,
   grant, revoke, copy, call, use`) with a `PermissionError`, unless `allow_external=True` (a
   deliberate, human-confirmed exception).

## Gotchas

- **The connector ≠ the deterministic SQL tool.** `adra/tools/sql_tools.py` (used by the offline
  `experiment` loop) shells to the `databricks` CLI or replays a fixture and encodes the 8-point
  access `PREFLIGHT` (so "no access" is never concluded without exhausting profile/warehouse/grants).
  `DatabricksData` is the live SDK-based `DataProvider`. Same read-only posture, different layer.
- **Warehouse, not cluster.** Probes run on a SQL warehouse — no interactive cluster spin-up.
- **`wait_timeout` default `30s`** bounds a probe; a long query returns a failed/timed state, not a
  hang.
- **Missing dep / creds / warehouse all raise clearly** — never an opaque error.

## What this IS and is NOT

- **IS** a read-only experiment probe surface with a grant-level boundary and an in-process guard.
- **IS NOT** a write path or a general Databricks client.

## See also

- [../../use-cases/03_experiment.md](../../use-cases/03_experiment.md) — the experiment skill.
- [../05_stdlib-emulator/05_stdlib-emulator.md](../05_stdlib-emulator/05_stdlib-emulator.md) — the
  offline SQLite warehouse (`EmulatorData`) that runs the same probes with no Databricks.
- [../../data-contract/04_missing-and-outlier-data.md](../../data-contract/04_missing-and-outlier-data.md)
  — the access preflight and degrade lanes.
