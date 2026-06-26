# 03 · databricks-sdk — read-only warehouse probes

**databricks-sdk** (the official Databricks SDK) backs ADRA's read-only **`DataProvider`** for the
`experiment` skill: ad-hoc SQL probes against a SQL warehouse via the **SQL Statement Execution
API**. ADR-0008 chose the SDK (one unified auth for the control plane + SQL) over
`databricks-sql-connector`.

## At a glance

| | |
|---|---|
| Package | `databricks-sdk` |
| Pin | `>=0.30` |
| Install | `pip install adra[databricks]` |
| ADRA module | `adra/connectors/databricks.py` (`DatabricksData`) |
| Implements | the `DataProvider` Protocol (`run_sql(sql) -> {"columns", "rows"}`) |
| Decision | ADR-0008 |
| Posture | **read-only** (SELECT probes); DDL/DML rejected in-loop unless `allow_external` |

## Read in order

1. [01_usage-and-safety.md](./01_usage-and-safety.md) — construction, auth chain, the
   SELECT-only guard, the `_to_table` mapping, and the gotchas.

## Why databricks-sdk (ADR-0008)

> Databricks via **`databricks-sdk` + CLI subprocess** (bundles); … one unified auth for the
> control plane + SQL; we skip `databricks-sql-connector`.

- One SDK resolves the **whole auth chain** (env / profile / OAuth / Azure CLI), so the warehouse
  probe and any future control-plane call share one credential model.
- The **Statement Execution API** runs SQL on a SQL warehouse (no interactive cluster), which is
  exactly the cheap, read-only surface an `experiment` probe needs.
- Degrades clean: a missing SDK, missing credentials, or missing warehouse id raises a clear
  `RuntimeError` at construction/probe time — never an opaque failure.

> Note: the **deterministic SQL tool** used inside the offline loop is `adra/tools/sql_tools.py`,
> which shells out to the `databricks` CLI (or replays a fixture) and encodes the access preflight.
> The **connector** here is the live `DataProvider` the console/connector phase uses. Both honor
> read-only-by-default.

## What this IS and is NOT

- **IS** a read-only experiment-probe surface, defended in depth (a SELECT-only grant *and* an
  in-process mutation guard).
- **IS NOT** a write path. ADRA never issues warehouse writes; mutating statements are rejected
  before they leave the process unless explicitly, deliberately allowed.

## See also

- [01_usage-and-safety.md](./01_usage-and-safety.md)
- [../../use-cases/03_experiment.md](../../use-cases/03_experiment.md) — the skill that probes.
- [../../security/01_read-only-default.md](../../security/01_read-only-default.md) — the posture.
