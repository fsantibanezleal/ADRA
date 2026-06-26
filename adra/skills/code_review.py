"""code_review skill.

Deterministic-first: run the language / leak scan over the diff and (when enabled)
the project's exact CI command, then let the model add semantic findings on top of
that grounded floor. Output is a structured findings report.
"""

from __future__ import annotations

from typing import Any

from adra.config import Settings
from adra.llm import ChatModel, invoke_text
from adra.nodes import Node
from adra.skills.base import Skill, load_prompt
from adra.state import RunState, ToolResult
from adra.tools import ci_tools, discovery_tools, lang_tools
from adra.utils import parse_json


class CodeReviewSkill(Skill):
    name = "code_review"

    def plan(self, model, settings, state):
        return {"skill": self.name, "tools": ["lang_scan", "test_discovery", "ci_command"]}

    def ground(self, settings: Settings, state: RunState) -> dict[str, ToolResult]:
        diff = state.intake.get("diff", "")
        grounding = {
            "lang_scan": lang_tools.scan_language(diff),
            "test_discovery": discovery_tools.check_test_discovery(
                discovery_tools.added_paths(diff)),
        }
        if (ci_cmd := state.intake.get("ci_command")):
            grounding["ci_command"] = ci_tools.run_ci_command(
                ci_cmd, repo=settings.repo_path,
                allow_external=settings.allow_external_calls,
                fixture=state.intake.get("ci_fixture"))
        return grounding

    def generate(self, model: ChatModel, settings, state) -> dict[str, Any]:
        system = load_prompt("code_review") or "You are a senior code reviewer."
        user = (
            "Review this diff. Return JSON {summary: str, semantic_findings: "
            "[{severity, category, message, location}]}. Only add findings the "
            "deterministic tools cannot settle.\n\n"
            f"GROUNDING: {state.to_dict()['grounding']}\n\nDIFF:\n{state.intake.get('diff','')}")
        data = parse_json(invoke_text(model, system, user, node=Node.CODE_REVIEW))
        return {
            "summary": data.get("summary", ""),
            "deterministic_findings": [f.to_dict() for f in state.grounding_findings()],
            "semantic_findings": data.get("semantic_findings", []),
        }

    def finalize(self, settings, state: RunState) -> dict[str, str]:
        d = state.draft or {}
        lines = [f"# Code review ({state.decision})", "", d.get("summary", ""),
                 "", "## Deterministic findings (tool-grounded)"]
        for f in d.get("deterministic_findings", []):
            lines.append(f"- **{f.get('severity')}** [{f.get('category')}] "
                         f"{f.get('message')} _(evidence: {f.get('evidence','')})_")
        lines.append("\n## Semantic findings (model)")
        for f in d.get("semantic_findings", []):
            lines.append(f"- **{f.get('severity')}** [{f.get('category')}] "
                         f"{f.get('message')} @ {f.get('location','')}")
        return {"review.md": "\n".join(lines)}
