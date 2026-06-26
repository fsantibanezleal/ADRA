# azure-identity + azure-monitor-query — usage & gotchas

`adra/connectors/azure.py` defines `AzureMonitorData`, a read-only `DataProvider` that runs
**KQL** probes against an Azure Log Analytics workspace.

Landing: [04_azure-identity-monitor.md](./04_azure-identity-monitor.md).

## Construction & auth

```python
AzureMonitorData(workspace_id=None, *, credential=None, timespan_hours=24)
```

- `from azure.identity import DefaultAzureCredential` is inside `__init__`; missing →
  `RuntimeError("... pip install adra[azure] (azure-identity, azure-monitor-query).")`.
- **Workspace id required**: `workspace_id=` or `AZURE_LOG_ANALYTICS_WORKSPACE_ID`; absent →
  `RuntimeError`.
- The credential is `credential or DefaultAzureCredential()`. Constructing it is cheap and **does
  not hit the network** — the token is acquired lazily on the first query, so the connector
  degrades at *query* time if the chain can't resolve a usable identity.
- `LogsQueryClient` is built lazily (`_logs_client`) the first time a probe runs; missing
  `azure-monitor-query` → a clear `RuntimeError` only then.

## The read path

```python
provider.run_sql("AzureMetrics | where TimeGenerated > ago(1h) | summarize count()")
# -> {"columns": [...], "rows": [[...]]}
```

`run_sql` calls `client.query_workspace(workspace_id=, query=kql, timespan=self.timespan)`,
raises on `LogsQueryStatus.FAILURE`, and maps the first table's columns/rows into the engine's
`{"columns", "rows"}` shape (empty dict shape if no tables).

## Gotchas

- **`run_sql` takes KQL, not ANSI SQL.** The method is named `run_sql` only to satisfy the
  `DataProvider` Protocol; passing SQL will fail at the service. The docstring says so explicitly.
- **`timespan` defaults to 24h** (`timespan_hours=24`); scope it for the probe you're running.
- **Lazy everything degrades cleanly:** missing `azure-identity` → error at construction; missing
  `azure-monitor-query` → error only when a KQL probe runs; unusable credentials → a clear error
  from the credential chain at query time, never an opaque failure.
- **Least-privilege credential.** `DefaultAzureCredential` should resolve to an identity with
  read-only Log Analytics access; ADRA never writes.

## What this IS and is NOT

- **IS** a read-only KQL availability/health probe returning the engine's column/row shape.
- **IS NOT** SQL, and **IS NOT** a write path.

## See also

- [../03_databricks-sdk/01_usage-and-safety.md](../03_databricks-sdk/01_usage-and-safety.md) — the
  sibling read-only data provider (Databricks SQL).
- [../../use-cases/03_experiment.md](../../use-cases/03_experiment.md) — the experiment skill that
  consumes a `DataProvider`.
