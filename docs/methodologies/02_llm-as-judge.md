# 02 · LLM-as-a-judge (swap-and-average + bias)

When ADRA scores a PR / experiment / doc, it is acting as an **LLM-as-a-judge**, a setup with
well-documented failure modes (position, verbosity, self-preference bias). `adra/judge.py` bakes
in the standard mitigations; the judge's role prompt is externalized (`prompts/judge.md`).

Read order: 01 → **02** → 03. Landing: [methodologies.md](./methodologies.md).

## The weighted rubric (the scoring equation)

`score(model, artifact, reference, rubric)` asks the model to rate each criterion in `[0,1]`
anchored to a reference, then computes a weighted total. The default weights
(`judge.DEFAULT_RUBRIC`) put correctness and evidence first:

| Criterion | Weight |
|---|---|
| `correctness` | 0.30 |
| `evidence_grounding` (claims backed by a second method / exact command) | 0.25 |
| `conformance` (matches existing repo convention / contract) | 0.20 |
| `minimum_functional` (only what advances the result) | 0.15 |
| `clarity` | 0.10 |

The total is the weighted sum:

$$\text{total} = \sum_{c} s_c \, w_c, \qquad s_c \in [0,1], \quad \sum_c w_c = 1$$

In code: `total = sum(by[c] * w for c, w in rubric.items())`. A mock-safe default of `0.7` per
criterion keeps the offline path well-defined.

## The three bias mitigations

LLM judges have known biases (Zheng et al. 2023, MT-Bench, `arXiv:2306.05685`; and rubric-ordering
bias — "Am I More Pointwise or Pairwise? Revealing Position Bias in Rubric-Based LLM-as-a-Judge",
`arXiv:2602.02219`). ADRA counters each:

1. **Swap-and-average (position bias).** `compare(model, a, b, ...)` scores both artifacts
   head-to-head in one prompt, then re-scores with the order reversed, and averages the two; a
   winner is trusted only when it is **stable under the swap**
   (`position_consistent = (forward == reverse)`). The averaged winner is:

   $$\text{winner} = \arg\max\big(\tfrac{s_a + s_a'}{2},\ \tfrac{s_b + s_b'}{2}\big)$$

   Disagreement under swap is a signal to **escalate** (ADR-0005), not to pick arbitrarily.
   Toggle via `Settings.judge_swap_average` (default `True`).
2. **Reference anchoring (taste/prior bias).** Scores are anchored to a concrete reference — the
   **exact CI command**, the **existing repo convention**, or the **data contract** — not the
   model's prior. The prompt: "Anchor to the reference; do not reward verbosity."
3. **Verbosity & self-preference.** The externalized `prompts/judge.md` instructs: reward evidence
   and correctness, never length; judge on the rubric, not on whether the artifact matches how the
   judge would have written it. Position bias is handled by the caller (swap-and-average), so each
   artifact is judged on its merits.

## Separation from the critic

The judge is its **own module** so it can be reused outside the loop (scoring/comparison anywhere),
and so the model that judges can differ from the model that generates or critiques (per-role
routing: `ADRA_MODEL_JUDGE`). ADR-0005: "The judge uses a separate model … disagreement under
position swap routes to escalation."

## What this IS and is NOT

- **IS** a bias-aware, reference-anchored, rubric-weighted scorer with logged raw verdicts.
- **IS NOT** a single ungrounded "rate this 1–10" call. Position/verbosity/self-preference are
  explicitly mitigated, and an unstable verdict escalates rather than guesses.

## References

Zheng et al. 2023 (MT-Bench, `arXiv:2306.05685`) · "Am I More Pointwise or Pairwise? Revealing
Position Bias in Rubric-Based LLM-as-a-Judge" (`arXiv:2602.02219`) — motivates the swap direction
(its balanced score-option permutation is not implemented here). See
[../../refs/README.md](../../refs/README.md) §3.

## See also

- [01_adversarial-spine.md](./01_adversarial-spine.md) — the critic the judge complements.
- [03_shared-rubric.md](./03_shared-rubric.md) — the criteria source.
- [../frameworks/01_pydantic-ai/03_usage-and-gotchas.md](../frameworks/01_pydantic-ai/03_usage-and-gotchas.md)
  — routing a strong model to the judge.
