# ADRA — documentation

**ADRA — Adversarial Dev Review Agent** is a **client-agnostic, deterministic-first,
adversarial-validation engine** for the software lifecycle. It reviews PRs, designs and runs
validation/refutation experiments, writes documentation back from provenance, and **escalates
to a human** exactly where a senior engineer would. The substance lives in **deterministic
tools** + a **shared typed rubric**; an LLM is the semantic layer on top, so the whole engine —
and its test suite — **runs offline with no API key** (the deterministic `mock` provider).

`pip install adra` · Python ≥ 3.11 · Apache-2.0 · the engine core has **zero required
third-party dependencies**.

```
intake ─▶ plan ─▶ ground (deterministic tools) ─▶ generate ─▶ CRITIC ─┐
                                                      ▲   revise ◀──────┘
                                                      └── accepted / escalate ─▶ artifacts + RunRecord
```

## How to read this wiki

- **The wiki is a folder per theme.** Each theme has a **same-named landing page**
  (`architecture/architecture.md`, `frameworks/frameworks.md`, …) plus **numbered deep pages**
  inside it (`01_…`, `02_…`). Read a theme top to bottom for the full picture, or jump to the
  page you need.
- **All links are relative.** You navigate by the section indexes below and the per-page
  "See also" links — there is no single file that unifies the rest.
- **Everything here is checked against the engine code.** Where a page states what a module
  does, it reflects the actual implementation in `adra/`. Where it states a limit, it is a real
  limit. There are no aspirational claims dressed as shipped behaviour.

## The seven themes

| Theme | What it answers |
|---|---|
| [**Architecture**](./architecture/architecture.md) | The adversarial loop, the layered design, the typed data flow, a run sequence — the framework-free state machine and why deterministic-first. |
| [**Frameworks**](./frameworks/frameworks.md) | One subfolder per real library actually used (pydantic-ai · httpx · databricks-sdk · azure-identity + azure-monitor-query · stdlib/sqlite emulator) — what it is, why (ADR), how ADRA uses it, gotchas. |
| [**Methodologies**](./methodologies/methodologies.md) | The adversarial-validation spine, LLM-as-judge (swap-and-average + bias), the shared rubric, deterministic-first grounding, human escalation — with criteria/equations and validated references. |
| [**Guides**](./guides/guides.md) | How to USE the engine on **other** repos/data: install, the CLI (`review`/`pr-eval`/`experiment`/`improve`/`document`/`decide`/`github-review`/`emu`), `ADRA_CLIENT_DIR`, multi-provider/per-role routing, the local scripts. |
| [**Use cases**](./use-cases/use-cases.md) | One deep page per skill: input → grounding → output → the rubric items it enforces. |
| [**Data contract**](./data-contract/data-contract.md) | The intake contracts (diff/PR/experiment), the connector `PullRequest`/`Issue`/`DataProvider` shapes, the immutable `RunRecord`, and how missing/outlier data is handled (degrade lanes, gating). |
| [**Security**](./security/security.md) | Read-only by default, gated writes, dual-LLM/CaMeL split, untrusted-content posture, secret handling. |

## Other entry points

| Doc | Contents |
|---|---|
| [adr/](./adr/README.md) | The **engine's** Architecture Decision Records (distinct from a *client's* governance ADRs under `adra/clients/synthetic/<client>/adr/`). |
| [../refs/README.md](../refs/README.md) | Annotated bibliography (agent foundations, adversarial validation, LLM-as-judge bias, grounding, agent safety, governance/provenance). |
| [../README.md](../README.md) | Project README — quickstart, what's different, status. |
| [../CHANGELOG.md](../CHANGELOG.md) | Release history (newest → oldest). |

## The six capabilities at a glance

| Skill | What it does | Deep page |
|---|---|---|
| `code_review` | Review a diff: language/leak scan + test-discoverability + exact CI command + semantic findings | [01](./use-cases/01_code-review.md) |
| `pr_eval` | Evaluate a PR: merge-base health → `bundle validate` → conformance → verdict + PR body | [02](./use-cases/02_pr-eval.md) |
| `experiment` | Hypothesis-driven validation experiment: SQL-warehouse probes + synthesis | [03](./use-cases/03_experiment.md) |
| `improve` | Minimum-functional improvement proposal (prune filler, smallest safe diff) | [04](./use-cases/04_improve.md) |
| `document` | Turn a run record into a PR page / experiment page / methodology row | [05](./use-cases/05_document.md) |
| `decide` | Route analysis: candidate routes + trade-offs + recommendation — **human-owned** | [06](./use-cases/06_decide.md) |

Each skill is the **same loop**, differing only by its domain prompt (`adra/prompts/<skill>.md`)
and the deterministic tools it grounds on.

## What ADRA IS and is NOT

- **IS** a reference, **deterministic-first** orchestrator whose verdicts carry **evidence**, not
  opinion; an engine you can run anywhere offline and connect to real platforms with your own
  tokens (BYOK).
- **IS NOT** an autonomous coder, a linter wrapper whose "model prose is the verdict", or a
  production SaaS. It does not merge, push, or take high-consequence actions on its own — those
  stay human-owned (see [security](./security/security.md), [methodologies §human escalation](./methodologies/05_human-escalation.md)).

## Honesty

The only bundled client is **fictional and industry-neutral** (Northwind Data Platform, under
`adra/clients/synthetic/northwind/`). The emulator's synthetic PRs are labelled synthetic and
carry deterministically-catchable, real failure modes — not a toy. Every reference in
[../refs/](../refs/) is a real, citeable source.
