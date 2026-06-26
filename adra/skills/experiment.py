"""experiment skill.

Produces a hypothesis-driven validation experiment in our house format: a
hypothesis table (probability / impact / probe), standalone probes, and a
synthesis. SQL probes run against the shared warehouse (or replay a fixture);
nothing is concluded that the probe data does not support.
"""

from __future__ import annotations

from typing import Any

from adra.config import Settings
from adra.llm import invoke_text
from adra.nodes import Node
from adra.skills.base import Skill, load_prompt
from adra.state import RunState, ToolResult
from adra.tools import sql_tools
from adra.utils import parse_json


class ExperimentSkill(Skill):
    name = "experiment"

    def plan(self, model, settings, state):
        return {"skill": self.name, "tools": ["sql_probe"]}

    def ground(self, settings: Settings, state: RunState) -> dict[str, ToolResult]:
        results: dict[str, ToolResult] = {}
        for i, probe in enumerate(state.intake.get("probes", []), 1):
            results[f"probe_{i:02d}"] = sql_tools.sql_probe(
                probe.get("sql", ""), warehouse_id=state.intake.get("warehouse_id", ""),
                profile=probe.get("profile", "prod"),
                allow_external=settings.allow_external_calls, fixture=probe.get("fixture"))
        return results

    def generate(self, model, settings, state) -> dict[str, Any]:
        system = load_prompt("experiment") or "You design validation experiments."
        user = (
            "Design the experiment. Return JSON {title, hypotheses: [{id, hypothesis, "
            "probability, impact, probe}], design, synthesis}. Conclude only what the "
            "probe rows support; flag anything that needs live data.\n\n"
            f"INTAKE: {state.intake}\nPROBE_RESULTS: {state.to_dict()['grounding']}")
        return parse_json(invoke_text(model, system, user, node=Node.EXPERIMENT))

    def finalize(self, settings, state: RunState) -> dict[str, str]:
        d = state.draft or {}
        slug = state.intake.get("slug", "experiment")
        rows = ["| # | Hypothesis | Probability | Impact | Probe |", "|---|---|---|---|---|"]
        for h in d.get("hypotheses", []):
            rows.append(f"| {h.get('id')} | {h.get('hypothesis')} | {h.get('probability')} "
                        f"| {h.get('impact')} | {h.get('probe')} |")
        top = (f"# {d.get('title', slug)}\n\n> Experiment ({state.decision}).\n\n"
               "## Hypotheses\n\n" + "\n".join(rows) + f"\n\n## Design\n\n{d.get('design','')}\n")
        synthesis = (f"# v0X-synthesis\n\n{d.get('synthesis','')}\n\n## Evidence\n\n"
                     f"- {len(state.grounding)} probe(s); "
                     f"{sum(r.data.get('row_count', 0) for r in state.grounding.values())} total rows\n")
        return {f"{slug}.md": top, f"{slug}__v0X-synthesis.md": synthesis}
