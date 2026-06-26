"""Git inspection (deterministic).

The headline check is *merge-base health*: the single failure mode that produced a
destructive PR in our history (a branch built on a stale ``develop`` deleted a
notebook and dropped bundle resources). We detect a stale base and the dangerous
operations a stale-base diff tends to carry (file deletions, resource renames).

Works on a real repo when ``git`` is available, and accepts an injected ``fixture``
so the offline path exercises the exact same decision logic.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from adra.state import Severity, ToolResult, finding


def _git(repo: Path, *args: str) -> str:
    """Run a git command in ``repo`` and return stdout (empty on failure)."""
    try:
        out = subprocess.run(["git", "-C", str(repo), *args],
                             capture_output=True, text=True, timeout=30)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def merge_base_health(
    repo: Path | None,
    source: str,
    target: str = "develop",
    fixture: dict[str, Any] | None = None,
) -> ToolResult:
    """Assess whether ``source`` is based on a fresh ``target``.

    Args:
        repo: Path to the git repo, or None to skip (returns ``ran=False``).
        source: The source branch / ref under review.
        target: The integration branch to compare against (default ``develop``).
        fixture: When provided, short-circuits git and supplies ``behind`` (int),
            ``deletions`` (list[str]) and ``renames`` (list[str]) — used offline.

    Returns:
        A :class:`~adra.state.ToolResult`. MAJOR when the branch is behind; BLOCKER
        for file deletions and for resource renames that would drop a bundle file.
    """
    if fixture is not None:
        behind = int(fixture.get("behind", 0))
        deletions = list(fixture.get("deletions", []))
        renames = list(fixture.get("renames", []))
        source_ref, target_ref = source, target
    elif repo is not None:
        target_ref, source_ref = f"origin/{target}", source
        base = _git(repo, "merge-base", source_ref, target_ref)
        behind = int(_git(repo, "rev-list", "--count", f"{base}..{target_ref}") or "0")
        diff = _git(repo, "diff", "--name-status", f"{base}..{source_ref}")
        deletions = [ln.split("\t", 1)[-1] for ln in diff.splitlines() if ln.startswith("D")]
        renames = [ln for ln in diff.splitlines() if ln.startswith("R")]
    else:
        return ToolResult(tool="merge_base_health", ran=False,
                          reason="no repo path provided")

    findings = []
    if behind > 0:
        findings.append(finding(
            Severity.MAJOR, "merge-base",
            f"Source branch is {behind} commit(s) behind {target_ref}; rebase or "
            "recreate it on the current base before review.",
            evidence=f"behind={behind}", source="merge_base_health"))
    if deletions:
        findings.append(finding(
            Severity.BLOCKER, "destructive",
            "Diff deletes files; confirm each deletion is intended (stale-base diffs "
            "silently remove notebooks / resources).",
            evidence=f"deletions={deletions}", source="merge_base_health"))
    suspicious = [r for r in renames if ".yml" in r and (".yml.t" in r or "->" in r)]
    if suspicious:
        findings.append(finding(
            Severity.BLOCKER, "bundle",
            "Resource files renamed away from `.yml` (e.g. `.yml.t`) would drop them "
            "from the bundle.",
            evidence=f"renames={suspicious}", source="merge_base_health"))
    return ToolResult(
        tool="merge_base_health", findings=findings,
        data={"source": source_ref, "target": target_ref, "behind": behind,
              "stale": behind > 0, "deletions": deletions, "renames": renames})
