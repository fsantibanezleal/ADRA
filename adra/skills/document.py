"""document skill.

Turns a run record (or any change description) into house documentation: a wiki
experiment page, a ``PR-XXXXX`` change-control page, or a ``Methodology_history``
milestone. Documentation is generated from provenance, so the technical,
operational and functional history all trace back to one auditable run.
"""

from __future__ import annotations

from typing import Any

from adra.config import Settings
from adra.llm import invoke_text
from adra.nodes import Node
from adra.skills.base import Skill, load_prompt
from adra.state import RunState, ToolResult
from adra.tools import lang_tools

PR_DOC_TEMPLATE = """# PR-{pr} - {title} ({status})

[[_TOC_]]

## Summary
{summary}

## Links
- PR: {pr_url}
- Key files (commit-pinned): {files}

## Metadata
- Status: {status}
- Source: `{source}`  Target: `{target}`
- Head: `{head}`  Base: `{base}`
- Merge date: {date}

## Code changes (evidence)
{evidence}

## Outputs / contracts impacted
{contracts}

## Validation checklist
- [ ] Unit tests green (exact CI command)
- [ ] CI/CD pipeline OK
- [ ] Docs updated (Data-Contracts / Operation)
"""


class DocumentSkill(Skill):
    name = "document"

    def plan(self, model, settings, state):
        return {"skill": self.name, "doc_type": state.intake.get("doc_type", "pr")}

    def ground(self, settings: Settings, state: RunState) -> dict[str, ToolResult]:
        # Grounding for documentation = the source-of-truth gap table + a leak scan
        # of the material we are about to write.
        gaps = state.intake.get("doc_gaps", [])
        return {
            "doc_gap": ToolResult(tool="doc_gap", data={"gaps": gaps}),
            "lang_scan": lang_tools.scan_language(state.intake.get("summary", "")),
        }

    def generate(self, model, settings, state) -> Any:
        doc_type = state.intake.get("doc_type", "pr")
        if doc_type == "pr":
            i = state.intake
            return PR_DOC_TEMPLATE.format(
                pr=i.get("pr", "XXXXX"), title=i.get("title", ""), status=i.get("status", "Merged"),
                summary=i.get("summary", ""), pr_url=i.get("pr_url", ""), files=i.get("files", ""),
                source=i.get("source", "task/..."), target=i.get("target", "develop"),
                head=i.get("head", ""), base=i.get("base", ""), date=i.get("date", ""),
                evidence=i.get("evidence", ""), contracts=i.get("contracts", ""))
        system = load_prompt("document") or "You write technical documentation."
        user = (f"Write a {doc_type} page from this record. House style, English, "
                f"third person, no AI-session leak.\n\nRECORD: {state.intake}")
        return invoke_text(model, system, user, node=Node.DOCUMENT)

    def finalize(self, settings, state: RunState) -> dict[str, str]:
        doc_type = state.intake.get("doc_type", "pr")
        name = {"pr": f"PR-{state.intake.get('pr','XXXXX')}.md",
                "experiment": f"{state.intake.get('slug','experiment')}.md",
                "lesson": f"{state.intake.get('slug','lesson')}.md"}.get(doc_type, "doc.md")
        return {name: str(state.draft)}
