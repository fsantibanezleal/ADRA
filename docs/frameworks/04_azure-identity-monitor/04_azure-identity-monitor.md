# 04 · azure-identity + azure-monitor-query — cloud-health probes

ADRA's Azure `DataProvider` runs read-only **cloud-health probes** via Log Analytics **KQL**,
using **azure-identity** (a single least-privilege `DefaultAzureCredential`) + **azure-monitor-query**
(`LogsQueryClient`). ADR-0008 chose Log Analytics KQL as the GA availability signal (with
`azure-mgmt-resourcehealth` able to layer on later).

## At a glance

| | |
|---|---|
| Packages | `azure-identity>=1.17`, `azure-monitor-query>=1.3` |
| Install | `pip install adra[azure]` |
| ADRA module | `adra/connectors/azure.py` (`AzureMonitorData`) |
| Implements | the `DataProvider` Protocol — `run_sql(kql)` (dialect is **KQL**, not ANSI SQL) |
| Decision | ADR-0008 |
| Posture | read-only; `DefaultAzureCredential` (least privilege), lazy token acquisition |

## Read in order

1. [01_usage-and-gotchas.md](./01_usage-and-gotchas.md) — construction, the credential chain,
   `run_sql`-takes-KQL, the `{"columns","rows"}` mapping, and the degrade behavior.

## Why these two (ADR-0008)

> Azure via **`azure-identity` + `azure-monitor-query`** (the GA availability signal;
> `azure-mgmt-resourcehealth` can layer on later).

- **One credential, least privilege.** `DefaultAzureCredential` walks the standard Azure auth
  chain (env, managed identity, Azure CLI, …) so the same identity drives every query — no bespoke
  secret handling in ADRA.
- **KQL over Log Analytics is the availability signal** the experiment/maintenance skills want,
  and it's GA (Resource Health can be added later without changing the `DataProvider` contract).
- **Same `DataProvider` shape** as Databricks/emulator (`run_sql → {"columns","rows"}`), so it
  composes with the experiment probe runner — even though the dialect is KQL.

## What this IS and is NOT

- **IS** a read-only health/availability probe surface returning the engine's column/row shape.
- **IS NOT** ANSI SQL (the method is named `run_sql` to satisfy the Protocol; the dialect is KQL)
  and **IS NOT** a write path.

## See also

- [01_usage-and-gotchas.md](./01_usage-and-gotchas.md)
- [../../data-contract/02_connector-shapes.md](../../data-contract/02_connector-shapes.md) — the
  `DataProvider` Protocol.
- [../../security/01_read-only-default.md](../../security/01_read-only-default.md) — the posture.
