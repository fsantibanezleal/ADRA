# 01 · Install & run

ADRA is `pip install adra` (Python ≥ 3.11, Apache-2.0). The **engine core has no required
third-party dependencies** — it runs offline on the standard library via the deterministic `mock`
provider. Real providers and platform connectors are opt-in extras.

Read order: **01** → 02. Landing: [guides.md](./guides.md).

## Install (offline, no key)

```bash
python -m venv .venv && . .venv/Scripts/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                               # from a clone; or: pip install adra
pytest -q                                             # offline test suite, no API key
python scripts/demo_offline.py                        # all six skills, deterministic mock
```

Expected from the demo: the stale-base PR is **blocked + escalated**; the language/leak review is
**blocked**; the clean experiment / improve / document / decide runs are **accepted**.

> Use a local `.venv` — never a global interpreter (project convention; isolated environments).

## Extras (only what you use)

| Extra | Pulls | Enables |
|---|---|---|
| `adra[llm]` | `pydantic-ai-slim[anthropic,groq,openai,google]` | real LLM providers (the semantic layer) |
| `adra[github]` | `httpx` | the real GitHub connector |
| `adra[azuredevops]` | `httpx` | the Azure DevOps connector |
| `adra[databricks]` | `databricks-sdk` | read-only warehouse probes |
| `adra[azure]` | `azure-identity`, `azure-monitor-query` | read-only Log Analytics (KQL) probes |
| `adra[all]` | all of the above | everything |
| `adra[dev]` | pytest, ruff, + the connector/LLM deps | development |

## Configuration (env-driven, `adra/config.py`)

A `.env` is loaded if present (a minimal built-in loader; explicit env vars always win).

| Env var | Default | Meaning |
|---|---|---|
| `ADRA_PROVIDER` | auto (first present key, else `mock`) | LLM provider: `mock`/`anthropic`/`openai`/`groq`/`xai`/`mistral`/`deepseek`/`openrouter`/`together`/`ollama` |
| `ADRA_MODEL` | per-provider default | model id (e.g. `claude-haiku-4-5`, `gpt-4o`) |
| `ADRA_MODEL_{PLAN,GENERATE,CRITIC,JUDGE}` | – | per-role override, `provider:model` or `model` |
| `ADRA_TEMPERATURE` | `0.0` | sampling temperature |
| `ADRA_MAX_TOKENS` | `4096` | max tokens |
| `ADRA_MAX_ROUNDS` | `3` | revise iterations before escalation |
| `ADRA_ALLOW_EXTERNAL` | `0` | `1` lets tools/connectors call git / CI / Databricks / write |
| `ADRA_REPO_PATH` | – | local repo for the deterministic git/CI tools |
| `ADRA_CLIENT_DIR` | bundled Northwind | active client governance suite |
| `ADRA_BASE_URL` / `ADRA_API_KEY` | – | any OpenAI-compatible endpoint |

Provider auto-detect order when `ADRA_PROVIDER` is unset:
`anthropic → openai → groq → xai → mistral → deepseek → openrouter → together`, else `mock`.

## Programmatic use

```python
from adra import Orchestrator, load_settings

state, record = Orchestrator(load_settings()).run(
    "pr_eval", {"source_branch": "task/NDP-1/x", "target_branch": "main"})
print(record.summary())          # run id | skill | decision | critic_passes | last_clean
print(state.artifacts["pr_body.md"])
print(state.decision)            # "accepted" | "escalate"
```

`Orchestrator.run(skill, intake)` returns `(RunState, RunRecord)`; the record is also written to
`runs/<run_id>.json` (see [../data-contract/03_run-record.md](../data-contract/03_run-record.md)).

## What this IS and is NOT

- **IS** a single `pip install` that runs fully offline; extras are additive.
- **IS NOT** a service you stand up. ADRA is a reference/standardization engine you run anywhere
  with your own tokens (the connected, key-holding web experience is the separate private console,
  ADR-0009).

## See also

- [02_the-cli.md](./02_the-cli.md) · [03_multi-provider-routing.md](./03_multi-provider-routing.md)
- [05_local-scripts.md](./05_local-scripts.md) — the `scripts/` and `.env` workflow.
