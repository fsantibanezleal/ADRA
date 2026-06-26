# pydantic-ai — usage & gotchas

## Install

```bash
pip install adra[llm]      # pydantic-ai-slim[anthropic,groq,openai,google] >=1,<2
# or: pip install adra[all]
```

The core engine needs nothing; this extra is only for the semantic layer. With no key set, ADRA
auto-detects no provider and uses the offline `mock` (see [config](../../guides/01_install-and-run.md)).

## Select a provider

```bash
export ADRA_PROVIDER=anthropic
export ANTHROPIC_API_KEY=...           # BYOK; never stored by ADRA, never logged
# optional: pin a model (defaults per provider otherwise)
export ADRA_MODEL=claude-haiku-4-5
```

If `ADRA_PROVIDER` is unset, ADRA auto-detects the first provider whose key is present
(`anthropic → openai → groq → xai → mistral → deepseek → openrouter → together`), else `mock`
(`adra/config.py`, `_autodetect_provider`).

## The providers matrix

| ADRA provider | How pydantic-ai reaches it | Default model (`adra/config.py`) | Key env |
|---|---|---|---|
| `anthropic` | native `anthropic:<model>` | `claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| `openai` | native `openai:<model>` | `gpt-4o` | `OPENAI_API_KEY` |
| `groq` | native `groq:<model>` | `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| `mistral` | native `mistral:<model>` | `mistral-large-latest` | `MISTRAL_API_KEY` |
| `google` | native `google-gla:<model>` | (per provider) | (Google creds) |
| `xai` | OpenAI-compatible base | `grok-4` | `XAI_API_KEY` |
| `deepseek` | OpenAI-compatible base | `deepseek-chat` | `DEEPSEEK_API_KEY` |
| `openrouter` | OpenAI-compatible base | `openai/gpt-4o` | `OPENROUTER_API_KEY` |
| `together` | OpenAI-compatible base | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | `TOGETHER_API_KEY` |
| `ollama` (local) | OpenAI-compatible base `http://localhost:11434/v1` | `llama3.1` | none |
| any other | `ADRA_BASE_URL` + `ADRA_API_KEY` | — | — |
| `mock` | offline, no network | `claude-haiku-4-5` (label only) | none |

The native vs OpenAI-compatible split is in `PydanticAIChatModel._model`: providers in
`_PYDANTIC_AI_PREFIX` use the native model string; everything else builds an `OpenAIChatModel`
with an `OpenAIProvider(base_url=..., api_key=...)`.

## Per-role routing (one run, multiple providers)

Route a strong model to the critic/judge and a cheaper/faster one to generation:

```bash
export ADRA_MODEL_CRITIC=anthropic:claude-opus-4-8
export ADRA_MODEL_JUDGE=anthropic:claude-opus-4-8
export ADRA_MODEL_GENERATE=groq:llama-3.3-70b-versatile
```

The value is `provider:model` or just `model` (provider inherits the default). The `ModelRouter`
caches a `ChatModel` per `(provider, model)` and resolves it per role
(`Settings.role` / `model_id`). See
[../../guides/03_multi-provider-routing.md](../../guides/03_multi-provider-routing.md).

## Gotchas

- **Missing extra → clear error, not a crash.** `PydanticAIChatModel.__init__` catches the
  `ImportError` and raises `RuntimeError("real providers require pip install adra[llm]
  (pydantic-ai).")`. The engine itself still imports and runs offline.
- **Unknown provider → explicit list.** `_model` raises `RuntimeError(f"unknown provider {provider!r};
  known: ...")` enumerating `mock`, the native prefixes, and `PROVIDERS`.
- **No per-call system_prompt API is assumed.** `generate` passes `f"{system}\n\n---\n\n{user}"`
  to `Agent.run_sync`, so the adapter stays framework-version-agnostic (it does not depend on a
  specific pydantic-ai `system_prompt` signature).
- **Model ids are bare.** Use `claude-haiku-4-5`, not a date-suffixed variant.
- **Temperature / params are pydantic-ai's concern.** ADRA's `Settings.temperature`
  (default `0.0`) and `max_tokens` are passed through the factory; the seam does not pin any
  model-version-specific parameter.
- **Keys are BYOK and never persisted.** ADRA reads the key from the environment (or `ADRA_API_KEY`
  for the OpenAI-compatible base) and never writes it anywhere — see
  [../../security/security.md](../../security/security.md).

## See also

- [01_what-it-is.md](./01_what-it-is.md) · [02_why.md](./02_why.md)
- [../../guides/01_install-and-run.md](../../guides/01_install-and-run.md) — full config table.
- [../../security/04_secret-handling.md](../../security/04_secret-handling.md) — BYOK + redaction.
