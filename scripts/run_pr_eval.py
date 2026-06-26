"""CLI: evaluate a PR / branch.

Usage:
  python scripts/run_pr_eval.py --repo PATH --source BRANCH [--target develop] [--external]

Runs the merge-base health check, bundle validate (with --external), language scan,
then the adversarial loop. Prints the verdict + the generated PR body.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from adra import Orchestrator, load_settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="ADRA PR evaluation")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--source", required=True, help="source branch")
    ap.add_argument("--target", default="develop")
    ap.add_argument("--objective", default="")
    ap.add_argument("--work-item", default="")
    ap.add_argument("--external", action="store_true",
                    help="allow databricks bundle validate to run")
    args = ap.parse_args()

    settings = load_settings(runs_dir=HERE.parent / "runs",
                             repo_path=Path(args.repo),
                             allow_external_calls=args.external)
    orch = Orchestrator(settings)
    state, rec = orch.run("pr_eval", {
        "source_branch": args.source,
        "target_branch": args.target,
        "objective": args.objective,
        "work_item": args.work_item,
    })
    print(rec.summary())
    print("\n--- pr_verdict.md ---\n")
    print(state.artifacts.get("pr_verdict.md", ""))
    print("\n--- pr_body.md ---\n")
    print(state.artifacts.get("pr_body.md", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
