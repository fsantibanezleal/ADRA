"""Real Databricks data connector (``databricks-sdk``, Statement Execution API).

A read-only :class:`~adra.connectors.base.DataProvider` for warehouse probes used by the
experiment skill. It runs SQL through the **SQL Statement Execution API** on a SQL
warehouse via the official ``databricks-sdk`` (ADR-0008 / dossier §2: one unified auth for
the control plane + SQL; we skip ``databricks-sql-connector``).

Read-only is the default posture: the engine never issues writes here, and the
recommendation is to back it with a SELECT-only service principal at the grant/RBAC level
(deterministic, not enforced in agent logic — dossier §4). As a defence-in-depth in-loop
guard we also reject obviously-mutating statements before they leave the process.

Degrades cleanly: if the SDK is missing, or credentials/warehouse are absent, a clear
:class:`RuntimeError` is raised at construction / probe time rather than failing opaque.
Requires the ``databricks`` extra: ``pip install adra[databricks]``.

Auth: the SDK's unified config resolves host + token from the environment / a profile
(``DATABRICKS_HOST`` + ``DATABRICKS_TOKEN``, OAuth, Azure CLI, etc.); the warehouse id
comes from ``DATABRICKS_WAREHOUSE_ID`` or is passed in.
"""

from __future__ import annotations

import os

# Statements that mutate state — rejected in-loop as a second line of defence behind a
# SELECT-only grant. The connector is for read-only experiment probes only.
_FORBIDDEN_PREFIXES = (
    "insert", "update", "delete", "merge", "drop", "truncate", "alter",
    "create", "replace", "grant", "revoke", "copy", "call", "use",
)


class DatabricksData:
    """A Databricks SQL warehouse as a read-only ``DataProvider``."""

    name = "databricks"

    def __init__(
        self,
        warehouse_id: str | None = None,
        *,
        host: str | None = None,
        token: str | None = None,
        catalog: str | None = None,
        schema: str | None = None,
        wait_timeout: str = "30s",
        allow_external: bool = False,
    ) -> None:
        try:
            from databricks.sdk import WorkspaceClient
        except ImportError as exc:  # pragma: no cover - only when extra missing
            raise RuntimeError(
                "the Databricks connector requires `pip install adra[databricks]` (databricks-sdk)."
            ) from exc
        self.allow_external = allow_external
        self.catalog = catalog
        self.schema = schema
        self.wait_timeout = wait_timeout
        self.warehouse_id = warehouse_id or os.environ.get("DATABRICKS_WAREHOUSE_ID")
        if not self.warehouse_id:
            raise RuntimeError(
                "Databricks needs a SQL warehouse id (pass warehouse_id= or set "
                "DATABRICKS_WAREHOUSE_ID)."
            )
        kwargs = {}
        if host or os.environ.get("DATABRICKS_HOST"):
            kwargs["host"] = host or os.environ["DATABRICKS_HOST"]
        if token or os.environ.get("DATABRICKS_TOKEN"):
            kwargs["token"] = token or os.environ["DATABRICKS_TOKEN"]
        try:
            # The SDK resolves the rest of the auth chain (profile, OAuth, Azure CLI…).
            self._client = WorkspaceClient(**kwargs)
        except Exception as exc:  # pragma: no cover - depends on ambient creds
            raise RuntimeError(
                f"Databricks auth failed (no usable credentials): {exc}"
            ) from exc

    def _guard(self, sql: str) -> None:
        head = sql.lstrip().lower()
        if any(head.startswith(p) for p in _FORBIDDEN_PREFIXES) and not self.allow_external:
            raise PermissionError(
                "write/DDL blocked: the Databricks connector is read-only (SELECT probes). "
                "Back it with a SELECT-only grant; set allow_external=True only for a "
                "deliberate, human-confirmed exception."
            )

    def run_sql(self, sql: str) -> dict:
        """Execute a read-only SQL probe and return ``{"columns": [...], "rows": [[...]]}``."""
        self._guard(sql)
        try:
            from databricks.sdk.service.sql import StatementState
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("databricks-sdk too old; need StatementState.") from exc
        resp = self._client.statement_execution.execute_statement(
            statement=sql,
            warehouse_id=self.warehouse_id,
            catalog=self.catalog,
            schema=self.schema,
            wait_timeout=self.wait_timeout,
        )
        status = getattr(resp, "status", None)
        state = getattr(status, "state", None)
        if state == StatementState.FAILED:
            err = getattr(status, "error", None)
            msg = getattr(err, "message", "") if err else ""
            raise RuntimeError(f"Databricks statement failed: {msg}")
        return _to_table(resp)


def _to_table(resp) -> dict:
    """Map a Databricks ``StatementResponse`` to the engine's column/row dict."""
    manifest = getattr(resp, "manifest", None)
    schema = getattr(manifest, "schema", None) if manifest else None
    cols = [c.name for c in getattr(schema, "columns", []) or []] if schema else []
    result = getattr(resp, "result", None)
    rows = list(getattr(result, "data_array", None) or []) if result else []
    return {"columns": cols, "rows": [list(r) for r in rows]}
