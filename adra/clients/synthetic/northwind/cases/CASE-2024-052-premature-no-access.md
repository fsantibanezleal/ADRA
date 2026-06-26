# CASE-2024-052 — "No access" to a catalog, concluded prematurely

**Domain:** `payments` · **Relates to:** ADR-0005

## What happened
An experiment reported "no access to `prod_payments_ledger`" and was closed. In fact
the query had been issued with the `dev` profile against a `prod_*` catalog; the
profile is bound to the workspace, so the grant did not apply.

## Diagnosis (preflight)
Walking the 8-point preflight surfaced it at step 1 (profile/env mismatch). Re-running
with `--profile prod` returned rows immediately.

## Fix / rule
Codified the 8-point access preflight in ADR-0005: never declare "no access" without
exhausting it.
