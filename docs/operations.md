# Operations

## Install & run (offline, no key)

```bash
python -m venv .venv && . .venv/Scripts/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python scripts/demo_offline.py                        # all six skills, deterministic mock
python -m pytest tests/ -q                            # 11 tests, no key
```

## Enable a real provider (vendor-agnostic)

```bash
pip install -e ".[anthropic]"          # native anthropic SDK; the ChatModel seam is provider-agnostic
export ANTHROPIC_API_KEY=...           # or put it in .env
export ADRA_PROVIDER=anthropic
```

## Configuration (`adra/config.py`, env-driven)

| Env var | Default | Meaning |
|---|---|---|
| `ADRA_PROVIDER` | auto (`anthropic` if key else `mock`) | LLM provider |
| `ADRA_MODEL` | latest configured model | model id |
| `ADRA_MAX_ROUNDS` | 3 | revise iterations before escalation |
| `ADRA_ALLOW_EXTERNAL` | 0 | `1` lets tools run git / databricks / the CI command |
| `ADRA_REPO_PATH` | – | repo under review (for the deterministic tools) |
| `ADRA_CLIENT_DIR` | bundled Northwind | the active client's governance suite |

Default is **dry-run / read-only**. `--external` (or `ADRA_ALLOW_EXTERNAL=1`) is
required for a tool to actually touch git / Databricks / CI.

## CLIs

| Command | Purpose |
|---|---|
| `adra review <diff> [--ci-command ...]` | Review a unified diff |
| `adra pr-eval --source <branch> [--repo ...]` | Evaluate a branch/PR |
| `adra experiment <spec.json>` | Run a validation experiment from a JSON spec |
| `adra improve "<context>"` | Minimum-functional improvement proposal |
| `adra document [--type pr] [--title ...]` | Render a doc from a run record |
| `adra decide "<problem>" <route> <route> ...` | Route analysis (human-owned) |
| `python scripts/demo_offline.py` | End-to-end offline demo (all six skills) |

Programmatic use:

```python
from adra import Orchestrator, load_settings
state, record = Orchestrator(load_settings()).run("pr_eval", {"source_branch": "task/NDP-1/x"})
print(record.summary()); print(state.artifacts["pr_body.md"])
```

## Extend

- **New criterion** → add a `RubricItem` to `adra/rubric.py`. Semantic items are
  auto-injected into the critic prompt; for a `deterministic` item, wire its check in
  `critic.deterministic_attacks` (or a tool).
- **New capability** → subclass `adra.skills.base.Skill`, add `prompts/<skill>.md`,
  register it in `adra/skills/__init__.py`, add a `Node` in `adra/nodes.py`.
- **New tool** → a function returning a `ToolResult`; call it from a skill's
  `ground()`. Accept a `fixture` so it replays offline.
- **Retarget a client** → set `ADRA_CLIENT_DIR` to a client's governance suite (or
  `Settings.client_dir`) and update the rubric incident references. The code does not change.

## Guarantees / limits

- Runs and tests pass **offline**; the deterministic floor carries the verdict.
- **No real PR** is created/modified by default; PR creation is a separate, explicit,
  confirmed action.
- It is a **reference / standardization scaffold**, not a production service.
