# 06 · `decide` — route analysis ("paths to follow")

Given a problem and candidate routes, produce a decision artifact: a routes table with honest
trade-offs (effort · blast radius · reversibility · risk · precedent), a recommendation, and an
**explicit human-owned decision**. It mirrors how candidate routes are laid out for review before a
person chooses (ADR-0008; illustrative incident Northwind `CASE-2024-061`).

Landing: [use-cases.md](./use-cases.md). Code: `adra/skills/decide.py`,
prompt `adra/prompts/decide.md`.

## Input → grounding → output

| Stage | Detail |
|---|---|
| **Input** (intake) | `problem` + `routes: [str, …]` (candidate routes) |
| **plan** | declares tool: `lang_scan` |
| **ground** (deterministic) | `lang_tools.scan_language(problem)` |
| **generate** | model returns `{problem, routes:[{name,summary,effort,blast_radius,reversibility,risk,precedent}], recommendation, rationale, open_question, decision_owner}`; `decision_owner` defaults to **`human`** |
| **output** | `route_analysis.md` — Problem / Routes table / Recommendation / Rationale / Decision (Owner: **human** + open question) |

## The rubric items it enforces

| id | severity · kind | what it catches |
|---|---|---|
| `blast_radius` | MAJOR · semantic | shared CI templates / cross-domain libraries / prod data / irreversible ops; prefer the smallest reversible route and name the rollback |
| `unverified_claim` | MAJOR · deterministic (cross-cutting) | a trade-off asserted without a second method |
| `language_leak` | BLOCKER · deterministic (cross-cutting) | English-only + no AI-session leak |

The skill **prefers the smallest reversible route justified against a precedent** and flags any
route that edits shared/templated assets (broad blast radius). The recommendation is exactly that —
a recommendation; the decision stays human-owned.

## Why human-owned

`decide` is the explicit formalization of [human escalation](../methodologies/05_human-escalation.md):
high-consequence calls are never autonomous. `decision_owner` is forced to `human`
(`data.setdefault("decision_owner", "human")`), and the artifact ends with the open question for the
person to resolve. ADRA prepares the evidence and a recommendation; a human decides (ADR-0007, NIST
AI RMF *manage*).

## Worked example (offline demo)

Problem: "Raise the catalog refresh trigger cadence." Routes: "edit the shared `ndp-ci` trigger
template" (high blast radius, low reversibility, no precedent) vs "change cadence in the catalog
repo only" (low blast radius, high reversibility, sibling precedent). Recommendation: the
scoped repo change; **accepted**, owner **human**.

## Invoke

```bash
adra decide "Raise the refresh cadence" "edit the shared CI template" "change it in the owning repo"
```

## What this IS and is NOT

- **IS** a trade-off-explicit route analysis that prefers the smallest reversible route and leaves
  the call to a human.
- **IS NOT** an autonomous decision. The owner is always `human`; the artifact ends with an open
  question, not a committed action.

## See also

- [../methodologies/05_human-escalation.md](../methodologies/05_human-escalation.md)
- [../security/02_gated-writes.md](../security/02_gated-writes.md) — the gates a chosen route still
  passes through.
- [../adr/ADR-0007-client-agnostic-grounding.md](../adr/ADR-0007-client-agnostic-grounding.md)
