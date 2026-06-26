# 05 · Local scripts & the `.env` workflow

`scripts/` holds thin, offline-first wrappers around the engine: one-command setup/test/demo, and
per-skill runners. Each runner inserts the repo root on `sys.path`, builds `Settings`, runs the
orchestrator, and prints the artifacts — handy for driving ADRA without the installed `adra`
console script.

Read order: 04 → **05**. Landing: [guides.md](./guides.md).

## The scripts

| Script | What it does |
|---|---|
| `scripts/setup.sh` / `setup.ps1` | create `.venv`, `pip install -e ".[dev]"` — offline-ready, no key |
| `scripts/test.sh` / `test.ps1` | run the offline test suite |
| `scripts/demo.sh` / `demo.ps1` | run the end-to-end offline demo |
| `scripts/demo_offline.py` | the demo itself — all six skills with bundled Northwind fixtures; writes records under `runs/` |
| `scripts/run_review.py` | `python scripts/run_review.py change.diff [--ci "<cmd>"] [--repo <path>] [--external]` |
| `scripts/run_pr_eval.py` | run `pr_eval` over a branch/PR |
| `scripts/run_experiment.py` | `python scripts/run_experiment.py spec.json [--external]` |
| `scripts/run_decide.py` | run a `decide` route analysis |

> Bash (`.sh`) and PowerShell (`.ps1`) variants are provided so the scripts run on both POSIX
> shells and Windows PowerShell. They do the same thing; pick the one for your shell.

### Example: a one-line review

```bash
python scripts/run_review.py my.diff \
  --ci 'python -m coverage run -m unittest discover -s . -p "test*.py"' --external
# prints: run <id> | skill=code_review | decision=... | ...
#         --- review.md --- (deterministic + semantic findings)
```

Each runner uses `load_settings(runs_dir=<repo>/runs, allow_external_calls=args.external)` and
selects a real provider when `ANTHROPIC_API_KEY` (or another key) is present, else the offline
mock.

## The `.env` workflow

- Copy `.env.example` → `.env` (gitignored) and fill **only** what you use. The engine runs with
  **no keys**.
- `adra/config.py` loads `.env` if present via a minimal built-in loader (no `python-dotenv`);
  **explicit environment variables always win** (`os.environ.setdefault`).
- `.env.example` documents every knob: provider/model + per-role routing, BYOK keys per provider,
  `ADRA_MAX_ROUNDS`, `ADRA_CLIENT_DIR`, `ADRA_ALLOW_EXTERNAL`, `ADRA_REPO_PATH`, and the connector
  tokens (`GITHUB_TOKEN`, `AZURE_DEVOPS_PAT`, `DATABRICKS_*`).
- **Never commit a real `.env`.** Secrets live only in your own secret store / environment; the repo
  ships `.env.example` only. See [../security/04_secret-handling.md](../security/04_secret-handling.md).

## Outputs

Every run writes an immutable record to `runs/<run_id>.json` (the provenance log). `record.summary()`
prints a one-line view; the artifacts (e.g. `review.md`, `pr_body.md`, `route_analysis.md`) are in
`state.artifacts`. See [../data-contract/03_run-record.md](../data-contract/03_run-record.md).

## What this IS and is NOT

- **IS** convenience wrappers + a clean `.env` workflow for local, offline-first runs.
- **IS NOT** a deployment mechanism. Production/connected use is the separate private console
  (ADR-0009).

## See also

- [01_install-and-run.md](./01_install-and-run.md) · [02_the-cli.md](./02_the-cli.md)
- [../data-contract/01_intake-contracts.md](../data-contract/01_intake-contracts.md) — the intake
  shapes these runners build.
