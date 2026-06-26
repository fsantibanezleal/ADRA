# Changelog

All notable changes to ADRA are documented here. Versions use the `X.XX.XXX` display
format (PEP 440 package version in `pyproject.toml` is the normalized equivalent).
Stays `0.x` while connectors are partly untested-live.

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
