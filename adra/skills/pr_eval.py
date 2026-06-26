"""pr_eval skill.

The first grounding step is *merge-base health* (the destructive failure mode in
our history), then ``bundle validate`` and a language scan. The model produces a
verdict and a structured PR body; any deterministic blocker forces
``changes-requested`` regardless of the model.
"""

from __future__ import annotations

from typing import Any

from adra.config import Settings
from adra.llm import invoke_text
from adra.nodes import Node
from adra.skills.base import Skill, load_prompt
from adra.state import RunState, ToolResult
from adra.tools import bundle_tools, git_tools, lang_tools
from adra.utils import parse_json

PR_BODY_TEMPLATE = """## Objective
{objective}

## Changes
{changes}

## What is NOT touched
{not_touched}

## Validation
{validation}

## Risks / mitigations
{risks}

## Test plan
{test_plan}

## Work Item
{work_item}
"""


class PrEvalSkill(Skill):
    name = "pr_eval"

    def plan(self, model, settings, state):
        return {"skill": self.name, "tools": ["merge_base_health", "bundle_validate", "lang_scan"]}

    def ground(self, settings: Settings, state: RunState) -> dict[str, ToolResult]:
        i = state.intake
        return {
            "merge_base_health": git_tools.merge_base_health(
                settings.repo_path, source=i.get("source_branch", "HEAD"),
                target=i.get("target_branch", "develop"), fixture=i.get("git_fixture")),
            "bundle_validate": bundle_tools.bundle_validate(
                settings.repo_path, target=i.get("bundle_target", "dev"),
                allow_external=settings.allow_external_calls, fixture=i.get("bundle_fixture")),
            "lang_scan": lang_tools.scan_language(i.get("pr_body_draft", "")),
        }

    def generate(self, model, settings, state) -> dict[str, Any]:
        system = load_prompt("pr_eval") or "You are a PR reviewer for a data platform."
        user = (
            "Evaluate this PR using the grounding. Return JSON {verdict: "
            "'approve'|'changes-requested', summary, objective, changes, not_touched, "
            "validation, risks, test_plan, work_item}.\n\n"
            f"GROUNDING: {state.to_dict()['grounding']}\nINTAKE: {state.intake}")
        data = parse_json(invoke_text(model, system, user, node=Node.PR_EVAL))
        # A deterministic blocker forces changes-requested, regardless of the model.
        has_blocker = any(r.blocking for r in state.grounding.values())
        data["verdict"] = "changes-requested" if has_blocker else data.get("verdict", "changes-requested")
        return data

    def finalize(self, settings, state: RunState) -> dict[str, str]:
        d = state.draft or {}
        i = state.intake
        body = PR_BODY_TEMPLATE.format(
            objective=d.get("objective", i.get("objective", "")),
            changes=d.get("changes", ""), not_touched=d.get("not_touched", ""),
            validation=d.get("validation", ""), risks=d.get("risks", ""),
            test_plan=d.get("test_plan", ""), work_item=d.get("work_item", i.get("work_item", "")))
        verdict = (f"# PR evaluation: {d.get('verdict','?')} ({state.decision})\n\n"
                   f"{d.get('summary','')}\n")
        return {"pr_verdict.md": verdict, "pr_body.md": body}
