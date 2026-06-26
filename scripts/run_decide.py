"""CLI: produce a route analysis ("paths to follow") for a problem.

Usage:
  python scripts/run_decide.py "problem statement" [--route R1 --route R2 ...]

Uses a real provider when configured, otherwise the offline mock.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from adra import Orchestrator, load_settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="ADRA route analysis")
    ap.add_argument("problem", help="the problem / decision to analyze")
    ap.add_argument("--route", action="append", default=[], help="a candidate route (repeatable)")
    args = ap.parse_args()

    settings = load_settings(runs_dir=HERE.parent / "runs")
    orch = Orchestrator(settings)
    state, rec = orch.run("decide", {"problem": args.problem, "routes": args.route})
    print(rec.summary())
    print("\n--- route_analysis.md ---\n")
    print(state.artifacts.get("route_analysis.md", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
