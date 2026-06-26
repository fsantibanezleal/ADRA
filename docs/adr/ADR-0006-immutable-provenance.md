# ADR-0006 — Immutable provenance run record

**Status:** Accepted

## Context
Documentation generated from memory drifts. Auditability and the `document` skill both need a
single, factual source of what happened in a run.

## Decision
Every run writes an immutable, append-only `RunRecord` (`adra/provenance.py`): `run_id`,
skill, intake, each step (inputs · tool evidence · critic verdicts), the final decision, and
the artifacts. The `document` skill renders documentation **from the record**, not from
memory. Aligns with internal-algorithmic-auditing, model-card, and W3C-PROV practice.

## Consequences
- Technical / operational / functional history all trace back to one auditable artifact.
- Runs are replayable and diffable; nothing self-reported is taken on faith.
