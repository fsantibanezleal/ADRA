# ADR-0005 — Blocking critic + human escalation (never silent approval)

**Status:** Accepted

## Context
The value of adversarial review is lost if the critic is advisory. High-consequence calls
(merging, pushing, risk claims) must stay human-owned.

## Decision
The critic is **mandatory and blocking**, run in two passes (deterministic hard-floor + LLM
semantic attacks) over the same rubric. An artifact is `accepted` only when no blocking
finding survives; otherwise the loop revises up to `max_rounds` and then `escalate`s to a
human with the evidence and a recommendation. The judge uses a separate model with
swap-and-average + reference anchoring; disagreement under position swap routes to escalation.

## Consequences
- Automation is never silent approval; escalation is correct behavior, not failure.
- The LLM-as-judge's known biases (position, verbosity, self-preference) are mitigated and
  its raw verdicts are logged.
