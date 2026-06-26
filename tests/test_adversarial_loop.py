"""Tests for the adversarial loop (offline, deterministic).

These assert the spine: destructive / non-compliant artifacts are blocked and
escalated; clean ones are accepted. They run with the mock provider, no API key.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adra import Finding, Orchestrator, Severity, load_settings  # noqa: E402


@pytest.fixture
def orch(tmp_path):
    return Orchestrator(load_settings(provider="mock", runs_dir=tmp_path))


def test_stale_base_pr_is_escalated(orch):
    state, rec = orch.run("pr_eval", {
        "source_branch": "task/x", "target_branch": "develop",
        "git_fixture": {"behind": 12, "deletions": ["nb.py"],
                        "renames": ["R\ta.yml\ta.yml.t"]},
        "bundle_fixture": {"stdout": "Error", "returncode": 1},
    })
    assert state.decision == "escalate"
    verdict = state.critic_history[-1]
    # blocking is a list of typed Finding objects, not strings
    assert verdict.blocking and all(isinstance(f, Finding) for f in verdict.blocking)
    assert all(f.severity in (Severity.BLOCKER, Severity.MAJOR) for f in verdict.blocking)
    blocking = " ".join(verdict.messages).lower()
    assert "merge-base" in blocking or "behind" in blocking
    assert "delet" in blocking
    assert "bundle" in blocking


def test_language_and_leak_blocked(orch):
    state, _ = orch.run("code_review", {
        "diff": "+ # Co-Authored-By: Claude\n+ def calcular():  # esta funcion no se toca\n",
    })
    assert state.decision == "escalate"
    blocking = " ".join(state.critic_history[-1].messages).lower()
    assert "session leak" in blocking or "leak" in blocking
    assert "english" in blocking or "spanish" in blocking


def test_clean_experiment_accepted(orch):
    state, _ = orch.run("experiment", {
        "slug": "exp", "probes": [{"sql": "SELECT 1", "fixture": {"rows": [["1"]]}}],
    })
    assert state.decision == "accepted"


def test_provenance_written(orch, tmp_path):
    _, rec = orch.run("improve", {"context": "remove dead test"})
    assert (tmp_path / f"{rec.run_id}.json").exists()
    assert rec.steps and rec.steps[0]["kind"] == "plan"


def test_tool_returns_typed_toolresult():
    from adra import ToolResult
    from adra.tools import git_tools
    r = git_tools.merge_base_health(None, "x",
                                    fixture={"behind": 3, "deletions": ["a.py"], "renames": []})
    assert isinstance(r, ToolResult)
    assert not r.clean and r.blocking            # a deletion is a blocking finding
    assert all(isinstance(f, Finding) for f in r.findings)
    assert r.data["behind"] == 3


def test_grounding_values_are_typed(orch):
    from adra import ToolResult
    state, _ = orch.run("pr_eval", {
        "git_fixture": {"behind": 0, "deletions": [], "renames": []}})
    assert state.grounding and all(isinstance(v, ToolResult) for v in state.grounding.values())


def test_test_discovery_flags_suffix_file():
    from adra.tools import discovery_tools
    r = discovery_tools.check_test_discovery(
        ["databricks/orders/py_aux_test.py", "databricks/tests/test_ok.py"])
    assert not r.clean
    assert any("py_aux_test.py" in f.evidence for f in r.findings)
    assert all(f.severity in (Severity.BLOCKER, Severity.MAJOR) for f in r.findings)


def test_decide_produces_route_analysis(orch):
    state, _ = orch.run("decide", {"problem": "raise cadence", "routes": ["a", "b"]})
    assert state.decision in ("accepted", "escalate")
    assert "route_analysis.md" in state.artifacts


def test_rubric_drives_critic(orch):
    from adra import rubric
    state, _ = orch.run("pr_eval", {"git_fixture": {"behind": 0, "deletions": [], "renames": []}})
    tried = state.critic_history[-1].attacks_tried
    assert tried == [it.id for it in rubric.for_skill("pr_eval")]
    assert "stale_merge_base" in tried


def test_standards_suite_present():
    from adra.utils import load_standard
    assert "Northwind" in load_standard("README.md")
    assert "ADR-0001" in load_standard("adr/ADR-0001-deterministic-grounding.md")
    assert load_standard("ci-standards.md")


def test_judge_swap_average_position_consistency():
    from adra.judge import compare
    from adra.llm import MockChatModel
    res = compare(MockChatModel(), "artifact A", "artifact B", reference="ref",
                  swap_average=True)
    assert "averaged" in res and res["position_consistent"] in (True, False)


def test_multi_provider_factory_and_per_role_routing():
    import pytest as _pytest

    from adra import load_settings
    from adra.config import PROVIDERS, default_model
    from adra.llm import MockChatModel, ModelRouter, make_chat_model, make_chat_model_for
    # offline default builds the deterministic mock with no key
    assert isinstance(make_chat_model(load_settings(provider="mock")), MockChatModel)
    # the registry covers paid + local providers
    for p in ("openai", "groq", "xai", "mistral", "deepseek", "ollama"):
        assert p in PROVIDERS
    assert default_model("groq") and default_model("anthropic")
    # an unknown provider is a clear, immediate error (no network / no openai import)
    with _pytest.raises(RuntimeError):
        make_chat_model_for("nope", "x", 0.0, 16)
    # per-role routing: one run can target a different model per role
    s = load_settings(provider="mock",
                      role_models={"critic": "mock:m-critic", "generate": "mock:m-gen"})
    assert s.role("critic") == ("mock", "m-critic")
    assert s.role("plan") == ("mock", s.model)            # falls back to the default
    assert isinstance(ModelRouter(s).for_role("critic"), MockChatModel)
