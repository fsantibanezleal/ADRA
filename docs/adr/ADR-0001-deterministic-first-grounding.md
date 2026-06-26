# ADR-0001 — Deterministic-first grounding

**Status:** Accepted

## Context
LLM reviewers that let the model be the final arbiter leak hallucinated and
"consistently-stated-but-false" verdicts. High-precision signal already exists in
deterministic tools (git merge-base, the exact CI command, static analysis, SQL probes).

## Decision
Deterministic tools run **before** the LLM and become both (a) the grounding the model may
not contradict and (b) the evidence in the provenance log. A blocking finding raised by a
tool stands regardless of the model's opinion. The LLM only adds what tools cannot settle
(semantic defects: swallowed errors, contract drift, hidden coupling).

## Consequences
- Verdicts carry evidence, not opinion; the offline path (mock provider) still produces a
  real adversarial outcome because the deterministic floor carries it.
- The whole loop — and the test suite — runs with no API key.
- New deterministic signal is added as a tool returning a typed `ToolResult`.
