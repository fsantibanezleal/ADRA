# pydantic-ai — what it is, and where ADRA uses it

**pydantic-ai** is a Python agent/LLM framework from the Pydantic team. ADRA uses only its thin
**model layer**: a single `Agent` object addresses any provider through a uniform
`provider:model` string and returns text. ADRA does not use pydantic-ai's higher-level agent
graph, tools, or dependency injection — the orchestration is ADRA's own hand-rolled state machine
(see [architecture](../../architecture/architecture.md)).

## The `provider:model` convention

A model is identified by a string of the form `<provider>:<model-id>`. ADRA maps its provider
names to pydantic-ai's native prefixes in `adra/llm.py`:

```python
_PYDANTIC_AI_PREFIX = {
    "anthropic": "anthropic",
    "openai":    "openai",
    "groq":      "groq",
    "mistral":   "mistral",
    "google":    "google-gla",
}
```

So ADRA's `anthropic` + `claude-haiku-4-5` becomes the pydantic-ai model string
`anthropic:claude-haiku-4-5`. Anthropic model ids are bare (no date suffix):
`anthropic:claude-haiku-4-5`, `anthropic:claude-opus-4-8`, `anthropic:claude-sonnet-4-6`.

Any provider **not** in that native map is reached as an **OpenAI-compatible** endpoint instead
(`xai` / `deepseek` / `openrouter` / `together` / local `ollama`, or any custom base URL) — see
[03_usage-and-gotchas.md](./03_usage-and-gotchas.md).

## Where ADRA uses it — the `ChatModel` seam

The engine never imports pydantic-ai outside `adra/llm.py`. That module defines a minimal seam:

```python
class ChatModel:
    def generate(self, system: str, user: str) -> str: ...

class PydanticAIChatModel(ChatModel):     # real provider, via pydantic-ai Agent
class MockChatModel(ChatModel):           # deterministic offline fallback (no key)
```

`PydanticAIChatModel.__init__` builds `Agent(self._model(provider, model), retries=1)` lazily
(the `from pydantic_ai import Agent` import is inside `__init__`, so importing ADRA never requires
the extra). `generate` calls `self._agent.run_sync(...)` and returns the output text.

Every node that calls the model goes through this seam: `plan`, `generate`, `revise` (in each
`Skill`), `critic` (`adra/critic.py`), and `judge` (`adra/judge.py`). The orchestrator resolves
*which* model each role gets via a `ModelRouter` (see
[../../guides/03_multi-provider-routing.md](../../guides/03_multi-provider-routing.md)), so one run
can use a strong model for the critic/judge and a cheaper one for generation.

## The node tag (why the offline mock is deterministic)

`invoke_text` appends a hidden tag to the system prompt — `[[ADRA-NODE:<node>]]` — before calling
`ChatModel.generate`. The real provider ignores it; the `MockChatModel` reads it to return a
node-keyed canned answer (`adra/llm.py`, `_CANNED`). This is what lets the *same* code path run
identically with a real provider or fully offline.

## What this page IS and is NOT

- **IS** an accurate description of the narrow slice of pydantic-ai ADRA depends on.
- **IS NOT** a claim that ADRA uses pydantic-ai's agent framework. It uses the model layer only;
  the loop, the rubric, the critic, and the judge are ADRA's.

## See also

- [02_why.md](./02_why.md) — the rationale and the ADRs.
- [03_usage-and-gotchas.md](./03_usage-and-gotchas.md) — install, providers, routing, gotchas.
