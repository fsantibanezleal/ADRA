# 05 · Why deterministic-first

The defining architectural choice (ADR-0001): deterministic tools run **before** the LLM and
carry the verdict. This page is the theory behind it — the failure modes it closes and what it
buys.

Read order: 04 → **05**. Landing: [architecture.md](./architecture.md).

## The market gap it answers

The AI-code-review space splits in two, and both miss the same spot:

- **Reviewers** (CodeRabbit, Greptile, Qodo, Korbit, Sourcery, Bito) feed linters into an LLM,
  but **the model's prose is the verdict** — hallucinated and "consistently-stated-but-false"
  findings leak through; the deterministic signals are inputs, never the gate.
- **Autonomous coders** (Devin, OpenHands, SWE-agent, Sweep) *write* code and treat "tests pass"
  as success rather than adversarially trying to prove the change **wrong**.

ADRA occupies the gap: a **deterministic spine** that *grounds* a **blocking adversarial critic**
whose job is to **refute**, not bless, each artifact — every finding carrying its evidence, with
disciplined **human escalation** when nothing deterministic backs the verdict.

## The two failure modes it closes

### 1. Hallucination is intrinsic, not a bug to be prompted away

*Why Language Models Hallucinate* (Kalai et al., 2025) and *Calibrated LMs Must Hallucinate*
(Kalai & Vempala, 2023) make the statistical case that a calibrated language model will produce
confident, false statements at some rate — it cannot be fully eliminated by better prompting.
The architectural response is **not to trust the model as the arbiter**: settle everything a tool
*can* settle with the tool, and require the model to "verify with an independent method or say
'unknown'" for the rest. In the rubric this is the `unverified_claim` item ("don't infer —
diagnose").

### 2. Ungrounded self-refinement games its own reward

*Reflexion* (Shinn et al., 2023) and *Self-Refine* (Madaan et al., 2023) show iterative
self-critique helps — **when the feedback is grounded**. *Spontaneous Reward Hacking in Iterative
Self-Refinement* shows the opposite: a critic that scores against its own prior, with no external
ground truth, learns to satisfy itself rather than the task. ADRA's critic therefore runs a
**deterministic red-team pass first** (the hard floor) and treats it as non-overridable; the LLM
pass may only *add* attacks the tools cannot encode.

## The precision argument

Best-in-class review combines **high-precision deterministic static analysis** with an LLM for
semantic findings. Deterministic checks (git merge-base, the exact CI command, `bundle validate`,
the language scan, a glob-based test-discovery check) have near-zero false-positive rates because
they measure a fact, not an opinion. Putting them first means the verdict has a hard,
evidence-backed base, and the model is confined to the genuinely semantic surface (swallowed
errors, contract drift, hidden coupling) where it adds value and where a mistake is cheap to
review.

## What it buys

| Property | Because… |
|---|---|
| **Runs offline, no API key** | the deterministic floor alone produces a real adversarial outcome; the `mock` provider fills the semantic layer with thin, non-inventive text. The test suite is fully offline. |
| **Verdicts carry evidence** | every blocking `Finding` has an `evidence` string from a tool, persisted in the `RunRecord`. |
| **Auditable** | the second-method proof and the critic verdicts are in the immutable run record (ADR-0006). |
| **Safe to connect** | a real provider only *adds* the semantic layer; it can never overturn a deterministic blocker. |

## What this IS and is NOT

- **IS** a design that makes the *floor* authoritative and the *model* additive.
- **IS NOT** a claim that the LLM is unimportant — the semantic pass is where contract drift and
  swallowed errors are caught. It is a claim about **ordering and authority**: tools decide what
  they can; the model decides only the rest; the human decides anything high-consequence.

## References

ADR-0001 · Kalai et al. 2025 (`arXiv:2509.04664`) · Kalai & Vempala 2023 (`arXiv:2311.14648`) ·
Shinn et al. 2023 (`arXiv:2303.11366`) · Madaan et al. 2023 (`arXiv:2303.17651`) · *Spontaneous
Reward Hacking* (`arXiv:2407.04549`). See [../../refs/README.md](../../refs/README.md) §2, §4.

## See also

- [methodologies/04_deterministic-first.md](../methodologies/04_deterministic-first.md) — the
  methodology framing of the same principle.
- [methodologies/01_adversarial-spine.md](../methodologies/01_adversarial-spine.md) — the
  generate→critic→revise lineage.
