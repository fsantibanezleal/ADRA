# ADR-0003 — Bundle resource files stay `.yml`

**Status:** Accepted

## Context
A Databricks Asset Bundle includes resources (jobs, schemas, volumes, pipelines)
declared in `resources/bundle.resources.<kind>.yml`. Renaming such a file to any
other extension (e.g. `.yml.t`) silently removes the resource from the bundle, so a
deploy drops the job/schema/volume without an obvious diff signal.

## Decision
- Resource files **must keep the `.yml` extension**.
- A rename away from `.yml` (e.g. `→ .yml.t`) is a **blocking** finding.
- Any change under `resources/` requires `databricks bundle validate -t <env>`
  returning `Validation OK!` before review (see `ci-standards.md`).

## Consequences
- Bundle composition stays explicit and validated.
- See `cases/CASE-2024-031`.
