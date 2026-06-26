# pydantic-ai — why (the decision)

## The decision (engine ADR-0003)

> **ADRA-owned `ChatModel` seam + native-SDK / pydantic-ai providers (no LangChain).**

The engine needs exactly one thing from an LLM framework: a uniform way to send a
system+user turn to *any* provider and get text back. It does **not** need a framework's agent
graph, memory, tool-routing, or callback machinery — ADRA already owns all of that
(`orchestrator.py`, `rubric.py`, `critic.py`, `judge.py`). So the choice is deliberately
minimal: a tiny `ChatModel` seam over a provider-agnostic model layer.

## Why pydantic-ai over the alternatives

| Option | Verdict | Why |
|---|---|---|
| **pydantic-ai (model layer only), behind a `ChatModel` seam** | ✅ chosen | One `provider:model` string addresses anthropic/openai/groq/mistral/google natively + the OpenAI-compatible long tail. Typed, maintained by the Pydantic team, minimal surface. The seam keeps the engine decoupled from it. |
| **LangChain / LangGraph** | ❌ rejected (ADR-0002, ADR-0003) | A heavy agent runtime would *replace* ADRA's readable, blocking-critic state machine and hide the one property that matters (nothing bypasses the critic). ADRA's loop is ~45 lines; a framework graph is the opposite of that. |
| **A raw per-vendor SDK directly in the engine** | ❌ rejected | Couples the engine to one vendor's API shape; every new provider becomes engine code. The whole point is config-not-code provider swaps. |

## What the `ChatModel` seam buys

1. **Provider swaps are configuration, never engine logic.** A new provider/model is
   `ADRA_PROVIDER` / `ADRA_MODEL` / `ADRA_MODEL_<ROLE>` — the engine code does not change.
2. **Offline-first is structural, not bolted on.** `MockChatModel` is the same
   `ChatModel` interface; the engine cannot tell the difference, so the test suite and the demo
   run with no key.
3. **The framework is replaceable.** If pydantic-ai were ever dropped, only `adra/llm.py` changes
   — the seam is the contract, and every node already speaks `ChatModel`.

## How provider selection works

- **Agentic-app archetype**: the LLM layer is pydantic-ai over a
  `provider:model` seam — the same lane used by other agentic apps in this stack, so the pattern is
  shared.
- **Provider selection by audience**: the default model is chosen by audience —
  `claude-haiku-4-5` is the cost-appropriate default for private/quality apps; switch to a
  stronger model (e.g. `claude-sonnet-4-6` or `claude-opus-4-8`) when reasoning depth matters.
  Per-role routing makes "strong for the critic, cheap for generation" a one-line config.

## What this IS and is NOT

- **IS** a justified, minimal dependency confined to one module.
- **IS NOT** an endorsement of building ADRA's orchestration *on* an agent framework — that was
  explicitly rejected (ADR-0002/0003).

## See also

- [../../adr/ADR-0003-owned-chatmodel-seam.md](../../adr/ADR-0003-owned-chatmodel-seam.md) — the
  engine ADR.
- [../../adr/ADR-0002-hand-rolled-orchestrator.md](../../adr/ADR-0002-hand-rolled-orchestrator.md)
  — why the loop is not on a framework.
- [03_usage-and-gotchas.md](./03_usage-and-gotchas.md) — how ADRA actually uses it.
