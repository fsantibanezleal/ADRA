# 05 · Human escalation (never silent approval)

Adversarial review is worthless if the critic is advisory. ADRA's critic is **mandatory and
blocking**, and when blockers cannot be resolved the run **escalates to a human** with evidence and
a recommendation. Escalation is **correct behavior, not failure** (ADR-0005).

Read order: 04 → **05**. Landing: [methodologies.md](./methodologies.md).

## The escalation mechanic

In `orchestrator.run`, after the critic loop:

- `decision = "accepted"` only when the critic returns clean.
- `decision = "escalate"` when blocking findings survive `max_rounds` (default 3) revisions.

The default `revise` (`skills/base.py`) records the unresolved blockers on the draft, so the loop
**cannot mask** a blocker into a false "accepted". The CLI returns a non-zero exit code on
escalation (`_print_run` returns `2` when `decision != "accepted"`), so escalation is machine-
detectable.

## What stays human-owned

High-consequence actions are never autonomous:

| Action | Why it stays human |
|---|---|
| Creating / merging PRs, pushing | irreversible or high-blast-radius; gated behind `allow_external` **and** explicit confirmation |
| Running the engine against a live repo / warehouse | tools only call out with `--external`; default is dry-run / read-only |
| Any decision-support **risk claim** | outputs are decision support, not guaranteed event detection (ADR-0007) |
| Picking a route in `decide` | the route-analysis skill prepares options + a recommendation; `decision_owner` defaults to **`human`** |

The `decide` skill is the explicit formalization of this: it produces a routes table scored on
**effort · blast radius · reversibility · risk · precedent**, a recommendation, and an explicit
**human-owned** decision (see [../use-cases/06_decide.md](../use-cases/06_decide.md)). The judge
reinforces it too — a verdict that is **not stable under position swap** routes to escalation
rather than an arbitrary pick (ADR-0005; see [02_llm-as-judge.md](./02_llm-as-judge.md)).

## Why (the governance basis)

| Principle | Source | In ADRA |
|---|---|---|
| Govern / map / measure / **manage** AI risk; keep humans in control of high-consequence calls | **NIST AI RMF — GenAI Profile** (`AI 600-1`, 2024) | the human gates above; provenance for every run |
| High-impact agent actions must be **gated** (dry-run by default) | **ToolEmu** (Ruan 2023, `arXiv:2309.15817`) | writes require `--external` + confirmation |
| Use **decision support**, not black-box event "detection", for high-stakes calls | **Rudin 2019** (`arXiv:1811.10154`) | the `overclaim_language` rubric item; `decide` is human-owned |

The agent prepares evidence and a recommendation; a person decides. This is the difference between
an autonomous coder that treats "tests pass" as success and ADRA, which treats an unresolved
blocker as a reason to **stop and ask**.

## What this IS and is NOT

- **IS** disciplined escalation with a hard, non-maskable gate and explicit human ownership of
  high-consequence actions.
- **IS NOT** automation that silently approves. There is no path in the loop from "blockers
  survive" to "accepted".

## References

NIST AI RMF GenAI Profile (`AI 600-1`) · ToolEmu (Ruan 2023, `arXiv:2309.15817`) · Rudin 2019
(`arXiv:1811.10154`). See [../../refs/README.md](../../refs/README.md) §5–6.

## See also

- [01_adversarial-spine.md](./01_adversarial-spine.md) — the loop that escalates.
- [../use-cases/06_decide.md](../use-cases/06_decide.md) — the human-owned route-analysis skill.
- [../security/security.md](../security/security.md) — the gated-write posture.
- [../adr/ADR-0005-blocking-critic-and-escalation.md](../adr/ADR-0005-blocking-critic-and-escalation.md)
