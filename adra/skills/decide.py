"""decide skill — route analysis ("paths to follow").

Given a problem and candidate routes, produces a decision artifact: a routes table
with honest trade-offs (effort, blast radius, reversibility, risk, precedent), a
recommendation, and an explicit human-owned decision. Mirrors how routes are laid
out in the wips before a human/owner chooses (ADR-0008, CASE-2024-061).
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


class DecideSkill(Skill):
    name = "decide"

    def plan(self, model, settings, state):
        return {"skill": self.name, "tools": ["lang_scan"]}

    def ground(self, settings: Settings, state: RunState) -> dict[str, ToolResult]:
        return {"lang_scan": lang_tools.scan_language(state.intake.get("problem", ""))}

    def generate(self, model, settings, state) -> dict[str, Any]:
        system = load_prompt("decide") or "You produce route analyses with trade-offs."
        user = (
            "Produce the route analysis. Return JSON {problem, routes: [{name, summary, "
            "effort, blast_radius, reversibility, risk, precedent}], recommendation, "
            "rationale, open_question, decision_owner}. Prefer the smallest reversible "
            "route justified against a precedent; the decision stays human-owned.\n\n"
            f"PROBLEM: {state.intake.get('problem','')}\n"
            f"CANDIDATE ROUTES: {state.intake.get('routes', [])}")
        data = parse_json(invoke_text(model, system, user, node=Node.DECIDE))
        data.setdefault("decision_owner", "human")
        return data

    def finalize(self, settings, state: RunState) -> dict[str, str]:
        d = state.draft or {}
        rows = ["| Route | Effort | Blast radius | Reversibility | Risk | Precedent |",
                "|---|---|---|---|---|---|"]
        for r in d.get("routes", []):
            rows.append(f"| {r.get('name')} | {r.get('effort')} | {r.get('blast_radius')} "
                        f"| {r.get('reversibility')} | {r.get('risk')} | {r.get('precedent')} |")
        md = (f"# Route analysis ({state.decision})\n\n"
              f"## Problem\n{d.get('problem', state.intake.get('problem',''))}\n\n"
              f"## Routes\n\n" + "\n".join(rows) + "\n\n"
              f"## Recommendation\n{d.get('recommendation','')}\n\n"
              f"## Rationale\n{d.get('rationale','')}\n\n"
              f"## Decision\nOwner: **{d.get('decision_owner','human')}** — open question: "
              f"{d.get('open_question','')}\n")
        return {"route_analysis.md": md}
