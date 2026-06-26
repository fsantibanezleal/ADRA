"""Base skill contract.

A skill is five small steps the orchestrator calls in order::

    plan -> ground -> generate -> (revise per critic round) -> finalize

Only ``ground`` is LLM-free (deterministic tools, returning ``ToolResult`` objects).
``plan`` / ``generate`` / ``revise`` use the chat model. Defaults are provided so a
concrete skill overrides only what it needs.
"""

from __future__ import annotations

from typing import Any

from adra.config import Settings
from adra.llm import ChatModel
from adra.state import CriticVerdict, RunState, ToolResult
from adra.utils import load_prompt  # re-exported so skill modules import it from here

__all__ = ["Skill", "load_prompt"]


class Skill:
    """Base class for a capability. Subclasses set ``name`` and override steps."""

    name: str = "base"

    def plan(self, model: ChatModel, settings: Settings, state: RunState) -> dict[str, Any]:
        """Classify the request and declare the tools this skill will ground on."""
        return {"skill": self.name}

    def ground(self, settings: Settings, state: RunState) -> dict[str, ToolResult]:
        """Run deterministic tools. Returns a name -> :class:`ToolResult` mapping."""
        return {}

    def generate(self, model: ChatModel, settings: Settings, state: RunState) -> Any:
        """Produce the draft artifact (str or structured)."""
        raise NotImplementedError

    def revise(self, model: ChatModel, settings: Settings, state: RunState,
               verdict: CriticVerdict) -> Any:
        """Revise the draft given the critic's blocking findings.

        The default records the unresolved blockers on the draft, which keeps the
        loop honest (it cannot mask a blocker) and routes to escalation when the
        offline mock cannot actually fix the issue.
        """
        notes = "\n".join(f"- UNRESOLVED: {m}" for m in verdict.messages)
        if isinstance(state.draft, dict):
            return {**state.draft, "_critic_unresolved": verdict.messages}
        return f"{state.draft}\n\n<!-- critic round {state.rounds} -->\n{notes}"

    def finalize(self, settings: Settings, state: RunState) -> dict[str, str]:
        """Render the accepted/escalated draft into named artifacts."""
        return {"artifact": str(state.draft)}
