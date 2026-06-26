"""improve skill.

Proposes a *minimum-functional* change: keep only what advances the result, prune
filler even when it came from a team standard, and require validation with the
exact CI command. Output is a rationale + the minimal change (a diff sketch).
"""

from __future__ import annotations

from typing import Any

from adra.config import Settings
from adra.llm import invoke_text
from adra.nodes import Node
from adra.skills.base import Skill, load_prompt
from adra.state import RunState, ToolResult
from adra.tools import lang_tools
from adra.utils import parse_json


class ImproveSkill(Skill):
    name = "improve"

    def plan(self, model, settings, state):
        return {"skill": self.name, "tools": ["lang_scan"]}

    def ground(self, settings: Settings, state: RunState) -> dict[str, ToolResult]:
        return {"lang_scan": lang_tools.scan_language(state.intake.get("context", ""))}

    def generate(self, model, settings, state) -> dict[str, Any]:
        system = load_prompt("improve") or "You propose minimum-functional improvements."
        user = (
            "Propose the minimum-functional improvement. Return JSON {proposal, rationale, "
            "minimal_change, dead_code_removed: [str], validation_command}. Justify every "
            "kept element; drop anything that does not change a CI result.\n\n"
            f"INTAKE: {state.intake}\nGROUNDING: {state.to_dict()['grounding']}")
        return parse_json(invoke_text(model, system, user, node=Node.IMPROVE))

    def finalize(self, settings, state: RunState) -> dict[str, str]:
        d = state.draft or {}
        removed = "\n".join(f"- {x}" for x in d.get("dead_code_removed", []))
        md = (f"# Improvement proposal ({state.decision})\n\n"
              f"## Proposal\n{d.get('proposal','')}\n\n"
              f"## Rationale (minimum functional)\n{d.get('rationale','')}\n\n"
              f"## Minimal change\n{d.get('minimal_change','')}\n\n"
              f"## Dead code removed\n{removed}\n\n"
              f"## Validation command\n`{d.get('validation_command','')}`\n")
        return {"proposal.md": md}
