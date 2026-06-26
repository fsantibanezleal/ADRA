# ADR-0003 — Multi-provider `ChatModel` factory + per-role routing (no LangChain)

**Status:** Accepted

## Context
The reference implementation depended on `langchain_core` for its chat-model type and wired
a single provider. ADRA must (a) work with **any** provider the user has — not one — (b) be a
low-dependency, auditable public tool, and (c) let the flow use **different models for
different roles** (a strong model to critique/judge, a cheaper/faster one to generate).

## Decision
Define a tiny ADRA-owned seam, `ChatModel.generate(system, user) -> str` (`adra/llm.py`),
and a **real multi-provider factory** behind it:
- **`anthropic`** — native `anthropic` SDK.
- **OpenAI-compatible** (`openai`, `groq`, `xai`, `mistral`, `deepseek`, `openrouter`,
  `together`, and **local** `ollama` / LM Studio / vLLM) via the `openai` SDK with a
  per-provider base URL (registry in `config.PROVIDERS`); any other compatible endpoint via
  `ADRA_BASE_URL` + `ADRA_API_KEY`.
- **`mock`** — a deterministic **offline** adapter so the engine + tests run with **zero
  keys**. It is not a product capability and never fakes results; the deterministic floor
  (tools + critic) carries the verdict.

A `ModelRouter` resolves a model **per flow role** (`plan` / `generate` / `critic` /
`judge`) from `ADRA_MODEL_<ROLE>` overrides, so one run orchestrates across providers; each
step records which model ran it (provenance). The provider auto-detects from whichever API
key is present. LangChain/LangGraph are **not** dependencies; LiteLLM may sit behind the
seam later but is never load-bearing.

## Consequences
- Anyone can use ADRA with their own provider — paid or **local/free** — or with no LLM at
  all (offline). It is never tied to one vendor.
- The flow can mix providers per role; the run record shows which model did what.
- The engine core keeps **zero required third-party dependencies** (a provider is an extra).
- The `ChatModel` seam is the factory's interface, not a reduction of capability.
