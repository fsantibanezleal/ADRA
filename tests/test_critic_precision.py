"""Tests for the critic precision/recall additions: ensemble aggregation, the
refutation gate, and severity ranking. All run offline with scripted chat models
(no provider, no network)."""

from __future__ import annotations

from adra import critic as critic_mod
from adra.config import Settings
from adra.llm import ChatModel
from adra.state import RunState, Severity, ToolResult, finding


class ScriptedModel(ChatModel):
    """A chat model that returns queued responses in order and counts calls."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls = 0

    def generate(self, system: str, user: str) -> str:  # noqa: D401
        self.calls += 1
        return self._responses.pop(0) if self._responses else '{"clean": true, "blocking": []}'


def _state(skill: str = "improve", draft: str = "a benign english draft", grounding=None) -> RunState:
    return RunState(skill=skill, intake={}, draft=draft, grounding=grounding or {})


def test_backward_compatible_single_pass():
    model = ScriptedModel(['{"clean": false, "blocking": ["A"], "notes": "n"}'])
    verdict = critic_mod.criticize(model, _state())  # no settings -> single pass
    assert "A" in verdict.messages
    assert model.calls == 1


def test_ensemble_unions_independent_passes():
    model = ScriptedModel([
        '{"clean": false, "blocking": ["A"], "notes": "n1"}',
        '{"clean": false, "blocking": ["B"], "notes": "n2"}',
    ])
    verdict = critic_mod.criticize(model, _state(), Settings(critic_runs=2))
    assert {"A", "B"}.issubset(set(verdict.messages))
    assert model.calls == 2  # aggregated over two semantic passes


def test_refutation_gate_drops_refuted_candidates():
    model = ScriptedModel(['{"clean": false, "blocking": ["A", "B"], "notes": ""}'])
    refuter = ScriptedModel([
        '{"refuted": true, "reason": "already handled"}',    # kills A
        '{"refuted": false, "reason": "real, evidenced"}',   # keeps B
    ])
    verdict = critic_mod.criticize(
        model, _state(), Settings(critic_runs=1, refute=True, provider="anthropic"), refuter=refuter)
    assert "A" not in verdict.messages
    assert "B" in verdict.messages
    assert refuter.calls == 2


def test_refute_is_noop_offline_mock():
    model = ScriptedModel(['{"clean": false, "blocking": ["A"], "notes": ""}'])
    refuter = ScriptedModel(['{"refuted": true, "reason": "x"}'])
    # provider defaults to mock -> the refutation gate is skipped, candidate survives.
    verdict = critic_mod.criticize(model, _state(), Settings(refute=True), refuter=refuter)
    assert "A" in verdict.messages
    assert refuter.calls == 0


def test_findings_ranked_most_severe_first():
    grounding = {"t": ToolResult(tool="t", findings=[
        finding(Severity.MAJOR, "x", "a major issue"),
        finding(Severity.BLOCKER, "y", "a blocking issue"),
    ])}
    model = ScriptedModel(['{"clean": true, "blocking": []}'])
    verdict = critic_mod.criticize(model, _state(grounding=grounding), Settings())
    assert verdict.blocking[0].severity == Severity.BLOCKER
