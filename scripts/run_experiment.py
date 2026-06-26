"""CLI: run a validation experiment from a JSON spec.

Usage:
  python scripts/run_experiment.py spec.json [--external]

spec.json: {"slug": "...", "warehouse_id": "...",
            "probes": [{"sql": "...", "profile": "prod"}]}
With --external the probes hit the real SQL warehouse; otherwise they dry-run
(or replay a per-probe "fixture").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from adra import Orchestrator, load_settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="ADRA validation experiment")
    ap.add_argument("spec", help="path to experiment spec JSON")
    ap.add_argument("--external", action="store_true", help="hit the SQL warehouse")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    settings = load_settings(runs_dir=HERE.parent / "runs",
                             allow_external_calls=args.external)
    orch = Orchestrator(settings)
    state, rec = orch.run("experiment", spec)
    print(rec.summary())
    for name, content in state.artifacts.items():
        print(f"\n--- {name} ---\n{content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
