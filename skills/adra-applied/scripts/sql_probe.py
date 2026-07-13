"""sql_probe.py — run a SQL statement on the shared warehouse (ADR-0005).

Uses the Databricks SQL Statement Execution API through the databricks CLI. This
is the only sanctioned way to run an experiment probe: the shared serverless SQL
warehouse, never a fresh interactive cluster. Read-oriented; gathering rows is
evidence, so it carries no findings unless the statement itself failed.

Usage:
    python sql_probe.py --profile <dev|prod> --warehouse-id <id> \
        --statement "SELECT ..." [--catalog c --schema s] --allow-external
    python sql_probe.py --fixture fixture.json                     # offline replay

Fixture shape: {"state": "SUCCEEDED", "columns": ["a"], "rows": [[1]]}
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402


def parse_response(text: str) -> dict:
    try:
        payload = json.loads(text or "{}")
    except ValueError:
        return {"state": "UNKNOWN", "columns": [], "rows": [], "error": text.strip()[:400]}
    status = payload.get("status", {}) or {}
    manifest = payload.get("manifest", {}) or {}
    cols = [col.get("name") for col in
            (manifest.get("schema", {}) or {}).get("columns", []) or []]
    rows = (payload.get("result", {}) or {}).get("data_array", []) or []
    return {
        "state": status.get("state", "UNKNOWN"),
        "error": (status.get("error", {}) or {}).get("message", ""),
        "columns": cols,
        "rows": rows,
    }


def build(parsed: dict) -> tuple[list, dict]:
    findings: list = []
    if parsed.get("state") == "FAILED":
        findings.append(c.finding(
            c.MAJOR, "probe_failed",
            f"SQL statement failed: {parsed.get('error', '')[:200]}",
            source="sql_probe"))
    data = {"state": parsed.get("state"), "columns": parsed.get("columns", []),
            "rows": parsed.get("rows", []), "row_count": len(parsed.get("rows", []))}
    return findings, data


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a SQL probe on the shared warehouse.")
    ap.add_argument("--profile", default="dev")
    ap.add_argument("--warehouse-id")
    ap.add_argument("--statement", required=True)
    ap.add_argument("--catalog")
    ap.add_argument("--schema")
    ap.add_argument("--allow-external", action="store_true")
    ap.add_argument("--fixture")
    args = ap.parse_args()

    fx = c.load_fixture(args.fixture)
    if fx is not None:
        findings, data = build(fx)
        data["source"] = "fixture"
        return c.emit(c.result("sql_probe", True, findings, data))

    if not args.allow_external:
        return c.emit(c.result("sql_probe", False, reason=c.dry_run_note(False),
                               data={"profile": args.profile}))
    if not args.warehouse_id:
        return c.emit(c.result("sql_probe", False,
                               reason="a --warehouse-id is required (see preflight.py)"))

    payload = {"warehouse_id": args.warehouse_id, "statement": args.statement,
               "wait_timeout": "30s", "format": "JSON_ARRAY"}
    if args.catalog:
        payload["catalog"] = args.catalog
    if args.schema:
        payload["schema"] = args.schema
    run = c.run_cmd(["databricks", "api", "post", "/api/2.0/sql/statements",
                     "--profile", args.profile, "--json", json.dumps(payload)],
                    timeout=180)
    if run["returncode"] != 0 and not run["stdout"].strip():
        return c.emit(c.result("sql_probe", False,
                               reason=f"databricks call failed: {run['stderr'].strip()[:300]}",
                               data={"profile": args.profile}))
    findings, data = build(parse_response(run["stdout"]))
    data["profile"] = args.profile
    return c.emit(c.result("sql_probe", True, findings, data))


if __name__ == "__main__":
    raise SystemExit(main())
