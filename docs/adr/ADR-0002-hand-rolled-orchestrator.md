# ADR-0002 — Hand-rolled orchestrator, not an agent-framework runtime

**Status:** Accepted

## Context
The control flow `plan → ground → generate → CRITIC → revise → escalate` is fixed at design
time (Anthropic's "evaluator-optimizer" pattern). Agent-graph runtimes (LangGraph, LangChain
agents) add nondeterminism, dependency weight, and an indirection that obscures provenance.

## Decision
The orchestrator is a small, explicit, **framework-free** state machine
(`adra/orchestrator.py`). The critic is mandatory and blocking; the loop revises up to
`max_rounds` then escalates. Every node writes a provenance event.

## Consequences
- The loop's determinism is owned by ADRA, which is the whole point of a deterministic-first
  design; the engine is auditable line-by-line.
- If a future need genuinely requires a dynamic graph, the node contracts are stable enough
  to be wrapped without rewriting the skills.
