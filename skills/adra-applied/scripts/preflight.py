"""preflight.py · the 8-point catalog access checklist (ADR-0005 / CASE-2024-052).

Run this before ever concluding "no access." It walks the eight checks as real
commands and reports the first one that fails (the likely cause). Only if all
runnable checks pass and access still fails should "no access" be reported, with
every output attached.

Usage:
    python preflight.py --profile <dev|prod> --warehouse-id <id> \
        --catalog <c> --schema <s> --table <t> --group <granting-group> --allow-external
    python preflight.py --fixture fixture.json                     # offline replay

Fixture shape: {"steps": [{"n": 1, "name": "...", "ok": true, "detail": "..."}]}

Blocking: none by itself; a failed step is reported as MAJOR so the caller stops
guessing and fixes the real cause.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402


def _stmt(profile: str, warehouse_id: str, sql: str) -> list:
    """Run a statement, return its rows (flattened) or []."""
    payload = {"warehouse_id": warehouse_id, "statement": sql,
               "wait_timeout": "30s", "format": "JSON_ARRAY"}
    run = c.run_cmd(["databricks", "api", "post", "/api/2.0/sql/statements",
                     "--profile", profile, "--json", json.dumps(payload)], timeout=120)
    try:
        payload = json.loads(run["stdout"] or "{}")
    except ValueError:
        return []
    return (payload.get("result", {}) or {}).get("data_array", []) or []


def _flat(rows: list) -> list:
    return [str(cell) for row in rows for cell in (row if isinstance(row, list) else [row])]


def run_live(a) -> list:
    steps: list = []

    def step(n, name, ok, detail=""):
        steps.append({"n": n, "name": name, "ok": bool(ok), "detail": detail})
        return ok

    # 1: profile/env heuristic
    env_ok = True
    detail = ""
    if a.catalog:
        if a.catalog.startswith("prod_") and a.profile != a.prod_profile:
            env_ok, detail = False, f"prod_* catalog needs the '{a.prod_profile}' profile"
        elif a.catalog.startswith("dev_") and a.profile == a.prod_profile:
            env_ok, detail = False, f"dev_* catalog should not use the '{a.prod_profile}' profile"
    step(1, "profile matches catalog env", env_ok, detail)

    # 2: current-user me
    me = c.run_cmd(["databricks", "current-user", "me", "--profile", a.profile])
    step(2, "current-user me", me["returncode"] == 0, me["stdout"].strip()[:200] or me["stderr"].strip()[:200])

    # 3: warehouse RUNNING
    if a.warehouse_id:
        wh = c.run_cmd(["databricks", "warehouses", "get", a.warehouse_id, "--profile", a.profile])
        running = '"RUNNING"' in wh["stdout"] or "RUNNING" in wh["stdout"]
        step(3, "warehouse RUNNING", running, "" if running else "start the warehouse")
    else:
        step(3, "warehouse RUNNING", False, "no --warehouse-id")

    # 4-6 require a warehouse
    if a.warehouse_id:
        if a.catalog:
            cats = _flat(_stmt(a.profile, a.warehouse_id, "SHOW CATALOGS"))
            step(4, "catalog exists", a.catalog in cats, f"catalogs seen: {len(cats)}")
            if a.schema:
                schs = _flat(_stmt(a.profile, a.warehouse_id, f"SHOW SCHEMAS IN {a.catalog}"))
                step(5, "schema exists", a.schema in schs, f"schemas seen: {len(schs)}")
                if a.table:
                    tbls = _flat(_stmt(a.profile, a.warehouse_id,
                                       f"SHOW TABLES IN {a.catalog}.{a.schema}"))
                    step(6, "table exists", a.table in tbls, f"tables seen: {len(tbls)}")
        if a.group:
            member = _flat(_stmt(a.profile, a.warehouse_id,
                                 f"SELECT is_member('{a.group}')"))
            ok = any(v.lower() in ("true", "1") for v in member)
            step(7, "current_user is a member of the granting group", ok,
                 f"is_member('{a.group}')={member}")

    # 8: SP grant; cannot be auto-verified
    step(8, "service-principal grant (if warehouse runs as SP)", True,
         "manual: if the warehouse runs as a service principal, confirm the SP has the grant")
    return steps


def build(steps: list) -> tuple[list, dict]:
    failed = [s for s in steps if not s.get("ok")]
    findings = []
    for s in failed:
        findings.append(c.finding(
            c.MAJOR, "access_preflight_failed",
            f"preflight step {s['n']} failed: {s['name']} · {s.get('detail', '')}",
            source="preflight"))
    data = {"steps": steps, "passed": len(steps) - len(failed), "total": len(steps),
            "all_passed": not failed}
    return findings, data


def main() -> int:
    ap = argparse.ArgumentParser(description="8-point catalog access preflight.")
    ap.add_argument("--profile", default="dev")
    ap.add_argument("--prod-profile", default="prod")
    ap.add_argument("--warehouse-id")
    ap.add_argument("--catalog")
    ap.add_argument("--schema")
    ap.add_argument("--table")
    ap.add_argument("--group")
    ap.add_argument("--allow-external", action="store_true")
    ap.add_argument("--fixture")
    args = ap.parse_args()

    fx = c.load_fixture(args.fixture)
    if fx is not None:
        findings, data = build(fx.get("steps", []))
        data["source"] = "fixture"
        return c.emit(c.result("preflight", True, findings, data))

    if not args.allow_external:
        return c.emit(c.result("preflight", False, reason=c.dry_run_note(False)))

    findings, data = build(run_live(args))
    return c.emit(c.result("preflight", True, findings, data))


if __name__ == "__main__":
    raise SystemExit(main())
