# 04 · Retarget a client (`ADRA_CLIENT_DIR`)

A **client** in ADRA is a *governance suite* — the conventions, ADRs, CI standards, glossary, and
incident cases the engine grounds on. ADRA ships one bundled, **fictional, industry-neutral**
client (Northwind Data Platform) and lets you point it at any other with one environment variable.
No engine code changes per client (ADR-0007).

Read order: 03 → **04** → 05. Landing: [guides.md](./guides.md).

## The one lever

```bash
export ADRA_CLIENT_DIR=/path/to/your/standards
# or programmatically:
#   load_settings(client_dir=Path("/path/to/your/standards"))
```

Default (unset): the bundled `adra/clients/synthetic/northwind/`. Resolution is in
`adra/utils.client_dir()` and `Settings.client_dir`.

## What a client suite contains

The bundled Northwind suite is the template — mirror its shape:

```
<your-standards>/
├── README.md            client profile + index
├── conventions.md       language / naming / branching / PR body / labels
├── ci-standards.md      the exact CI command, coverage, test discovery, bundle validate
├── glossary.md          domain + platform terms
├── adr/ADR-0001..N      the client's architecture decision records
└── cases/CASE-….md      anonymized post-incident notes the rubric is learned from
```

`adra/utils.load_standard("adr/ADR-0002-…")` loads any document from the active suite (returns ''
if absent, so a partial suite degrades cleanly).

## How the engine uses the suite

- The **rubric** references the suite by id (each `RubricItem.incident` cites an `ADR-xxxx` /
  `CASE-xxxx`).
- The **prompts** cite it (the critic/judge role prompts are written for "the active client").
- The **engine code does not change** — it is client-agnostic by construction (ADR-0007). No real
  client, mining, or single-industry framing ships in the engine.

## Steps to point at your own client

1. Author the suite folder above (start by copying the Northwind one).
2. Update the **rubric incident references** in `adra/rubric.py` to your `ADR-`/`CASE-` ids (the
   criteria themselves are usually portable; the *citations* are client-specific).
3. `export ADRA_CLIENT_DIR=/path/to/your/standards`.
4. Run as usual — `adra review …`, `adra pr-eval …`, etc. The deterministic floor (git / CI /
   bundle / language) is universal; the standards suite tunes the *conformance* and *incident*
   grounding.

## Multi-industry synthetic clients

Additional fictional clients can live under `adra/clients/synthetic/` and be selected the same way
— useful for demos across industries without referencing any real organization (ADR-0007).

## What this IS and is NOT

- **IS** configuration-plus-a-folder retargeting; the engine is reused, not forked.
- **IS NOT** a place for secrets. A client suite is governance documents only — no credentials.

## See also

- [../methodologies/03_shared-rubric.md](../methodologies/03_shared-rubric.md) — rubric ↔ standards.
- [../adr/ADR-0007-client-agnostic-grounding.md](../adr/ADR-0007-client-agnostic-grounding.md)
- [../use-cases/use-cases.md](../use-cases/use-cases.md) — the skills that ground on the suite.
