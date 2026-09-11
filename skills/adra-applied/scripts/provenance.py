"""provenance.py · append-only run record (ADR-0006).

Documentation is generated from this record, not from memory. The record captures
the plan, the grounding evidence, the drafts, the critic rounds, and the decision.
Secrets never go in it.

Usage:
    # start a run (prints the run_id)
    python provenance.py --new --skill review [--runs-dir runs]
    # append an event
    python provenance.py --run-id <id> --event ground --kind tool --payload '{"tool":"..."}'
    # finalize
    python provenance.py --run-id <id> --decision accepted
    # show
    python provenance.py --run-id <id> --show
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402


def runs_dir(arg: str | None) -> str:
    d = arg or os.environ.get("ADRA_RUNS_DIR") or "runs"
    os.makedirs(d, exist_ok=True)
    return d


def path_for(d: str, run_id: str) -> str:
    return os.path.join(d, f"{run_id}.json")


def load(d: str, run_id: str) -> dict | None:
    p = path_for(d, run_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(d: str, record: dict) -> str:
    p = path_for(d, record["run_id"])
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=True, indent=2)
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="Append-only provenance run record.")
    ap.add_argument("--new", action="store_true")
    ap.add_argument("--skill")
    ap.add_argument("--run-id")
    ap.add_argument("--event")
    ap.add_argument("--kind", default="event")
    ap.add_argument("--payload")
    ap.add_argument("--decision")
    ap.add_argument("--artifact-name")
    ap.add_argument("--artifact-file")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--runs-dir")
    args = ap.parse_args()

    d = runs_dir(args.runs_dir)

    if args.new:
        run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        record = {"run_id": run_id, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                  "skill": args.skill or "", "runtime": "agent-harness",
                  "steps": [], "final_decision": "pending", "artifacts": {}}
        p = save(d, record)
        return c.emit(c.result("provenance", True, [],
                               {"run_id": run_id, "path": p, "action": "created"}))

    if not args.run_id:
        return c.emit(c.result("provenance", False, reason="--run-id required (or --new)"))
    record = load(d, args.run_id)
    if record is None:
        return c.emit(c.result("provenance", False,
                               reason=f"run {args.run_id} not found in {d}"))

    if args.show:
        return c.emit(c.result("provenance", True, [], record))

    payload = c.load_fixture(args.payload) if args.payload else None
    if args.event:
        record["steps"].append({"t": time.strftime("%H:%M:%S"), "node": args.event,
                                "kind": args.kind, "payload": payload})
    if args.artifact_name and args.artifact_file and os.path.exists(args.artifact_file):
        with open(args.artifact_file, "r", encoding="utf-8") as fh:
            record["artifacts"][args.artifact_name] = fh.read()
    if args.decision:
        record["final_decision"] = args.decision

    p = save(d, record)
    summary = (f"run {record['run_id']} | skill={record['skill']} "
               f"| decision={record['final_decision']} | steps={len(record['steps'])}")
    return c.emit(c.result("provenance", True, [],
                           {"run_id": record["run_id"], "path": p, "summary": summary}))


if __name__ == "__main__":
    raise SystemExit(main())
