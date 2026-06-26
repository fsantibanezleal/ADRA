# ADR-0003 — ADRA-owned `ChatModel` seam + native-SDK providers

**Status:** Accepted

## Context
The reference implementation depended on `langchain_core` for its chat-model type. For a
serious, low-dependency public tool, a heavy framework base class is unnecessary: ADRA only
needs "one system+user turn returns text", plus a deterministic offline mock.

## Decision
Define a tiny ADRA-owned seam, `ChatModel.generate(system, user) -> str` (`adra/llm.py`).
Ship two adapters: a deterministic `MockChatModel` (offline, keyless) and an
`AnthropicChatModel` using the **native `anthropic` SDK** (lazy import). New providers
(`openai` / `groq` / `xai`) are one small subclass each. LangChain/LangGraph are not
dependencies; LiteLLM may sit behind the seam later but is never load-bearing.

## Consequences
- The engine core has **no required third-party dependencies** (pure stdlib + offline mock).
- Provider-native features and deterministic knobs are not normalized away by a gateway.
- The offline mock composes trivially with the rest of the engine and the tests.
