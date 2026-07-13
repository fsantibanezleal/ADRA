"""Shared helpers for the ADRA Applied deterministic tools.

Every tool script prints a single JSON object shaped like the engine's ToolResult
(tool, ran, findings, data, reason) and exits non-zero when a blocking finding is
present. Tools are read-only / dry-run unless ``--allow-external`` is passed, and
accept ``--fixture`` to replay a captured result offline (no network, no secrets).

Standard library only, so the scripts are portable with no install step.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

BLOCKER = "BLOCKER"
MAJOR = "MAJOR"
MINOR = "MINOR"
NIT = "NIT"

_BLOCKING = {BLOCKER, MAJOR}


def finding(severity: str, category: str, message: str, **extra: Any) -> dict:
    """Build a typed finding. ``severity`` is one of BLOCKER/MAJOR/MINOR/NIT."""
    item = {"severity": severity, "category": category, "message": message}
    item.update({k: v for k, v in extra.items() if v not in (None, "", [])})
    return item


def is_blocking(f: dict) -> bool:
    return f.get("severity") in _BLOCKING


def result(tool: str, ran: bool = True, findings: list | None = None,
           data: dict | None = None, reason: str = "") -> dict:
    return {
        "tool": tool,
        "ran": ran,
        "findings": findings or [],
        "data": data or {},
        "reason": reason,
    }


def run_cmd(args, cwd: str | None = None, timeout: int = 120,
            shell: bool = False) -> dict:
    """Run a command, capturing stdout+stderr and the return code.

    Never raises on a non-zero exit; the caller inspects ``returncode``. Returns a
    dict {cmd, returncode, stdout, stderr}. On a missing executable or timeout the
    returncode is set to a sentinel and the error goes to ``stderr``.
    """
    try:
        proc = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True,
            timeout=timeout, shell=shell,
        )
        return {
            "cmd": args if isinstance(args, str) else " ".join(args),
            "returncode": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
        }
    except FileNotFoundError as exc:
        return {"cmd": args, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {"cmd": args, "returncode": 124, "stdout": "", "stderr": f"timeout: {exc}"}


def load_fixture(value: str | None) -> Any:
    """Load a fixture: a path to a JSON file, or an inline JSON string, or None."""
    if not value:
        return None
    if os.path.exists(value):
        with open(value, "r", encoding="utf-8") as fh:
            return json.load(fh)
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return None


def emit(res: dict) -> int:
    """Print the result as JSON and return the process exit code.

    Exit 0 when clean, 1 when any finding is blocking, 2 when the tool could not
    run (ran is False and a reason was given but no findings).
    """
    print(json.dumps(res, ensure_ascii=True, indent=2))
    if any(is_blocking(f) for f in res.get("findings", [])):
        return 1
    if not res.get("ran", True) and not res.get("findings"):
        return 2
    return 0


def dry_run_note(allow_external: bool) -> str:
    return "" if allow_external else (
        "dry-run: pass --allow-external to run this against a live system"
    )
