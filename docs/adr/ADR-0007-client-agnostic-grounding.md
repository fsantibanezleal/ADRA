# ADR-0007 — Client-agnostic grounding; no client/domain in the engine

**Status:** Accepted

## Context
ADRA must serve any client without code changes, and (as a public OSS tool) must contain no
real client and no single-industry framing.

## Decision
A *client* is a governance suite (conventions, ADRs, CI standards, glossary, incident cases)
the engine grounds on. The active suite is selected by `ADRA_CLIENT_DIR` (or
`Settings.client_dir`) and defaults to a bundled **fictional, industry-neutral** client
(Northwind Data Platform). The rubric references the suite by id; prompts cite it; the engine
code does not change per client. No real client, mining, or domain-specific framing ships in
the engine.

## Consequences
- Retargeting a client is configuration + a governance folder, not a fork.
- The engine is safe to open-source: the only bundled client is fictional and neutral.
- Multi-industry synthetic clients can be added under `adra/clients/synthetic/`.
