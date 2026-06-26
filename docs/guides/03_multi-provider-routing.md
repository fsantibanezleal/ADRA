# 03 · Connecting a provider & per-role routing

The deterministic loop runs offline with no key. Connecting a provider adds the **semantic layer**
on top (semantic findings, richer prose) — it never overturns a deterministic blocker. Providers
are pydantic-ai behind ADRA's `ChatModel` seam (see
[../frameworks/01_pydantic-ai/01_pydantic-ai.md](../frameworks/01_pydantic-ai/01_pydantic-ai.md)).

Read order: 02 → **03** → 04. Landing: [guides.md](./guides.md).

## Connect a provider (BYOK)

```bash
pip install -e ".[anthropic]"        # or adra[llm] / adra[all]
export ADRA_PROVIDER=anthropic
export ANTHROPIC_API_KEY=...         # BYOK — read from the env, never stored by ADRA, never logged
# optional model pin (defaults per provider otherwise):
export ADRA_MODEL=claude-haiku-4-5
```

If `ADRA_PROVIDER` is unset, ADRA auto-detects the first provider whose key is present, else the
offline `mock`.

## The providers

Native pydantic-ai: `anthropic`, `openai`, `groq`, `mistral`, `google`. The OpenAI-compatible long
tail via a base URL: `xai`, `deepseek`, `openrouter`, `together`, local `ollama`, or any custom
endpoint with `ADRA_BASE_URL` + `ADRA_API_KEY`. Full matrix + default models:
[../frameworks/01_pydantic-ai/03_usage-and-gotchas.md](../frameworks/01_pydantic-ai/03_usage-and-gotchas.md).

Anthropic model ids are bare: `claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-opus-4-8`.

## Per-role routing (one run, multiple providers)

ADRA resolves a model **per flow role** — `plan`, `generate`, `critic`, `judge` — so a single run
can orchestrate across providers. The canonical pattern is a strong model for the
critic/judge and a cheaper/faster one for generation:

```bash
export ADRA_MODEL_CRITIC=anthropic:claude-opus-4-8
export ADRA_MODEL_JUDGE=anthropic:claude-opus-4-8
export ADRA_MODEL_GENERATE=groq:llama-3.3-70b-versatile
```

Each value is `provider:model` or just `model` (provider inherits the default). The `ModelRouter`
(`adra/llm.py`) caches one `ChatModel` per `(provider, model)`; `Settings.role(role)` resolves
`(provider, model)` and `Settings.model_id(role)` logs `provider:model` into the run record.

Why this pairs well with the methods: the **critic** and **judge** are where rigor matters most
(blocking decisions, bias-mitigated scoring), so spend the strong model there; **generation** is
advisory (the critic enforces), so a cheaper model is fine.

## Local & free (Ollama / LM Studio / vLLM)

```bash
export ADRA_PROVIDER=ollama          # default base http://localhost:11434/v1, model llama3.1
```

No key needed — runs against your local server, fully offline-capable.

## What this IS and is NOT

- **IS** vendor-agnostic, BYOK, with per-role routing as configuration only.
- **IS NOT** a place secrets live. Keys are read from the environment and never persisted by ADRA;
  the connected, key-holding instance is the separate private console (ADR-0009). See
  [../security/04_secret-handling.md](../security/04_secret-handling.md).

## See also

- [../frameworks/01_pydantic-ai/01_pydantic-ai.md](../frameworks/01_pydantic-ai/01_pydantic-ai.md)
- [../methodologies/02_llm-as-judge.md](../methodologies/02_llm-as-judge.md) — why route a strong
  model to the judge.
- [04_retarget-a-client.md](./04_retarget-a-client.md) — ground on your standards.
