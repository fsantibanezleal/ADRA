# ADR-0009 — Two-repo split + BYOK/vault secrets model

**Status:** Accepted

## Context
ADRA should be a serious public OSS tool, yet the connected, key-holding web experience must
never expose the owner's LLM/STT/GitHub credentials to anonymous users.

## Decision
Two repositories:
- **`ADRA` (this repo) — public-destined OSS**: the engine + connectors + emulator + CLI +
  docs. Contains **no secrets, ever** (only `.env.example`). Runs offline with the emulator;
  real connectors work with the user's **own tokens supplied locally** (BYOK), read from the
  environment and never stored by ADRA.
- **`ADRA_Console` — private**: a private web app + backend that *consumes* `adra` as a
  dependency, holds keys from the operator's private secrets store, runs experiments and real connections,
  and is deployed behind access control.

Secrets are never written to the run record or logged (provenance logs only provider+model;
connectors set the auth header without logging the token). A dual-LLM split — the agent that
reads untrusted content holding no write capability — is planned for the connector phase, not
yet implemented.

## Consequences
- The open repo is safe to publish; the engine is the adoptable artifact.
- The owner's keys live only on the access-gated console, never in the repo or a public demo.
- Mirrors the common library + apps split (engine published, app private).
