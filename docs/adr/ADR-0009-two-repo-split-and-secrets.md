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
- **`ADRA_Console` — private**: a Veta-style web app + backend that *consumes* `adra` as a
  dependency, holds keys from the CAOS_MANAGE vault, runs experiments and real connections,
  and is deployed behind access control.

Secrets are redacted from logs and model context; the agent that reads untrusted content
holds no write capability (dual-LLM split, connector phase).

## Consequences
- The open repo is safe to publish; the engine is the adoptable artifact.
- The owner's keys live only on the access-gated console, never in the repo or a public demo.
- Mirrors the existing `Acc_agentic_core` (library) + apps pattern.
