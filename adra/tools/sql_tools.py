"""Databricks SQL warehouse probe (deterministic).

The first-choice tool for validation experiments: an ad-hoc SQL statement against
the shared SQL warehouse (no interactive cluster). Real mode shells out to the
``databricks`` CLI; ``fixture`` mode replays a captured ``data_array`` so
experiments are reproducible offline.

Encodes the access-troubleshooting contract: never conclude "no access" without
checking profile / warehouse / grants first (the :data:`PREFLIGHT` checklist).
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from adra.state import ToolResult

PREFLIGHT = [
    "profile matches the catalog env (prod for prod_*, dev for dev_*)",
    "`databricks current-user me --profile <p>` returns the expected user",
    "warehouse_id is valid for the profile and is RUNNING",
    "the catalog exists in the workspace (SHOW CATALOGS)",
    "the schema exists (SHOW SCHEMAS IN <catalog>)",
    "the table exists (SHOW TABLES IN <catalog>.<schema>)",
    "current_user is a member of the granting security group (is_member)",
    "if the warehouse runs as a service principal, the SP has the grant",
]


def sql_probe(
    statement: str,
    warehouse_id: str = "",
    profile: str = "dev",
    allow_external: bool = False,
    fixture: dict[str, Any] | None = None,
) -> ToolResult:
    """Run a SQL statement on the warehouse, or replay a fixture result.

    Args:
        statement: The SQL to execute.
        warehouse_id: Target SQL warehouse id (required for real execution).
        profile: Databricks CLI profile (``prod`` / ``dev``).
        allow_external: Gate; the CLI only runs when True (default dry-run).
        fixture: ``{"rows": [...]}`` to replay offline.

    Returns:
        A :class:`~adra.state.ToolResult` with the returned rows in ``data["rows"]``.
        Carries no findings (a probe gathers evidence; the skill/critic interpret it).
    """
    if fixture is not None:
        rows = list(fixture.get("rows", []))
        return ToolResult(tool="sql_probe",
                          data={"statement": statement, "profile": profile, "rows": rows,
                                "row_count": len(rows)})
    if not (allow_external and warehouse_id):
        return ToolResult(tool="sql_probe", ran=False,
                          reason="external calls disabled or no warehouse_id (dry-run)",
                          data={"statement": statement, "preflight": PREFLIGHT})

    payload = json.dumps({"warehouse_id": warehouse_id, "statement": statement,
                          "wait_timeout": "30s", "format": "JSON_ARRAY"})
    proc = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements", "--profile", profile,
         "--json", payload], capture_output=True, text=True, timeout=120)
    try:
        rows = json.loads(proc.stdout or "{}").get("result", {}).get("data_array", [])
    except json.JSONDecodeError:
        rows = []
    return ToolResult(tool="sql_probe",
                      data={"statement": statement, "profile": profile, "rows": rows,
                            "row_count": len(rows), "preflight": PREFLIGHT})
