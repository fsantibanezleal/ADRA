"""End-to-end offline demo (no API key required).

Runs every skill through the adversarial loop with bundled fixtures for the
fictional client (Northwind Data Platform) and prints each run record. Shows that
the deterministic floor alone produces a real adversarial outcome: destructive /
non-compliant artifacts are blocked and escalated, while clean ones are accepted.

Run:  python scripts/demo_offline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from adra import Orchestrator, load_settings  # noqa: E402

RUNS = HERE.parent / "runs"


def banner(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def show(state, rec) -> None:
    print(rec.summary())
    for m in state.critic_history[-1].messages:
        print("   BLOCK:", m)


def main() -> int:
    orch = Orchestrator(load_settings(provider="mock", runs_dir=RUNS))

    # 1) PR eval on a STALE-BASE branch (the destructive failure mode). Expect block.
    banner("pr_eval - stale-base PR (must be blocked + escalated)")
    state, rec = orch.run("pr_eval", {
        "source_branch": "task/NDP-1487/current-state-table",
        "target_branch": "main",
        "objective": "Split current-state table creation into its own parallel task.",
        "work_item": "NDP-1487",
        "git_fixture": {  # 12 commits behind; deletes a notebook; renames resources
            "behind": 12,
            "deletions": ["refined/nb-priority-coverage.py"],
            "renames": ["R100\tresources/bundle.resources.schemas.yml\tresources/bundle.resources.schemas.yml.t"],
        },
        "bundle_fixture": {"stdout": "Error: schema resource not found", "returncode": 1},
        "pr_body_draft": "Objective: split task. Validation: looks fine.",
    })
    show(state, rec)

    # 2) code_review: Spanish + AI-leak + a *_test.py CI never collects + 0 tests. Block.
    banner("code_review - language/leak + uncollectable test + no coverage data (must block)")
    state, rec = orch.run("code_review", {
        "diff": ("+++ b/databricks/orders/fulfilment/py_aux_functions_test.py\n"
                 "+ # Co-Authored-By: Claude\n"
                 "+ def calcular_salida():  # esta funcion no se toca\n"),
        "ci_command": 'python -m coverage run -m unittest discover -s databricks -p "test*.py"',
        "ci_fixture": {"stdout": "Ran 0 tests in 0.000s\nNo data was collected", "returncode": 1},
    })
    show(state, rec)

    # 3) experiment with a clean probe result (fixture). Expect accepted.
    banner("experiment - clean probe (expected accepted)")
    state, rec = orch.run("experiment", {
        "slug": "2024-09-tag-coverage-check",
        "probes": [{"sql": "SELECT count(*) FROM prod_orders_fulfilment.refined.order_stream",
                    "profile": "prod", "fixture": {"rows": [["130000000"]]}}],
    })
    show(state, rec)

    # 4) improve + document (expected accepted).
    banner("improve + document (expected accepted)")
    _, rec = orch.run("improve", {"context": "Remove a redundant test file CI never collects."})
    print(rec.summary())
    _, rec2 = orch.run("document", {
        "doc_type": "pr", "pr": "1487", "title": "Estado-despacho parallel task",
        "status": "Merged", "summary": "Split the current-state table into its own task."})  # noqa: E501
    print(rec2.summary())

    # 5) decide - route analysis (paths to follow, human-owned decision).
    banner("decide - route analysis (expected accepted)")
    state, rec = orch.run("decide", {
        "problem": "Raise the catalog refresh trigger cadence.",
        "routes": ["edit the shared ndp-ci trigger template", "change cadence in the catalog repo only"]})
    print(rec.summary())
    print("   ", (state.artifacts.get("route_analysis.md", "").splitlines() or [""])[0])

    print(f"\nRun records written under: {RUNS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
