# Changelog

All notable changes to ADRA are documented here. Versions use the `X.XX.XXX` display
format (PEP 440 package version in `pyproject.toml` is the normalized equivalent).
Stays `0.x` while connectors are partly untested-live.

## [0.03.000] — 2026-06-26

### Added
- **Connector layer** (`adra/connectors/`): one Protocol family (`RepoProvider` /
  `DataProvider`) + a factory wired from a client binding. Read-only by default; writes gated.
- **Real GitHub connector** (REST over httpx): read PRs + their unified diff, list PRs, create
  issues, comment on PRs (writes gated). CLI: `adra github-review owner/repo <pr#>
  [--skill code_review|pr_eval] [--post --external]`.
- **Offline emulator** (`adra/connectors/emulator.py`): 4 multi-industry synthetic PRs
  (fintech / ecommerce / healthtech / logistics, with planted flaws) + a seeded SQLite
  warehouse. CLI: `adra emu list|review`.
- `github` extra (httpx); connector tests (now 14 total).

## [0.02.000] — 2026-06-26

### Added
- **Real multi-provider LLM layer.** A provider factory behind the `ChatModel` seam:
  Anthropic (native SDK) + OpenAI-compatible (`openai`, `groq`, `xai`, `mistral`, `deepseek`,
  `openrouter`, `together`) + **local/free** (`ollama` / LM Studio / vLLM), plus any other
  OpenAI-compatible endpoint via `ADRA_BASE_URL`/`ADRA_API_KEY`. Provider auto-detects from
  whichever API key is present.
- **Per-role model routing** (`ModelRouter`): `plan` / `generate` / `critic` / `judge` can
  each run a different model/provider (`ADRA_MODEL_<ROLE>`), so one run orchestrates across
  providers; each step records which model ran it (provenance).

### Changed
- `mock` is now explicitly the **offline-only** lane (zero keys; the deterministic floor
  carries the verdict) — not the semantic layer. ADR-0003 rewritten to reflect the
  multi-provider factory (not a reduction).

## [0.01.000] — 2026-06-26

Initial engine cut — the client-agnostic, deterministic-first adversarial-validation core.

### Added
- **Engine (`adra/`)**: the adversarial loop `plan → ground → generate → CRITIC → revise →
  escalate`, six skills (`code_review`, `pr_eval`, `experiment`, `improve`, `document`,
  `decide`), the shared typed **rubric**, the blocking two-pass **critic** (deterministic
  hard-floor + LLM semantic), the **LLM-as-judge** with swap-and-average + reference
  anchoring, the immutable **provenance** run record, and deterministic **tools**
  (`git`, `ci`, `bundle`, `lang`, `discovery`, `sql`).
- **Provider seam (`adra/llm.py`)**: a tiny ADRA-owned `ChatModel` interface with a
  deterministic offline `MockChatModel` and a native-SDK `AnthropicChatModel` — **no
  agent framework**; the orchestrator is a hand-rolled deterministic state machine.
- **Client-agnostic grounding**: `ADRA_CLIENT_DIR` / `Settings.client_dir` select the
  active client's governance suite; bundled fictional client **Northwind Data Platform**
  (`adra/clients/synthetic/northwind/`: conventions, CI standards, glossary, 8 ADRs, 5
  anonymized incident cases).
- **CLI (`adra`)**: `review`, `pr-eval`, `experiment`, `improve`, `document`, `decide`.
- **Docs (`docs/`)** + **references (`refs/`)** (annotated bibliography + papers) +
  **engine ADRs (`docs/adr/`)**.
- Runs fully **offline with no API key**; **11/11 tests pass**; offline demo green.

### Notes
- Real platform connectors (GitHub via `githubkit`, Azure DevOps REST, Databricks SDK,
  Azure) and the offline **emulator** land in the next phase (see `wip/adra/plan.md`).
