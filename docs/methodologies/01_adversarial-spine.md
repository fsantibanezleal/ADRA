# 01 · The adversarial-validation spine

ADRA's loop is `plan → ground → generate → CRITIC → (revise → CRITIC)* → decide`. The defining
move is the **CRITIC**: its job is to **refute** the draft, not to bless it. Existing tools
generate opinions; ADRA generates proofs and refutations, and escalates when it can't.

Read order: **01** → 02. Landing: [methodologies.md](./methodologies.md).

## The two-pass critic (`adra/critic.py`)

`criticize(model, state)` runs two passes over the **same rubric** and merges their blocking
findings (deduped by `(category, message)`):

1. **`deterministic_attacks` — the hard floor.** Collects the blocking findings already raised by
   the grounding tools, plus critic-level rubric checks: an unverified-claim language scan
   (`probably`, `i assume`, `likely`, `seems to`, `no access`, …), the exact-CI-reproduced check
   for review skills, the "no access without preflight" check for experiments, and an AI-leak /
   language scan of the draft text itself. These are non-overridable.
2. **`llm_critique` — semantic attacks.** Asks the model to *break* the draft against the rubric
   ("Try to BREAK it. Return JSON {clean, blocking, notes}") — catching what tools cannot encode:
   a hidden assumption, a contract the change quietly widens, a place it would harm production, a
   conclusion the data doesn't support.

`clean` is true only when **no** blocking finding survives either pass. The critic's role prompt
is externalized (`prompts/critic.md`) and explicitly forbids re-litigating what the deterministic
floor settled.

## Bounded revise, then escalate (`orchestrator.run`)

```
while True:
    verdict = criticize(...)
    if verdict.clean:        decision = "accepted"; break
    if rounds >= max_rounds: decision = "escalate"; break
    rounds += 1
    draft = revise(..., verdict)
```

The loop is **bounded** by `max_rounds` (default 3). If blockers survive revision, the run
**escalates to a human** with the evidence and a recommendation — it never silently approves
(ADR-0005). The default `revise` records the unresolved blockers on the draft, so the loop *cannot
mask* a blocker (`skills/base.py`).

## Research lineage (and where each idea lands)

| Idea | Source | In ADRA |
|---|---|---|
| Interleaved reason → act → observe | **ReAct** (Yao 2023, `arXiv:2210.03629`) | `plan → ground → generate` |
| Tool-grounded self-critique improves outputs | **Reflexion** (Shinn 2023, `arXiv:2303.11366`) | the generate→critic→revise loop |
| Iterative refinement (and its limits) | **Self-Refine** (Madaan 2023, `arXiv:2303.17651`) | the bounded revise loop |
| Critique against an explicit written set of principles | **Constitutional AI** (Bai 2022, `arXiv:2212.08073`) | the shared rubric injected into the critic prompt |
| Adversarial cross-examination | **Multi-agent debate** (Du 2023, `arXiv:2305.14325`) | the critic as a separate adversary to the generator |
| Ungrounded self-refinement games its reward | **Spontaneous Reward Hacking** (`arXiv:2407.04549`) | **why the critic's first pass is deterministic** |

The last row is the crux: Reflexion/Self-Refine help **only when feedback is grounded**. So
ADRA's critic runs the deterministic floor first and treats it as ground truth — the LLM pass may
only *add* attacks, never overturn a tool's blocker (see
[04_deterministic-first.md](./04_deterministic-first.md)).

## What this IS and is NOT

- **IS** a blocking, refutation-oriented critic with bounded revision and honest escalation.
- **IS NOT** "self-refine until the model is happy". The critic is adversarial and grounded, and
  the loop terminates in `accepted` or `escalate` — never an unbounded self-approval.

## References

ReAct (`arXiv:2210.03629`) · Reflexion (`arXiv:2303.11366`) · Self-Refine (`arXiv:2303.17651`) ·
Constitutional AI (`arXiv:2212.08073`) · Multi-Agent Debate (`arXiv:2305.14325`) · Spontaneous
Reward Hacking (`arXiv:2407.04549`). See [../../refs/README.md](../../refs/README.md) §1–2.

## See also

- [02_llm-as-judge.md](./02_llm-as-judge.md) · [03_shared-rubric.md](./03_shared-rubric.md) ·
  [05_human-escalation.md](./05_human-escalation.md)
- [../adr/ADR-0005-blocking-critic-and-escalation.md](../adr/ADR-0005-blocking-critic-and-escalation.md)
