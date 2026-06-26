# Design

## Domain model (one typed contract)

Every step speaks the same dataclasses (`adra/state.py`); nothing passes ad-hoc
dicts. This is what makes the critic and skills composable and the run record
auditable.

![Domain model](images/domain_model.svg)

A `RunRecord` (`provenance.py`) mirrors `RunState` as an append-only, JSON event log.

## Key design decisions

| Decision | Why | Where |
|---|---|---|
| **Deterministic-first** | Tools are ground truth; the LLM can't contradict them. Verdicts carry evidence, not opinion. | `tools/`, `critic.deterministic_attacks` |
| **Shared rubric** | The adversarial criteria are data, used by both the deterministic checks and the critic prompt — code and prompt can't diverge. | `rubric.py` |
| **Blocking critic + escalation** | Never silently approve; unresolved blockers go to a human. | `orchestrator.run` |
| **Bias-aware judge** | Swap-and-average + reference anchoring counter position/verbosity/self-preference bias. | `judge.py` |
| **Provider factory + offline mock** | Vendor-agnostic; runs and tests with no API key. | `llm.py` |
| **Read-only by default** | Tools never call git/databricks/CI unless `allow_external`; no real PR is created. | `config.Settings`, every tool |
| **Externalized prompts + client standards** | Swap `prompts/` and the active client dir (`ADRA_CLIENT_DIR`) to retarget; no code change. | `prompts/`, `adra/clients/` |
| **Immutable provenance** | One auditable record per run = the deep change-history. | `provenance.py` |

## How the pieces interrelate

- A **skill** owns five steps (`plan/ground/generate/revise/finalize`); only
  `ground` is deterministic. Skills differ only by **prompt + tools**.
- The **critic** is skill-agnostic: it reads `RunState.grounding` (typed
  `ToolResult`s) + the `rubric` items applicable to the skill, and produces a
  `CriticVerdict`. It is the single enforcement point.
- The **rubric** maps each criterion to a **client standard** (`ADR-xxxx` /
  `CASE-xxxx`) in the active client dir; `prompt_block(skill)` renders the applicable
  items into the critic prompt.
- The **judge** is used wherever scoring/comparison is needed (it is its own module
  so it can be reused outside the loop).

## Extension points

![Extension points](images/extension_points.svg)

See [operations.md](operations.md) for the concrete steps.
