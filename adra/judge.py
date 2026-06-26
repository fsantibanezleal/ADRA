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


def _pairwise(
    model: ChatModel,
    first: str,
    second: str,
    reference: str = "",
    rubric: dict[str, float] | None = None,
) -> tuple[float, float, str]:
    """Score two artifacts presented TOGETHER, in this exact order (FIRST, SECOND).

    Both candidates sit in one prompt so the model judges them head-to-head; the
    caller varies the order across calls to expose position bias. Returns
    ``(first_total, second_total, notes)`` as weighted-rubric totals.
    """
    rubric = rubric or DEFAULT_RUBRIC
    criteria = ", ".join(rubric)
    user = (
        "Two candidate artifacts (FIRST and SECOND) answer the same task. Score EACH "
        "against the REFERENCE on every criterion in [0,1]; anchor to the reference and "
        "do not reward verbosity or length. Return JSON "
        f"{{first: {{<criterion>: float}}, second: {{<criterion>: float}}, notes: str}}. "
        f"Criteria: {criteria}.\n\nREFERENCE:\n{reference or '(none)'}\n\n"
        f"FIRST:\n{first}\n\nSECOND:\n{second}"
    )
    system = load_prompt("judge") or "You are a rubric-based judge."
    data = parse_json(invoke_text(model, system, user, node=Node.JUDGE))
    data = data if isinstance(data, dict) else {}

    def _total(key: str) -> float:
        raw = data.get(key, {})
        raw = raw if isinstance(raw, dict) else {}
        return sum(float(raw.get(c, 0.7)) * w for c, w in rubric.items())  # mock-safe default

    return _total("first"), _total("second"), str(data.get("notes", ""))


def compare(
    model: ChatModel,
    a: str,
    b: str,
    reference: str = "",
    rubric: dict[str, float] | None = None,
    swap_average: bool = True,
) -> dict:
    """Pairwise winner with a real position-bias mitigation (swap-and-average).

    A and B are scored head-to-head in one prompt (A first); when ``swap_average`` they
    are scored again with the order reversed (B first). Each artifact's two scores are
    averaged, and a winner is ``position_consistent`` only when it wins in BOTH orders;
    otherwise the averaged total breaks the tie. Because A occupies the first slot in the
    forward call and the second slot in the reverse call (and vice-versa for B), the swap
    genuinely varies artifact position — so it exercises and mitigates position bias rather
    than re-running an identical call.
    """
    fa, fb, fnotes = _pairwise(model, a, b, reference, rubric)  # A first, B second
    forward = "A" if fa >= fb else "B"
    result = {
        "forward": {"A": round(fa, 3), "B": round(fb, 3), "winner": forward},
        "winner": forward,
        "position_consistent": True,
        "notes": fnotes,
    }
    if swap_average:
        rb, ra, _ = _pairwise(model, b, a, reference, rubric)  # B first, A second
        reverse = "A" if ra >= rb else "B"
        avg_a = (fa + ra) / 2  # A's first-slot + second-slot scores
        avg_b = (fb + rb) / 2  # B's second-slot + first-slot scores
        winner = "A" if avg_a >= avg_b else "B"
        result.update(
            reverse={"A": round(ra, 3), "B": round(rb, 3), "winner": reverse},
            averaged={"A": round(avg_a, 3), "B": round(avg_b, 3), "winner": winner},
            position_consistent=(forward == reverse),
            winner=winner,
        )
    return result
