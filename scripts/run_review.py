"""CLI: review a diff/patch file.

Usage:
  python scripts/run_review.py path/to/change.diff [--ci "exact ci command"] [--external]

Uses Anthropic Claude when ANTHROPIC_API_KEY is set, otherwise the offline mock.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from adra import Orchestrator, load_settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="ADRA code review")
    ap.add_argument("diff", help="path to a unified diff / patch file")
    ap.add_argument("--ci", default=None, help="exact CI command to reproduce")
    ap.add_argument("--external", action="store_true", help="allow running the CI command")
    ap.add_argument("--repo", default=None, help="repo path for tools")
    args = ap.parse_args()

    settings = load_settings(runs_dir=HERE.parent / "runs",
                             allow_external_calls=args.external)
    if args.repo:
        settings.repo_path = Path(args.repo)
    orch = Orchestrator(settings)
    state, rec = orch.run("code_review", {
        "diff": Path(args.diff).read_text(encoding="utf-8"),
        "ci_command": args.ci,
    })
    print(rec.summary())
    print("\n--- review.md ---\n")
    print(state.artifacts.get("review.md", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
