"""Small Azure health / data connector (``azure-identity`` + optional ``azure-monitor-query``).

A read-only :class:`~adra.connectors.base.DataProvider` for cloud-health probes used by the
experiment / maintenance skills (ADR-0008 / dossier §2): a single least-privilege
``DefaultAzureCredential`` drives Log Analytics **KQL** queries via ``azure-monitor-query``
(the GA availability signal; ``azure-mgmt-resourcehealth`` can layer on later).

The :meth:`run_sql` method takes **KQL** (not ANSI SQL) and returns the engine's
``{"columns": [...], "rows": [[...]]}`` shape, so it composes with the experiment skill's
probe runner. A ``workspace_id`` (Log Analytics workspace GUID) scopes the query.

Degrades cleanly: missing ``azure-identity`` → clear error at construction; missing
``azure-monitor-query`` → clear error only when a KQL probe is actually run; missing /
unusable credentials → a clear error from the credential chain at query time, never an
opaque failure. Requires the ``azure`` extra: ``pip install adra[azure]``.
"""

from __future__ import annotations

import os
from datetime import timedelta


class AzureMonitorData:
    """Azure Log Analytics (KQL) as a read-only ``DataProvider``."""

    name = "azure"

    def __init__(
        self,
        workspace_id: str | None = None,
        *,
        credential=None,
        timespan_hours: int = 24,
    ) -> None:
        try:
            from azure.identity import DefaultAzureCredential
        except ImportError as exc:  # pragma: no cover - only when extra missing
            raise RuntimeError(
                "the Azure connector requires `pip install adra[azure]` "
                "(azure-identity, azure-monitor-query)."
            ) from exc
        self.workspace_id = workspace_id or os.environ.get("AZURE_LOG_ANALYTICS_WORKSPACE_ID")
        if not self.workspace_id:
            raise RuntimeError(
                "Azure needs a Log Analytics workspace id (pass workspace_id= or set "
                "AZURE_LOG_ANALYTICS_WORKSPACE_ID)."
            )
        self.timespan = timedelta(hours=timespan_hours)
        # Constructing the credential is cheap and does not hit the network; the actual
        # token is acquired lazily on the first query (so we degrade at query time if the
        # chain can't resolve a usable identity).
        self._credential = credential or DefaultAzureCredential()
        self._client = None  # built lazily so a missing monitor-query extra is query-time

    def _logs_client(self):
        if self._client is None:
            try:
                from azure.monitor.query import LogsQueryClient
            except ImportError as exc:  # pragma: no cover - only when extra missing
                raise RuntimeError(
                    "Azure KQL probes need `azure-monitor-query` "
                    "(`pip install adra[azure]`)."
                ) from exc
            self._client = LogsQueryClient(self._credential)
        return self._client

    def run_sql(self, kql: str) -> dict:
        """Run a **KQL** probe against the workspace; returns ``{"columns", "rows"}``.

        Named ``run_sql`` to satisfy the ``DataProvider`` Protocol; the dialect is KQL.
        """
        from azure.monitor.query import LogsQueryStatus

        client = self._logs_client()
        resp = client.query_workspace(
            workspace_id=self.workspace_id, query=kql, timespan=self.timespan
        )
        if resp.status == LogsQueryStatus.FAILURE:  # pragma: no cover - needs live creds
            raise RuntimeError(f"Azure KQL query failed: {getattr(resp, 'partial_error', resp)}")
        tables = list(getattr(resp, "tables", None) or [])
        if not tables:
            return {"columns": [], "rows": []}
        t = tables[0]
        cols = list(getattr(t, "columns", []) or [])
        rows = [list(r) for r in (getattr(t, "rows", []) or [])]
        return {"columns": cols, "rows": rows}
