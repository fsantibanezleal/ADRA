"""Test-discoverability check (deterministic).

Encodes ADR-0004 / CASE-2024-047: ``unittest discover`` collects files matching the
``test*.py`` **prefix**; a ``*_test.py`` **suffix** file is never collected and is
dead code. This catches, mechanically, a defect that otherwise only surfaces as a
confusing "No data was collected" coverage failure.
"""

from __future__ import annotations

import fnmatch
import re
from typing import Iterable

from adra import rubric
from adra.state import ToolResult

_ADDED_PATH = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


def added_paths(diff: str) -> list[str]:
    """Extract added/modified file paths from a unified diff."""
    return [p for p in _ADDED_PATH.findall(diff or "") if p and p != "/dev/null"]


def check_test_discovery(paths: Iterable[str], pattern: str = "test*.py") -> ToolResult:
    """Flag test files that the CI discovery pattern will never collect.

    Args:
        paths: Candidate file paths (e.g. added paths from a diff).
        pattern: The discovery glob (default ``test*.py``).

    Returns:
        A :class:`~adra.state.ToolResult`; a MAJOR finding per uncollectable test file.
    """
    flagged = []
    for p in paths:
        base = p.rsplit("/", 1)[-1]
        looks_like_test = "test" in base.lower() and base.endswith(".py")
        if looks_like_test and not fnmatch.fnmatch(base, pattern):
            flagged.append(p)
    findings = [rubric.get("test_discoverability").to_finding(evidence=p, source="test_discovery")
                for p in flagged]
    return ToolResult(tool="test_discovery", findings=findings,
                      data={"pattern": pattern, "flagged": flagged, "checked": list(paths)})
