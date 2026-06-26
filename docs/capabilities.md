# Capabilities

Six skills, one loop. Each shares `plan → ground → generate → critic → revise →
finalize` and differs only by its prompt (`prompts/<skill>.md`) and the deterministic
tools it grounds on. All are vendor/model-agnostic and run offline with the mock.

| Skill | Input | Deterministic grounding | Output artifact | Focus |
|---|---|---|---|---|
| `code_review` | a diff / patch | language+leak scan · test-discoverability · exact CI command | `review.md` (deterministic + semantic findings) | correctness, convention, EN, minimum-functional |
| `pr_eval` | a PR / branch | merge-base health · `bundle validate` · language scan | `pr_verdict.md` + `pr_body.md` | prevent destructive merges; conform to precedent |
| `experiment` | a hypothesis | SQL-warehouse probes · access preflight | experiment page + `v0X-synthesis` | reproducibility; conclude only from evidence |
| `improve` | a component | language scan · minimum-functional | `proposal.md` | smallest reversible diff; no filler |
| `document` | a run record | source-of-truth gap + leak scan | PR / experiment / methodology page | history that doesn't drift |
| `decide` | a problem + routes | language scan | `route_analysis.md` | smallest reversible route; human-owned call |

## How a skill enforces criteria

Each skill's `generate` is *advisory* (the prompt asks the model to behave); the
**critic enforces**. The deterministic blockers are non-negotiable: e.g. `pr_eval`
forces `changes-requested` whenever any grounding tool reports a blocker, regardless
of the model's verdict.

![Skill grounding & enforcement](images/capability_grounding.svg)

## `decide` — the "paths to follow" capability

The route-analysis skill is the formalization of how options are laid out in the
wips before a human chooses: candidate routes, each scored on **effort · blast
radius · reversibility · risk · precedent**, a recommendation, and an explicit
**human-owned** decision. It prefers the smallest reversible route justified against
a precedent (ADR-0008) and flags any route that edits shared/templated assets (broad
blast radius).

## Per-skill prompts

Operational depth lives in `prompts/<skill>.md` (method + artifact structure +
domain rules + ADR references) — see [governance.md](governance.md) for how the
rubric is injected and how the prompts cite the client standards.
