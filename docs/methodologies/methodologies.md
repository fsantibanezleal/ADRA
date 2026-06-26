# Methodologies

The methods that make ADRA's verdicts defensible rather than opinionated. Five spines, each
grounded in the engine code **and** in validated literature (real DOIs/arXiv ids from
[`../../refs/references.bib`](../../refs/references.bib)).

## Read in order

1. [01_adversarial-spine.md](./01_adversarial-spine.md) — the generate → critic → revise loop:
   refute, don't bless; the research lineage (ReAct, Reflexion, Self-Refine, Constitutional AI,
   multi-agent debate) and why the critic is blocking.
2. [02_llm-as-judge.md](./02_llm-as-judge.md) — LLM-as-a-judge with documented bias mitigations:
   swap-and-average, reference anchoring, rubric weighting — with the scoring equation.
3. [03_shared-rubric.md](./03_shared-rubric.md) — one typed rubric as the single source of the
   criteria; deterministic vs semantic items; the "code and prompt can't drift" property.
4. [04_deterministic-first.md](./04_deterministic-first.md) — grounding-first ("don't infer —
   diagnose"): tools settle what they can, the model adds the rest, the floor carries the verdict.
5. [05_human-escalation.md](./05_human-escalation.md) — disciplined escalation: never silent
   approval; what stays human-owned and why (NIST AI RMF *manage/govern*).

## The spine at a glance

| Method | Core claim | Engine locus | Key references |
|---|---|---|---|
| Adversarial validation | The critic's job is to **refute** each artifact, not bless it; bounded revise then escalate. | `orchestrator.py`, `critic.py` | Reflexion · Self-Refine · Constitutional AI · multi-agent debate · *Spontaneous Reward Hacking* |
| LLM-as-judge + bias | Scoring with **swap-and-average + reference anchoring + rubric weights** counters position/verbosity/self-preference bias. | `judge.py`, `prompts/judge.md` | MT-Bench (Zheng 2023) · position-bias-in-rubric-judges |
| Shared rubric | The adversarial criteria are **data**, consumed by both the deterministic checks and the critic prompt. | `rubric.py` | Constitutional AI (critique against written principles) |
| Deterministic-first | Tools run first, are ground truth, carry the verdict; the model adds only what tools can't settle. | `tools/*`, `critic.deterministic_attacks` | *Why LMs Hallucinate* · *Calibrated LMs Must Hallucinate* · *Spontaneous Reward Hacking* |
| Human escalation | High-consequence calls stay human-owned; escalation is correct behavior, not failure. | `orchestrator.run`, `decide` skill | NIST AI RMF (GenAI Profile) · ToolEmu · Rudin 2019 (decision support) |

## What this section IS and is NOT

- **IS** the methodological backbone tied to specific engine code and real sources.
- **IS NOT** a research survey for its own sake — every method here is *implemented*. Where a paper
  is cited, it explains a choice that exists in `adra/`, not an aspiration.

## See also

- [../architecture/architecture.md](../architecture/architecture.md) — how these methods are wired.
- [../../refs/README.md](../../refs/README.md) — the annotated bibliography (grouped by pillar).
- [../use-cases/use-cases.md](../use-cases/use-cases.md) — the methods applied per skill.
