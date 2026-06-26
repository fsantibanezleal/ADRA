"""Databricks Asset Bundle validation (deterministic).

"Validate with the build's own tool" — run ``databricks bundle validate -t <env>``
and surface its verdict, rather than eyeballing the YAML. Read-only by default.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from adra.state import Severity, ToolResult, finding


def bundle_validate(
    repo: Path | None,
    target: str = "dev",
    allow_external: bool = False,
    fixture: dict[str, Any] | None = None,
) -> ToolResult:
    """Run ``databricks bundle validate`` (or replay ``fixture``).

    Args:
        repo: The bundle repo root.
        target: The bundle target/environment to validate.
        allow_external: Gate; the CLI only runs when True (default dry-run).
        fixture: ``{"stdout": str, "returncode": int}`` to replay offline.

    Returns:
        A :class:`~adra.state.ToolResult`; BLOCKER unless validation returns OK.
    """
    if fixture is not None:
        stdout, returncode = fixture.get("stdout", ""), int(fixture.get("returncode", 0))
    elif allow_external and repo is not None:
        proc = subprocess.run(["databricks", "bundle", "validate", "-t", target],
                              cwd=str(repo), capture_output=True, text=True, timeout=300)
        stdout, returncode = (proc.stdout or "") + (proc.stderr or ""), proc.returncode
    else:
        return ToolResult(tool="bundle_validate", ran=False,
                          reason="external calls disabled (dry-run); pass allow_external=True",
                          data={"target": target})

    ok = returncode == 0 and "Validation OK" in stdout
    findings = []
    if not ok:
        findings.append(finding(
            Severity.BLOCKER, "bundle",
            f"`databricks bundle validate -t {target}` did not return Validation OK.",
            evidence=stdout[-400:], source="bundle_validate"))
    return ToolResult(tool="bundle_validate", findings=findings,
                      data={"target": target, "returncode": returncode, "ok": ok})
