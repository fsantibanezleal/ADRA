# 04 · Secret handling (BYOK, two-repo split)

ADRA is **public-destined OSS** and holds **no secrets, ever** — only `.env.example`. Real
providers and connectors work with the user's **own tokens supplied locally** (BYOK), read from the
environment and never stored or logged by ADRA (ADR-0009).

Landing: [security.md](./security.md).

## BYOK — bring your own key

- Provider keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …) and connector tokens (`GITHUB_TOKEN`,
  `AZURE_DEVOPS_PAT`, `DATABRICKS_TOKEN`, …) are read from the **environment** (or `.env`, which is
  gitignored).
- They are **never persisted** by ADRA: nothing writes a key to disk, the run record
  (`provenance.py`) logs `provider` + `model` but no credential, and the connectors set the auth
  header without logging the token.
- The `.env` loader (`config._load_dotenv`) uses `os.environ.setdefault`, so explicit env vars
  always win and a committed `.env` is never relied upon (and never committed — only `.env.example`
  ships).

## English-only + AI-authorship-leak scan

Anything ADRA would write to disk (a PR body, a doc, a commit-message-shaped artifact) is scanned
by `lang_tools.scan_language` before it lands:

- **AI-session leak** (`co-authored-by`, `claude`, `anthropic`, "generated with … (claude|ai)",
  "as an ai") → **BLOCKER** (rubric `language_leak`).
- **Spanish content** (function-word + accent markers) → MAJOR.

This is both a quality rule and a leakage control: a prompt-injected or accidental attempt to
insert AI attribution into committed text is blocked at the boundary.

## The two-repo split (ADR-0009)

| Repo | What it holds | Secrets |
|---|---|---|
| **`ADRA` (this repo)** — public-destined OSS | engine + connectors + emulator + CLI + docs | **none, ever** — only `.env.example`; runs offline with the emulator; real connectors use the user's own local tokens |
| **`ADRA_Console`** — private | a private web app + backend that *consumes* `adra` | holds keys from the operator's private secret store; runs experiments + real connections behind access control |

The open repo is safe to publish; the owner's keys live only on the access-gated console, never in
the repo or a public demo. (Operational rule: secrets live only in the operator's secret manager; no
app repo commits a real `.env`.)

## Defence-in-depth on data writes

- The Databricks connector is read-only (SELECT probes); DDL/DML is rejected in-loop and should be
  backed by a SELECT-only grant at the RBAC level
  (see [../frameworks/03_databricks-sdk/01_usage-and-safety.md](../frameworks/03_databricks-sdk/01_usage-and-safety.md)).
- Secrets are never written to the run record or logged (provenance logs only provider+model;
  connectors set the auth header without logging the token). A dual-LLM split — the agent that
  reads untrusted content holding no write capability — is planned for the connector phase, not yet
  implemented (see [03_untrusted-content.md](./03_untrusted-content.md)).

## What this IS and is NOT

- **IS** a zero-secret public engine, BYOK from the environment, with disk-bound text scanned for
  leaks.
- **IS NOT** a place secrets are stored or logged. The connected, key-holding instance is the
  separate private console.

## See also

- [../adr/ADR-0009-two-repo-split-and-secrets.md](../adr/ADR-0009-two-repo-split-and-secrets.md)
- [../guides/05_local-scripts.md](../guides/05_local-scripts.md) — the `.env` workflow.
- [../frameworks/01_pydantic-ai/03_usage-and-gotchas.md](../frameworks/01_pydantic-ai/03_usage-and-gotchas.md)
  — BYOK provider keys.
