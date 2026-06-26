# 01 · pydantic-ai — the LLM layer

**pydantic-ai** is ADRA's house standard for talking to LLM providers (engine ADR-0003). It sits
behind a tiny ADRA-owned `ChatModel` seam (`adra/llm.py`), so the rest of the engine never
imports pydantic-ai directly — and the engine still runs **with no provider at all** via the
deterministic `mock`.

## Read in order

1. [01_what-it-is.md](./01_what-it-is.md) — what pydantic-ai is, the `provider:model` model-string
   convention, and exactly where ADRA uses it.
2. [02_why.md](./02_why.md) — why pydantic-ai over LangChain/LangGraph or a raw per-vendor SDK
   (the ADRs), and what the `ChatModel` seam buys.
3. [03_usage-and-gotchas.md](./03_usage-and-gotchas.md) — installing the extra, the providers
   matrix, per-role routing, and the gotchas (missing extra, OpenAI-compatible long tail, the
   offline mock).

## At a glance

| | |
|---|---|
| Package | `pydantic-ai-slim[anthropic,groq,openai,google]` |
| Pin | `>=1,<2` (`pyproject.toml`, the `llm` extra) |
| Install | `pip install adra[llm]` (or `adra[all]`) |
| ADRA seam | `adra/llm.py` — `ChatModel` (interface) · `PydanticAIChatModel` · `MockChatModel` · `ModelRouter` |
| Required for the engine? | **No.** The core has zero deps; pydantic-ai is opt-in for the semantic layer. |
| Decisions | engine ADR-0003 |
| Model string | `provider:model`, e.g. `anthropic:claude-haiku-4-5` |

## What ADRA IS and is NOT (re: the LLM layer)

- **IS** provider-agnostic and BYOK: pick any of `anthropic` / `openai` / `groq` / `mistral` /
  `google` natively, plus the OpenAI-compatible long tail (`xai` / `deepseek` / `openrouter` /
  `together` / local `ollama`), via configuration only — never engine code.
- **IS NOT** tied to a model version. The default is `claude-haiku-4-5`
  (cost-appropriate for private/quality apps; switch up when reasoning depth matters), but nothing
  in the engine assumes it. The whole loop runs offline with the deterministic `mock`, so a
  missing key degrades, it does not break.

## See also

- [../frameworks.md](../frameworks.md) — the frameworks index.
- [../../architecture/01_overview.md](../../architecture/01_overview.md) — where `plan` /
  `generate` / `critic` / `judge` call the model (the seam in motion).
- [../../guides/03_multi-provider-routing.md](../../guides/03_multi-provider-routing.md) — picking
  and routing providers per role.
- [../../methodologies/02_llm-as-judge.md](../../methodologies/02_llm-as-judge.md) — the role the
  model plays in scoring (and its bias mitigations).
