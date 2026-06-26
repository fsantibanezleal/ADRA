# 01 · The orchestrated loop

ADRA runs every capability through **one loop**. A skill is five small steps the orchestrator
calls in order; the only difference between `code_review`, `pr_eval`, `experiment`, `improve`,
`document` and `decide` is the **prompt** they generate against and the **deterministic tools**
they ground on.

Read order for this node: **you are on 01.** Next: [02_layered-design.md](./02_layered-design.md),
then [03_data-flow.md](./03_data-flow.md). Landing page: [architecture.md](./architecture.md).

## The spine

```
plan ─▶ ground ─▶ generate ─▶ CRITIC ─▶ (revise ─▶ CRITIC)* ─▶ decide
```

![ADRA adversarial loop](../images/loop.svg)

| Step | Calls the LLM? | What it does | Code |
|---|---|---|---|
| `plan` | yes (cheap) | Classify the intake and declare which grounding tools this skill will run. | `Skill.plan` |
| `ground` | **no** | Run the deterministic tools; each returns a typed `ToolResult` (findings + raw evidence). | `Skill.ground`, `adra/tools/` |
| `generate` | yes | Produce the draft artifact (structured dict or markdown), grounded on the tool output. | `Skill.generate` |
| `CRITIC` | yes + deterministic | Two passes over the **same rubric**: a deterministic red-team (the hard floor) then an LLM semantic attack. Returns a `CriticVerdict`. | `adra/critic.py` |
| `revise` | yes | Address the critic's blocking findings and re-enter the critic. Bounded by `max_rounds`. | `Skill.revise` |
| `decide` | no | `accepted` when the critic is clean; `escalate` when blockers survive `max_rounds`. Render artifacts; write the `RunRecord`. | `Orchestrator.run`, `Skill.finalize` |

The loop is implemented in `Orchestrator.run` (`adra/orchestrator.py`) — a single readable
method. Its core is literally:

```python
state.plan = impl.plan(self._model("plan"), self.settings, state)
state.grounding = impl.ground(self.settings, state)        # LLM-free
state.draft = impl.generate(self._model("generate"), self.settings, state)
while True:
    verdict = critic_mod.criticize(self._model("critic"), state)
    if verdict.clean:
        state.decision = "accepted"; break
    if state.rounds >= self.settings.max_rounds:
        state.decision = "escalate"; break
    state.rounds += 1
    state.draft = impl.revise(self._model("generate"), self.settings, state, verdict)
state.artifacts = impl.finalize(self.settings, state)
```

## Why a hand-rolled state machine (not an agent framework)

ADR-0002 records the decision. The whole flow is a fixed, six-node pipeline — there is no need
for a planner that invents arbitrary tool call sequences, and a heavy runtime would hide the one
property that matters most: **the critic is mandatory, blocking, and the last gate.** A
framework-free loop is:

- **Readable and auditable** — you can see in ~45 lines that nothing bypasses the critic and
  that every node writes a provenance event (`record.event(...)`).
- **Deterministic offline** — every LLM call is tagged with its `Node` (`adra/nodes.py`), so the
  offline `mock` provider answers per node and the loop runs identically with no key.
- **Stable under wrapping** — if a richer runtime is ever desired, the node contracts
  (`plan/ground/generate/critic/revise/finalize`) are the interface; nothing internal leaks.

## Per-role model routing inside one run

The orchestrator resolves a model **per role** (`plan` / `generate` / `critic` / `judge`) via a
`ModelRouter`, so a single run can orchestrate across providers — e.g. a strong model for the
critic/judge and a cheaper/faster one for generation (`ADRA_MODEL_CRITIC`, `ADRA_MODEL_GENERATE`;
see [guides/03_multi-provider-routing.md](../guides/03_multi-provider-routing.md)). An explicitly
passed `model` (tests / single-model runs) wins for every role.

## What this page IS and is NOT

- **IS** the canonical description of the control flow every skill obeys.
- **IS NOT** a description of *what each skill checks* — that is the rubric
  ([methodologies/03_shared-rubric.md](../methodologies/03_shared-rubric.md)) and the per-skill
  use-case pages ([use-cases/](../use-cases/use-cases.md)).

## See also

- [02_layered-design.md](./02_layered-design.md) — the three layers and the module map.
- [04_run-sequence.md](./04_run-sequence.md) — the same loop traced concretely for `pr_eval`.
- [methodologies/01_adversarial-spine.md](../methodologies/01_adversarial-spine.md) — the
  research lineage of generate→critic→revise (Reflexion, Self-Refine, Constitutional AI).
