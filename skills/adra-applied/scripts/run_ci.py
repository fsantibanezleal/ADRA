"""run_ci.py — reproduce the EXACT CI command (ADR-0001/0004).

Runs the repository's exact CI command (never an approximation) and parses the
test count, the "no data collected" signal, and the coverage percentage.

Usage:
    python run_ci.py --repo <path> --command "<exact CI command>" --allow-external
    python run_ci.py --command "..." --fixture fixture.json          # offline replay

Fixture shape: {"returncode": 0, "stdout": "Ran 12 tests ... TOTAL 100 20 83%"}

Blocking (BLOCKER): non-zero exit, "Ran 0 tests", or "No data was collected".
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402

_RAN = re.compile(r"Ran\s+(\d+)\s+tests?", re.IGNORECASE)
_NODATA = re.compile(r"No data was collected", re.IGNORECASE)
_COV = re.compile(r"TOTAL\s+\d+\s+\d+\s+(\d+)%")


def analyze(returncode: int, output: str, min_coverage: int | None) -> tuple[list, dict]:
    findings: list = []
    tests = int(_RAN.search(output).group(1)) if _RAN.search(output) else None
    no_data = bool(_NODATA.search(output))
    cov = int(_COV.search(output).group(1)) if _COV.search(output) else None
    data = {"returncode": returncode, "tests": tests, "coverage": cov, "no_data": no_data}

    if returncode not in (0, None):
        findings.append(c.finding(
            c.BLOCKER, "ci_failed", f"CI command exited non-zero ({returncode})",
            source="run_ci"))
    if tests == 0 or no_data:
        findings.append(c.finding(
            c.BLOCKER, "zero_tests_no_data",
            "no tests were collected ('Ran 0 tests' / 'No data was collected')",
            evidence=f"tests={tests} no_data={no_data}", source="run_ci"))
    if min_coverage is not None and cov is not None and cov < min_coverage:
        findings.append(c.finding(
            c.MAJOR, "coverage_below_gate",
            f"coverage {cov}% is below the gate of {min_coverage}%", source="run_ci"))
    return findings, data


def main() -> int:
    ap = argparse.ArgumentParser(description="Reproduce the exact CI command.")
    ap.add_argument("--repo")
    ap.add_argument("--command", required=True, help="the exact CI command string")
    ap.add_argument("--min-coverage", type=int, default=None)
    ap.add_argument("--allow-external", action="store_true")
    ap.add_argument("--fixture")
    args = ap.parse_args()

    fx = c.load_fixture(args.fixture)
    if fx is not None:
        findings, data = analyze(int(fx.get("returncode", 0)),
                                 fx.get("stdout", ""), args.min_coverage)
        data["source"] = "fixture"
        return c.emit(c.result("run_ci", True, findings, data))

    if not args.allow_external:
        return c.emit(c.result(
            "run_ci", False, reason=c.dry_run_note(False),
            data={"command": args.command}))

    run = c.run_cmd(args.command, cwd=args.repo, timeout=900, shell=True)
    output = (run["stdout"] or "") + (run["stderr"] or "")
    findings, data = analyze(run["returncode"], output, args.min_coverage)
    data["command"] = args.command
    return c.emit(c.result("run_ci", True, findings, data))


if __name__ == "__main__":
    raise SystemExit(main())
