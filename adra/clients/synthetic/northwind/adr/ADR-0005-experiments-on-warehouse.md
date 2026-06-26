# ADR-0005 — Experiments run on the shared SQL warehouse; 8-point access preflight

**Status:** Accepted

## Context
Ad-hoc validation that spins up interactive clusters is slow and costly, and
"no access to this catalog" is often concluded prematurely (wrong profile, stopped
warehouse, missing grant) instead of diagnosed.

## Decision
- Validation experiments use the **shared SQL warehouse** via
  `databricks api post /api/2.0/sql/statements`; do not create interactive clusters.
- A hypothesis is **falsifiable**, carries a probability and an impact-if-true, and
  is tied to a **standalone probe**; raw rows are persisted (`runs/*.json`).
- Conclude only what the rows support; record discarded hypotheses with data too.

### The 8-point access preflight (exhaust before declaring "no access")
1. Profile matches the catalog env (`prod` for `prod_*`, `dev` for `dev_*`).
2. `databricks current-user me --profile <p>` returns the expected user.
3. `warehouse_id` is valid for the profile and is `RUNNING`.
4. The catalog exists in that workspace (`SHOW CATALOGS`).
5. The schema exists (`SHOW SCHEMAS IN <catalog>`).
6. The table exists (`SHOW TABLES IN <catalog>.<schema>`).
7. `current_user` is a member of the granting group (`is_member(...)`).
8. If the warehouse runs as a service principal, the SP has the grant.

## Consequences
- Reproducible, cheap experiments; "no access" becomes a diagnosis, not a guess.
- See `cases/CASE-2024-052`.
