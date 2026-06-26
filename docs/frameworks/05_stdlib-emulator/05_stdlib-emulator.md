# 05 · The Python standard library (the offline engine + emulator)

ADRA's most important "framework" is the one with **zero install cost**: the Python standard
library. The engine core declares **no third-party dependencies** (`pyproject.toml`:
`dependencies = []`). Everything that runs offline — the deterministic tools, the orchestrator,
the provenance log, the CLI, and the self-contained emulator — is built on stdlib alone. This is
what makes "runs offline with no API key" a true claim (ADR-0001, ADR-0002, ADR-0008).

## At a glance

| | |
|---|---|
| Packages | none (CPython standard library) |
| Install | nothing — `pip install adra` with **no extras** runs the full offline path |
| Key stdlib modules | `sqlite3` (emulator warehouse) · `subprocess` (git / CI / bundle / databricks CLI) · `argparse` (CLI) · `dataclasses` / `enum` / `json` (domain model + provenance) · `re` / `fnmatch` (lang + discovery checks) · `base64` (ADO PAT auth) |
| Decision | ADR-0001 (deterministic-first), ADR-0002 (framework-free orchestrator), ADR-0008 (emulator) |

## Read in order

1. [01_the-emulator.md](./01_the-emulator.md) — the self-contained platform: synthetic
   multi-industry PRs (with planted, deterministically-catchable flaws) + a seeded SQLite
   warehouse, both implementing the connector Protocol so the full flow runs offline.

## What stdlib carries

| Concern | stdlib used | Where |
|---|---|---|
| Domain model + provenance | `dataclasses`, `enum`, `json` | `state.py`, `provenance.py` |
| Deterministic tools | `subprocess` (git/CI/bundle/databricks CLI), `re`, `fnmatch` | `tools/*` |
| Offline warehouse | `sqlite3` (`:memory:`) | `connectors/emulator.py` |
| CLI | `argparse` | `cli/__main__.py` |
| Config + `.env` | `os`, `pathlib` (a minimal `.env` loader, no `python-dotenv`) | `config.py` |
| Offline LLM mock | `json`, `re` (node-keyed canned answers) | `llm.py` |

The deterministic tools (`git`, the exact CI command, `databricks bundle validate`, the SQL
warehouse, the language scan, test discovery) are the **verdict-carrying floor** — and they all
run on stdlib + locally-installed CLIs. A missing CLI or disabled external calls returns a
`ToolResult(ran=False, reason=...)`, so the package always runs.

## What this IS and is NOT

- **IS** a genuinely dependency-free core: the adversarial loop, the deterministic floor, and the
  emulator all run with `pip install adra` and no extras.
- **IS NOT** a toy. The emulator's synthetic PRs carry real failure modes the deterministic floor
  catches, and the warehouse is a real (seeded) SQLite DB queried with real SQL.

## See also

- [01_the-emulator.md](./01_the-emulator.md)
- [../../architecture/05_why-deterministic-first.md](../../architecture/05_why-deterministic-first.md)
  — why the floor (stdlib) carries the verdict.
- [../../data-contract/02_connector-shapes.md](../../data-contract/02_connector-shapes.md) — the
  Protocol the emulator implements.
