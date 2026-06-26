# Guides

How to **use the ADRA engine on your own repos and data** — install, the CLI, connecting a
provider and routing per role, pointing the engine at another client's governance, and the local
scripts.

## Read in order

1. [01_install-and-run.md](./01_install-and-run.md) — `pip install adra`, the offline quickstart,
   the full env-var config table, programmatic use.
2. [02_the-cli.md](./02_the-cli.md) — every command: `review` · `pr-eval` · `experiment` ·
   `improve` · `document` · `decide` · `github-review` · `emu`, with `--external`.
3. [03_multi-provider-routing.md](./03_multi-provider-routing.md) — connect a provider, BYOK,
   per-role routing, the OpenAI-compatible long tail, local Ollama.
4. [04_retarget-a-client.md](./04_retarget-a-client.md) — `ADRA_CLIENT_DIR`: ground the engine on
   any client's governance suite (no code change).
5. [05_local-scripts.md](./05_local-scripts.md) — `scripts/` (demo, setup, test, per-skill runners)
   and the `.env` workflow.

## The 30-second version

```bash
python -m venv .venv && . .venv/Scripts/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q                                            # offline, no key
python scripts/demo_offline.py                       # all six skills end-to-end
adra emu list && adra emu review 102                 # the synthetic stale-base PR → blocked + escalated
```

Add a provider later for the semantic layer:

```bash
pip install -e ".[anthropic]"        # pydantic-ai (anthropic extra)
export ADRA_PROVIDER=anthropic ANTHROPIC_API_KEY=...
adra github-review owner/repo 42 --skill pr_eval      # read-only by default
```

## Using ADRA on OTHER data — the three levers

| You want to… | Lever | Page |
|---|---|---|
| Review a diff/PR from any repo | `adra review <diff>` / `adra github-review owner/repo PR#` | [02](./02_the-cli.md) |
| Run an experiment over your warehouse | `adra experiment <spec.json>` (+ `--external` for live SQL) | [02](./02_the-cli.md) · [03_experiment](../use-cases/03_experiment.md) |
| Ground on **your** standards | `ADRA_CLIENT_DIR=/path/to/your/standards` | [04](./04_retarget-a-client.md) |
| Use **your** provider/model | `ADRA_PROVIDER` / `ADRA_MODEL` / `ADRA_MODEL_<ROLE>` (BYOK) | [03](./03_multi-provider-routing.md) |

## Safety default

Everything is **dry-run / read-only by default.** Deterministic tools and connectors only call out
(git / CI / Databricks / GitHub writes) with `--external` (or `ADRA_ALLOW_EXTERNAL=1`), and any
real write also needs explicit confirmation. See [../security/security.md](../security/security.md).

## See also

- [../use-cases/use-cases.md](../use-cases/use-cases.md) — what each skill does, in depth.
- [../frameworks/frameworks.md](../frameworks/frameworks.md) — the extras the connectors/providers
  need.
- [../data-contract/data-contract.md](../data-contract/data-contract.md) — the exact intake shapes
  the CLI builds.
