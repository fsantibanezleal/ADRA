# Frameworks

ADRA's **engine core has zero required third-party dependencies** — it runs offline on the Python
standard library via the deterministic `mock` provider (`pyproject.toml`: `dependencies = []`).
Everything below is an **opt-in extra**: a real LLM provider or a real platform connector. This
section has **one subfolder per library actually used**, each documenting *what it is*, *why ADRA
chose it (citing the ADR)*, *how ADRA uses it*, and the *gotchas*.

## Read in order

| # | Framework | Extra | Role in ADRA | Decision |
|---|---|---|---|---|
| [01](./01_pydantic-ai/01_pydantic-ai.md) | **pydantic-ai** | `adra[llm]` | The LLM layer — `provider:model` seam, multi-provider/agnostic | ADR-0003 (engine) |
| [02](./02_httpx/02_httpx.md) | **httpx** | `adra[github]`, `adra[azuredevops]` | The GitHub REST v3 + Azure DevOps REST 7.1 connectors | ADR-0008 |
| [03](./03_databricks-sdk/03_databricks-sdk.md) | **databricks-sdk** | `adra[databricks]` | Read-only warehouse probes (SQL Statement Execution API) for `experiment` | ADR-0008 |
| [04](./04_azure-identity-monitor/04_azure-identity-monitor.md) | **azure-identity + azure-monitor-query** | `adra[azure]` | Read-only cloud-health probes via Log Analytics (KQL) | ADR-0008 |
| [05](./05_stdlib-emulator/05_stdlib-emulator.md) | **stdlib (`sqlite3`, `subprocess`, `argparse`)** | none | The offline emulator + every deterministic tool + the CLI | ADR-0001, ADR-0002, ADR-0008 |

## The dependency map (`pyproject.toml`)

```toml
dependencies = []                                          # core: stdlib only, runs offline
[project.optional-dependencies]
llm         = ["pydantic-ai-slim[anthropic,groq,openai,google]>=1,<2"]
github      = ["httpx>=0.27"]
azuredevops = ["httpx>=0.27"]
databricks  = ["databricks-sdk>=0.30"]
azure       = ["azure-identity>=1.17", "azure-monitor-query>=1.3"]
all         = [ ... all of the above ... ]
dev         = ["pytest>=8.0", "ruff>=0.6", "httpx>=0.27", "pydantic-ai-slim[anthropic]>=1,<2", ...]
```

The split mirrors *where the code runs*: the core (stdlib) is what executes the deterministic
floor and the offline emulator; each extra is the boundary where ADRA reaches a real LLM or a
real platform. **You only install the extra you actually use.** A missing extra never crashes the
engine — each adapter raises a clear `RuntimeError` at construction time telling you which
`pip install adra[...]` to run.

## Why these and not an agent framework

ADRA deliberately **does not** depend on LangChain / LangGraph / a heavy agent runtime (ADR-0002,
ADR-0003). The orchestration is a hand-rolled state machine; the only thing the engine needs from
a framework is a uniform way to talk to many LLM providers — which is exactly the narrow job
**pydantic-ai** does behind the tiny `ChatModel` seam. Platform access is intentionally a **thin
REST client over `httpx`** (full control, small surface) plus the official SDKs only where they
add real value (Databricks' Statement Execution, Azure's credential chain).

## What this section IS and is NOT

- **IS** a true accounting of every external library ADRA can use, and the precise extra that
  pulls it in.
- **IS NOT** a list of aspirational integrations. Each subfolder describes code that exists in
  `adra/` today (the connector adapters are implemented; ADR-0008 records that GitHub + emulator
  were the first cut, with the others following in the connector phase).

## See also

- [../guides/03_multi-provider-routing.md](../guides/03_multi-provider-routing.md) — choosing and
  routing providers.
- [../data-contract/02_connector-shapes.md](../data-contract/02_connector-shapes.md) — the
  `RepoProvider` / `DataProvider` Protocol shapes these adapters implement.
- [../security/security.md](../security/security.md) — the read-only-by-default + gated-write
  posture every connector follows.
