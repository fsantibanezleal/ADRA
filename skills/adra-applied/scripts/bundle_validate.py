"""bundle_validate.py — Databricks Asset Bundle validation (ADR-0003).

Runs `databricks bundle validate -t <env>` from the repo root. The validate is
read-only, but reaching a live workspace requires --allow-external.

Usage:
    python bundle_validate.py --repo <path> --target <env> --allow-external
    python bundle_validate.py --fixture fixture.json          # offline replay

Fixture shape: {"returncode": 0, "stdout": "Validation OK!"}

Blocking (BLOCKER): validate did not print "Validation OK".
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402


def analyze(returncode: int, output: str) -> list:
    if returncode == 0 and "Validation OK" in output:
        return []
    return [c.finding(
        c.BLOCKER, "bundle_validate",
        "databricks bundle validate did not pass ('Validation OK!' not found)",
        evidence=(output.strip()[-400:] or f"exit {returncode}"), source="bundle_validate")]


def main() -> int:
    ap = argparse.ArgumentParser(description="databricks bundle validate verdict.")
    ap.add_argument("--repo")
    ap.add_argument("--target", default="dev")
    ap.add_argument("--allow-external", action="store_true")
    ap.add_argument("--fixture")
    args = ap.parse_args()

    fx = c.load_fixture(args.fixture)
    if fx is not None:
        out = fx.get("stdout", "")
        return c.emit(c.result("bundle_validate", True,
                               analyze(int(fx.get("returncode", 0)), out),
                               {"target": args.target, "source": "fixture"}))

    if not args.allow_external:
        return c.emit(c.result("bundle_validate", False, reason=c.dry_run_note(False),
                               data={"target": args.target}))
    if not args.repo:
        return c.emit(c.result("bundle_validate", False, reason="no --repo"))

    run = c.run_cmd(["databricks", "bundle", "validate", "-t", args.target],
                    cwd=args.repo, timeout=300)
    output = (run["stdout"] or "") + (run["stderr"] or "")
    return c.emit(c.result("bundle_validate", True, analyze(run["returncode"], output),
                           {"target": args.target, "returncode": run["returncode"]}))


if __name__ == "__main__":
    raise SystemExit(main())
