"""The judge: rubric-based scoring with documented bias mitigations.

When ADRA scores a PR / experiment / doc it is acting as an LLM-as-a-judge, which
has well-documented failure modes (position, verbosity, self-preference bias).
This module bakes in the standard mitigations:

- **Swap-and-average** for any pairwise comparison (evaluate twice, both orders).
- **Reference-anchored** scoring (anchor to the exact CI command / the existing
  repo convention / the data contract) rather than prompt-only.
- **Rubric-based** deterministic criteria with explicit weights.

See ``refs/`` (LLM-as-judge bias mitigations) for sources.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from adra.llm import ChatModel, invoke_text
from adra.nodes import Node
from adra.utils import load_prompt, parse_json

# Default rubric: criterion -> weight. Tuned to our priorities (correctness and
# evidence dominate; style is a tie-breaker).
DEFAULT_RUBRIC: dict[str, float] = {
    "correctness": 0.30,
    "evidence_grounding": 0.25,  # claims backed by a second method / exact command
    "conformance": 0.20,  # matches existing repo convention / contract
    "minimum_functional": 0.15,  # only what advances the result
    "clarity": 0.10,
}


@dataclass
class Score:
    total: float
    by_criterion: dict[str, float] = field(default_factory=dict)
    reference_used: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "total": round(self.total, 3),
            "by_criterion": {k: round(v, 3) for k, v in self.by_criterion.items()},
            "reference_used": self.reference_used,
            "notes": self.notes,
        }


def score(
    model: ChatModel,
    artifact: str,
    reference: str = "",
    rubric: dict[str, float] | None = None,
) -> Score:
    """Score a single artifact against a reference using the weighted rubric."""
    rubric = rubric or DEFAULT_RUBRIC
    criteria = ", ".join(rubric)
    user = (
        "Score the ARTIFACT against the REFERENCE on each criterion in [0,1]. "
        "Anchor to the reference; do not reward verbosity. Return JSON "
        f"{{scores: {{<criterion>: float}}, notes: str}}. Criteria: {criteria}.\n\n"
        f"REFERENCE:\n{reference or '(none)'}\n\nARTIFACT:\n{artifact}"
    )
    system = load_prompt("judge") or "You are a rubric-based judge."
    data = parse_json(invoke_text(model, system, user, node=Node.JUDGE))
    raw = data.get("scores", {}) if isinstance(data, dict) else {}
    by = {c: float(raw.get(c, 0.7)) for c in rubric}  # mock-safe default
    total = sum(by[c] * w for c, w in rubric.items())
    return Score(total=total, by_criterion=by, reference_used=reference[:80],
                 notes=str(data.get("notes", "")))


def compare(
    model: ChatModel,
    a: str,
    b: str,
    reference: str = "",
    swap_average: bool = True,
) -> dict:
    """Pairwise winner with position-bias mitigation (swap-and-average)."""
    sa = score(model, a, reference)
    sb = score(model, b, reference)
    forward = "A" if sa.total >= sb.total else "B"
    result = {
        "forward": {"A": sa.to_dict(), "B": sb.to_dict(), "winner": forward},
        "winner": forward,
        "position_consistent": True,
    }
    if swap_average:
        # Re-score with positions swapped; only trust a winner stable under swap.
        sb2 = score(model, b, reference)
        sa2 = score(model, a, reference)
        reverse = "A" if sa2.total >= sb2.total else "B"
        avg_a = (sa.total + sa2.total) / 2
        avg_b = (sb.total + sb2.total) / 2
        winner = "A" if avg_a >= avg_b else "B"
        result.update(
            reverse={"winner": reverse},
            averaged={"A": round(avg_a, 3), "B": round(avg_b, 3), "winner": winner},
            position_consistent=(forward == reverse),
            winner=winner,
        )
    return result
