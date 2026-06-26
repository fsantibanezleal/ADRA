"""Deterministic tools (no LLM).

Every tool returns a :class:`~adra.state.ToolResult` — typed ``Finding`` objects
plus raw ``data`` evidence — used for two things at once:

1. *grounding* the LLM (findings the model may not contradict), and
2. *evidence* in the provenance record (the second-method proof).

Tools degrade gracefully when an external CLI (git, databricks) is unavailable or
when external calls are disabled (``ran=False`` with a ``reason``), so the package
always runs. Each tool also accepts an injected ``fixture`` so the offline path
exercises the exact same decision logic.
"""

from adra.tools import (bundle_tools, ci_tools, discovery_tools, git_tools,
                        lang_tools, sql_tools)

__all__ = ["git_tools", "ci_tools", "bundle_tools", "lang_tools", "sql_tools",
           "discovery_tools"]
