"""CI command runner (deterministic).

Embodies the rule "reproduce the *exact* command the system uses, not an
approximation". The agent runs the project's real CI command and parses its result
rather than asserting the build is green.

Real mode runs the command (only when external calls are allowed); ``fixture`` mode
replays a captured result so the offline path exercises the same parsing.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from adra.state import Severity, ToolResult, finding

_TESTS_RE = re.compile(r"Ran (\d+) tests?")
_NO_DATA_RE = re.compile(r"No data was collected", re.IGNORECASE)
_COVERAGE_RE = re.compile(r"TOTAL\s+\d+\s+\d+\s+(\d+)%")


def run_ci_command(
    command: str,
    repo: Path | None = None,
    allow_external: bool = False,
    fixture: dict[str, Any] | None = None,
) -> ToolResult:
    """Run ``command`` (or replay ``fixture``) and judge the test / coverage outcome.

    Args:
        command: The exact CI command to reproduce.
        repo: Working directory for the command.
        allow_external: Gate; the command only runs when True (default dry-run).
        fixture: ``{"stdout": str, "returncode": int}`` to replay offline.

    Returns:
        A :class:`~adra.state.ToolResult`. BLOCKER on non-zero exit, 0 tests
        collected, or coverage reporting no data.
    """
    if fixture is not None:
        stdout, returncode = fixture.get("stdout", ""), int(fixture.get("returncode", 0))
    elif allow_external and repo is not None:
        proc = subprocess.run(command, shell=True, cwd=str(repo),
                              capture_output=True, text=True, timeout=600)
        stdout, returncode = (proc.stdout or "") + (proc.stderr or ""), proc.returncode
    else:
        return ToolResult(tool="ci_command", ran=False,
                          reason="external calls disabled (dry-run); pass allow_external=True",
                          data={"command": command})

    tests = int(m.group(1)) if (m := _TESTS_RE.search(stdout)) else None
    no_data = bool(_NO_DATA_RE.search(stdout))
    coverage = int(m.group(1)) if (m := _COVERAGE_RE.search(stdout)) else None

    findings = []
    if returncode != 0:
        findings.append(finding(Severity.BLOCKER, "ci",
                                f"CI command exited {returncode}; not green.",
                                evidence=f"command={command!r}", source="ci_command"))
    if tests == 0:
        findings.append(finding(
            Severity.BLOCKER, "ci",
            "0 tests collected; coverage will report no data. Add a discoverable unit "
            "test (`test*.py`) over importable, non-notebook code.",
            evidence="Ran 0 tests", source="ci_command"))
    if no_data:
        findings.append(finding(
            Severity.BLOCKER, "coverage",
            "Coverage collected no data; the measured code is not imported by any "
            "discoverable test.", evidence="No data was collected", source="ci_command"))
    return ToolResult(tool="ci_command", findings=findings,
                      data={"command": command, "returncode": returncode,
                            "tests": tests, "coverage_pct": coverage, "no_data": no_data})
