# NDP conventions

## Language & authorship
- Everything written to disk is **English**: code, docstrings, comments, commit
  messages, PR titles/descriptions, test names, file and folder names.
- **Third person.** No first-person singular in code, docs, commits or PRs.
- **No AI-session leak.** Nothing written to a repo may reveal AI authorship
  (no `Claude`, `Anthropic`, `Co-Authored-By`, "generated with AI", etc.). See
  `adr/ADR-0006`.

## Naming
- Catalogs: `<env>_<domain>_<subdomain>` — e.g. `prod_orders_fulfilment`. `env` ∈
  `dev` / `preprod` / `prod`.
- Schemas follow the medallion split: `landing` / `trusted` / `refined`.
- DAB resource files: `bundle.resources.<kind>.yml` and they **stay `.yml`** (see
  `adr/ADR-0003`).
- Notebooks: `nb-<purpose>.py` with the `# Databricks notebook source` header.

## Branching & tickets
- Integration branch: `main`. Never commit product changes directly to `main`.
- Work branches: `task/<NDP-####>/<short-slug>`, always rebased on a fresh `main`
  (see `adr/ADR-0002`).
- Tickets are `NDP-####`; every PR links its ticket.

## Pull requests
PR description uses these sections, in order:

```
## Objective
## Changes
## What is NOT touched
## Validation        (exact CI command output; `bundle validate` OK)
## Risks / mitigations
## Test plan
## Work Item         (NDP-####)
```

- Reference another PR by its **full URL**, never a bare `#NNNN`.
- Use **commit-pinned** file links (`?version=GC<full-sha>`) so links survive the merge.
- Apply the owning team's **labels** before completing the PR.
- A PR with any deterministic blocker is **changes-requested** regardless of opinion.

## Decision-support framing
`analytics` products are **decision support**: outputs are *forecasts, risk scores and
recommendations* with their evidence — never claims to "guarantee", "prevent",
"detect" or "predict" an outcome (see `adr/ADR-0007`).
