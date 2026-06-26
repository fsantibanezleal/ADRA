# ADR-0008 — Connector `Protocol` + offline emulator as a real backend

**Status:** Accepted (GitHub connector + emulator implemented 2026-06-26; ADO/Databricks/Azure adapters next)

## Context
ADRA must reach real platforms (GitHub, Azure DevOps, Databricks, Azure) *and* run a complete
flow offline for demos, tests, and air-gapped reproducibility — without the engine knowing
which it is talking to.

## Decision
All platform access goes through one connector `Protocol` family (`RepoProvider`,
`DataProvider`, `CIProvider`, `WikiProvider`, `BoardProvider`) + a factory wired from a
client binding. Adapters: GitHub via a **thin REST client over `httpx`** (read PRs + diff,
issues, comments; writes gated) — githubkit/GraphQL optional later for line-level review
composition; Azure DevOps via **raw REST 7.1 over `httpx`**; Databricks via
**`databricks-sdk` + CLI subprocess** (bundles); Azure via **`azure-identity` +
`azure-monitor-query` + `azure-mgmt-resourcehealth` + `azure-storage-blob`**. A self-contained
**emulator** (synthetic git repos + PRs + wiki + boards + CI + SQLite warehouse) implements
the same Protocol so the full flow runs offline. Read-only by default; every write is gated.

## Consequences
- The same skills run against a real platform or a synthetic one (config flip).
- The public demo and the test fixtures use the emulator — no external dependency, no toy.
- A `Protocol`-conformant adapter is the only thing a new platform needs.
- Implemented in v0.03.000: the connector Protocol + factory, the **real GitHub** adapter
  (`adra github-review owner/repo PR#`, read-only by default), and the **emulator**
  (4 multi-industry synthetic PRs + a seeded SQLite warehouse). ADO/Databricks/Azure next.
