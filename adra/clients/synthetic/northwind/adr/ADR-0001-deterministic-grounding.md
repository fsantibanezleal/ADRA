# ADR-0001 — Deterministic-first grounding and second-method proof

**Status:** Accepted

## Context
Reviews and experiments that rely on a reviewer's narrative ("this looks fine",
"that's probably because…") let unverified claims through. Plausible explanations
without verification have caused rework and missed defects.

## Decision
- Deterministic, high-precision checks (the exact CI command, `bundle validate`,
  git merge-base, language scan, SQL probes) run **first** and are **ground truth**.
- Any cause or outcome must be backed by a **second, independent method** (a probe,
  a re-run of the exact command, a cross-check) or stated as **"unknown"**.
- An LLM may only add findings the deterministic tools cannot settle; it may not
  contradict them.

## Consequences
- Verdicts carry evidence, not opinion.
- The agent reproduces the exact thing under test instead of approximating.
- See `cases/CASE-2024-058` (an anomaly confirmed only after live verification).
