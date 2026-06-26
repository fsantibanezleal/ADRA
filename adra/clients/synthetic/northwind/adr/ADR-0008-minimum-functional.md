# ADR-0008 — Minimum-functional, smallest reversible change

**Status:** Accepted

## Context
Changes that copy whole templates or add "just in case" scaffolding accumulate dead
code and widen blast radius. Larger diffs are harder to review and to roll back.

## Decision
- Include **only what advances the result**; prune filler even when it was copied
  from a team standard or template.
- Removing code requires **proof it is dead** (not collected by CI discovery,
  unreferenced) — not an assertion.
- Prefer the **smallest, reversible** diff; name the rollback. Assess **blast radius**
  (shared CI templates, cross-domain libraries, prod data) and prefer the
  smallest-scope route (see `cases/CASE-2024-061`).

## Consequences
- Smaller, safer, defensible changes; less dead code.
