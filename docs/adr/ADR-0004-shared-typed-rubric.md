# ADR-0004 — One shared, typed rubric for all adversarial criteria

**Status:** Accepted

## Context
If the criteria the deterministic checks enforce and the criteria the critic prompt asks the
LLM to attack live in two places, they drift. "What we check" must be single-sourced.

## Decision
All adversarial criteria are typed `RubricItem` data in `adra/rubric.py` (id, severity,
category, `kind` = deterministic|semantic, `applies_to`, method, originating incident). The
deterministic critic enforces the `deterministic` items; the same rubric is rendered into the
critic's prompt for the `semantic` items.

## Consequences
- Code and prompt cannot diverge; criteria are version-controlled and explainable.
- Each item is traceable to the (illustrative) incident case it encodes.
- Adding a criterion is one data entry (+ a check, if deterministic).
