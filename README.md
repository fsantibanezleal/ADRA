# ADRA — Adversarial Dev Review Agent

> A **client-agnostic, deterministic-first, adversarial-validation engine** that supports
> the software lifecycle: it reviews PRs, designs and runs validation/refutation
> experiments, writes documentation back, and **escalates to a human** exactly where a
> senior engineer would. Governed by **LLM-as-Judge + a blocking adversarial critic**,
> grounded by **deterministic tools**, with **immutable provenance**. Runs **offline with
> no API key**.

`pip install adra` · Python ≥ 3.11 · Apache-2.0 · status: `v0.01.000` (engine cut)

---

## What's different

The AI-code-review market splits in two, and both miss the same spot:

- **Reviewers** (CodeRabbit, Greptile, Qodo, Korbit, Sourcery, Bito) feed linters into an
  LLM, but the **model's prose is the verdict** — hallucinated and "consistently-stated-
  but-false" findings leak through; the deterministic signals are inputs, never the gate.
- **Autonomous coders** (Devin, OpenHands, SWE-agent, Sweep) *write* code and treat
  "tests pass" as success rather than adversarially trying to prove the change **wrong**.

ADRA occupies the gap: a **deterministic spine** (git / CI / static analysis / SQL probes)
that *grounds* a **blocking adversarial critic** whose job is to **refute**, not bless, each
artifact — every finding carrying its evidence, with disciplined **human escalation** when
nothing deterministic backs the verdict. Existing tools generate opinions; ADRA generates
proofs and refutations, and escalates when it can't.

## The six capabilities

| Skill | What it does |
|---|---|
| `code_review` | Review a diff: language/leak scan + test-discoverability + exact CI command + semantic findings |
| `pr_eval` | Evaluate a PR: merge-base health → `bundle validate` → conformance → verdict + PR body |
| `experiment` | Hypothesis-driven validation experiment: SQL-warehouse probes + synthesis |
| `improve` | Minimum-functional improvement proposal (prune filler, smallest safe diff) |
| `document` | Turn a run record into a PR page / experiment page / methodology-history row |
| `decide` | Route analysis: candidate routes + trade-offs + recommendation — **human-owned** |

Each skill is the same loop, differing only by its domain prompt and deterministic tools.

## Why deterministic-first

Tools (`git`, the exact CI command, `bundle validate`, language scan, SQL probe) run
**first** and become both the grounding the model may not contradict and the evidence in
the provenance log. Because the deterministic floor carries the verdict, the whole loop
runs — and the test suite passes — **offline with no API key**. Connecting a real provider
adds the semantic layer on top.

## Architecture

```
intake ─▶ plan ─▶ ground (deterministic tools) ─▶ generate ─▶ CRITIC ─┐
                                                      ▲   revise ◀──────┘
                                                      └── accepted / escalate ─▶ artifacts + run record
```

- `adra/state.py` — the typed **domain model** (`Severity`, `Finding`, `ToolResult`,
  `CriticVerdict`, `RunState`). One contract end to end.
- `adra/rubric.py` — the shared adversarial **rubric** (criteria as typed data); drives both
  the deterministic critic and the critic prompt, so "what we check" never drifts.
- `adra/orchestrator.py` — the hand-rolled, **framework-free** state machine.
- `adra/critic.py` — deterministic red-team pass (rubric-driven) + LLM semantic attacks.
- `adra/judge.py` — rubric scoring with **swap-and-average** + reference anchoring.
- `adra/llm.py` — the tiny ADRA-owned `ChatModel` seam: `mock` (offline) | `anthropic`
  (native SDK). No LangChain/LangGraph.
- `adra/tools/` — each returns a `ToolResult` (git / CI / bundle / lang / discovery / sql).
- `adra/skills/` — the `Skill` base + the six skills.
- `adra/clients/` — client governance suites (the bundled fictional **Northwind Data
  Platform**); selectable via `ADRA_CLIENT_DIR`.
- `adra/provenance.py` — the immutable run record (the deep change-history layer).
- `cli/` — the `adra` command. `refs/` — annotated bibliography + papers. `docs/` — deep
  docs + engine ADRs (`docs/adr/`).

## Quickstart (offline, no key)

```bash
python -m venv .venv && . .venv/Scripts/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q                                            # 11 passing, fully offline
python scripts/demo_offline.py                       # end-to-end demo, all six skills
```

Expected: the stale-base PR is **blocked + escalated** (12 commits behind, a notebook
deletion, a `.yml → .yml.t` rename dropping a bundle resource, `bundle validate` failing);
the language/leak review is **blocked**; the clean experiment / improve / document / decide
runs are **accepted**.

```bash
adra review path/to.diff --ci-command 'python -m coverage run -m unittest discover -s . -p "test*.py"'
adra decide "Raise the refresh cadence" "edit the shared CI template" "change it in the owning repo"
```

## Enable a real provider

```bash
pip install -e ".[anthropic]"            # native anthropic SDK; the seam is provider-agnostic
export ANTHROPIC_API_KEY=...             # or put it in .env
export ADRA_PROVIDER=anthropic
adra pr-eval --source task/123/x --repo /path/to/repo --external
```

`--external` (or `ADRA_ALLOW_EXTERNAL=1`) lets the tools actually run git / the CI command.
Default is **dry-run / read-only**.

## Client-agnostic grounding

A *client* = a governance suite (conventions, ADRs, CI standards, glossary, incident cases)
the engine grounds on. ADRA ships a complete, **fictional** client — **Northwind Data
Platform** — under `adra/clients/synthetic/northwind/`. Point ADRA at any client:

```bash
export ADRA_CLIENT_DIR=/path/to/your/standards   # or Settings(client_dir=...)
```

The rubric references the suite by id and the prompts cite it — the engine code does not
change per client.

## Connectors & emulator (next phase)

The engine grounds through one connector `Protocol` so the same skills run against a real
platform or a synthetic one:

- **Real**: GitHub (PRs/reviews/issues/contents via `githubkit`), Azure DevOps (REST 7.1),
  Databricks (`databricks-sdk` + bundles CLI), Azure (`azure-identity` + monitor / health).
- **Emulator**: a self-contained platform (synthetic git repos + PRs + wiki + boards + CI +
  a SQLite warehouse) so the full flow runs offline.

> These land in the next phase (the engine + offline mock are complete today). Roadmap +
> design: tracked in the private management repo's `wip/adra/plan.md`.

## Security model

Deterministic floor (tools are ground truth; the LLM cannot overturn a blocker) · read-only
by default (writes require `--external` **and** explicit human confirmation) · human gates on
PR create / push / merge and any risk claim · English-only + AI-authorship-leak scan on
anything written to disk · immutable provenance for every run. The agent reads **untrusted**
repo/PR/issue content — the connector phase adds a dual-LLM / capability split + sandboxed,
egress-filtered execution + authored-diff secret scanning (OWASP LLM/Agentic Top-10).

## Two-repo layout

ADRA is the **public-destined OSS engine** (this repo) — no secrets, ever. A separate
private **ADRA Console** (a Veta-style web app + backend) *consumes* this engine for
experiments and real connections behind access control. The engine is the serious tool you
can run anywhere with your own tokens; the console is the connected instance.

## Extending

- **New criterion:** add a `RubricItem` to `adra/rubric.py` (it shows up in the critic
  prompt and, if `kind="deterministic"`, wire its check in `critic.py`).
- **New capability:** add a `Skill` subclass + a `prompts/<skill>.md`, register it in
  `adra/skills/__init__.py`, add a `Node`.
- **New tool:** a function returning a `ToolResult`; call it from a skill's `ground`.
- **New provider:** a small `ChatModel` subclass in `adra/llm.py`.

## Status

`v0.01.000` — the engine is complete and green offline (11/11 tests). Real connectors, the
emulator, multi-industry synthetic clients, and the web console are the next phases. Stays
`0.x` while connectors are partly untested-live.

## License

Apache-2.0 — see [LICENSE](LICENSE).

## References

`refs/` holds an annotated bibliography (`refs/README.md`) + BibTeX (`refs/references.bib`)
+ the core papers (ReAct, Reflexion, Self-Refine, Constitutional AI, LLM-as-judge bias,
agentic security / CaMeL, NIST AI RMF, OWASP LLM/Agentic, provenance, code-review agents).
