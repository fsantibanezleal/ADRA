"""Offline tests for the real platform connectors (Azure DevOps · Databricks · Azure).

No live credentials, no network: Azure DevOps is exercised against an ``httpx.MockTransport``
serving recorded REST 7.1 fixtures; Databricks/Azure are exercised for construction,
read-only gating, and the factory wiring (with ``importorskip`` where the SDK is genuinely
required). These assert the contract: real adapters parse correctly, writes are gated by
``allow_external``, and the factory routes provider strings to the right class.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

httpx = pytest.importorskip("httpx")

from adra.connectors import (  # noqa: E402
    PullRequest, get_data_provider, get_repo_provider,
)


# --- Azure DevOps (recorded REST 7.1 fixtures over httpx.MockTransport) -----------------

_ADO_PRS = {
    "value": [
        {
            "pullRequestId": 42, "title": "feat: widen route schema",
            "sourceRefName": "refs/heads/feature/route", "targetRefName": "refs/heads/main",
            "createdBy": {"displayName": "Dev One"}, "description": "adds eta_seconds",
            "url": "https://dev.azure.com/org/proj/_apis/git/repositories/repo/pullRequests/42",
        }
    ]
}
_ADO_PR = _ADO_PRS["value"][0]
_ADO_ITERATIONS = {"value": [{"id": 1}, {"id": 2}]}
_ADO_CHANGES = {
    "changeEntries": [
        {"changeType": "edit", "item": {"path": "/telemetry/models/route.py"}},
        {"changeType": "add", "item": {"path": "/telemetry/tests/test_route.py"}},
    ]
}
_ADO_REPOS = {
    "value": [
        {"id": "r1", "name": "repo", "defaultBranch": "refs/heads/main",
         "webUrl": "https://dev.azure.com/org/proj/_git/repo"}
    ]
}


def _ado_handler(write_calls: list):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path.endswith("/threads"):
            write_calls.append(request)
            return httpx.Response(200, json={"id": 777})
        if path.endswith("/git/repositories"):
            return httpx.Response(200, json=_ADO_REPOS)
        if path.endswith("/pullrequests"):
            return httpx.Response(200, json=_ADO_PRS)
        if "/iterations/" in path and path.endswith("/changes"):
            return httpx.Response(200, json=_ADO_CHANGES)
        if path.endswith("/iterations"):
            return httpx.Response(200, json=_ADO_ITERATIONS)
        if "/pullrequests/" in path:
            return httpx.Response(200, json=_ADO_PR)
        return httpx.Response(404, json={"message": f"unhandled {path}"})
    return handler


@pytest.fixture
def ado_repo():
    """An AzureDevOpsRepo whose client is rewired to a recorded mock transport."""
    write_calls: list = []
    repo = get_repo_provider({
        "provider": "azure_devops", "organization": "org", "project": "proj",
        "repo": "repo", "token": "fake-pat",
    })
    repo._client = httpx.Client(
        base_url="https://dev.azure.com",
        headers=repo._client.headers,
        transport=httpx.MockTransport(_ado_handler(write_calls)),
    )
    repo._write_calls = write_calls
    return repo


def test_ado_factory_and_auth_header():
    repo = get_repo_provider({
        "provider": "azure_devops", "organization": "org", "project": "proj",
        "repo": "repo", "token": "fake-pat",
    })
    assert repo.name == "azure_devops"
    # PAT → Basic auth with an empty username; the token is base64'd, never plain.
    auth = repo._client.headers.get("Authorization", "")
    assert auth.startswith("Basic ") and "fake-pat" not in auth


def test_ado_bearer_auth_header():
    repo = get_repo_provider({
        "provider": "ado", "organization": "org", "project": "proj",
        "repo": "repo", "token": "tok", "bearer": True,
    })
    assert repo._client.headers.get("Authorization") == "Bearer tok"


def test_ado_list_repositories(ado_repo):
    repos = ado_repo.list_repositories()
    assert repos and repos[0]["name"] == "repo"
    assert repos[0]["default_branch"] == "refs/heads/main"


def test_ado_list_pull_requests(ado_repo):
    prs = ado_repo.list_pull_requests()
    assert len(prs) == 1 and isinstance(prs[0], PullRequest)
    pr = prs[0]
    assert pr.number == 42 and pr.target_branch == "main" and pr.source_branch == "feature/route"
    assert pr.author == "Dev One"


def test_ado_get_pull_request_with_changes(ado_repo):
    pr = ado_repo.get_pull_request(42)
    assert pr.number == 42
    # the latest iteration's changes ground the path list + a diff-shaped summary
    assert "telemetry/models/route.py" in pr.files
    assert "telemetry/tests/test_route.py" in pr.files
    assert "route.py" in pr.diff and "add" in pr.diff


def test_ado_comment_gated_by_default(ado_repo):
    with pytest.raises(PermissionError):
        ado_repo.comment_on_pull_request(42, "blocking finding")
    assert not ado_repo._write_calls  # nothing left the process


def test_ado_comment_allowed_when_external(ado_repo):
    ado_repo.allow_external = True
    url = ado_repo.comment_on_pull_request(42, "blocking finding")
    assert "threads/777" in url
    assert len(ado_repo._write_calls) == 1


# --- Databricks (construction / gating / factory; SDK-required path skipped if absent) --

def test_databricks_factory_unknown_provider_errors():
    with pytest.raises(ValueError):
        get_data_provider({"provider": "nope"})


def test_databricks_missing_warehouse_id_is_clear_error():
    pytest.importorskip("databricks.sdk")
    with pytest.raises(RuntimeError, match="warehouse id"):
        get_data_provider({"provider": "databricks"})


def test_databricks_degrades_without_sdk():
    """Without the SDK installed, construction raises a clear 'pip install' error."""
    try:
        import databricks.sdk  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match=r"pip install adra\[databricks\]"):
            get_data_provider({"provider": "databricks", "warehouse_id": "w1"})
    else:
        pytest.skip("databricks-sdk installed; degrade path covered by the import-guard")


def test_databricks_read_only_guard_rejects_writes():
    """The in-loop SELECT-only guard rejects mutating SQL without touching the network."""
    pytest.importorskip("databricks.sdk")
    from adra.connectors.databricks import DatabricksData
    db = DatabricksData.__new__(DatabricksData)  # bypass auth/network for the guard unit
    db.allow_external = False
    for bad in ("DELETE FROM t", "drop table t", "  INSERT INTO t VALUES(1)", "MERGE INTO t"):
        with pytest.raises(PermissionError):
            db._guard(bad)
    db._guard("SELECT count(*) FROM t")  # read-only passes
    db.allow_external = True
    db._guard("DELETE FROM t")           # explicit, human-gated exception


def test_databricks_to_table_maps_response():
    pytest.importorskip("databricks.sdk")
    from adra.connectors.databricks import _to_table

    class _Col:
        def __init__(self, n): self.name = n

    class _Schema:
        columns = [_Col("a"), _Col("b")]

    class _Manifest:
        schema = _Schema()

    class _Result:
        data_array = [["1", "x"], ["2", "y"]]

    class _Resp:
        manifest = _Manifest()
        result = _Result()

    out = _to_table(_Resp())
    assert out == {"columns": ["a", "b"], "rows": [["1", "x"], ["2", "y"]]}


# --- Azure (construction / factory; SDK-required path skipped if absent) ----------------

def test_azure_factory_unknown_provider_errors():
    with pytest.raises(ValueError):
        get_data_provider({"provider": "totally-unknown"})


def test_azure_missing_workspace_id_is_clear_error():
    pytest.importorskip("azure.identity")
    with pytest.raises(RuntimeError, match="workspace id"):
        get_data_provider({"provider": "azure"})


def test_azure_degrades_without_sdk():
    """Without azure-identity, construction raises a clear 'pip install' error."""
    try:
        import azure.identity  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match=r"pip install adra\[azure\]"):
            get_data_provider({"provider": "azure", "workspace_id": "ws-1"})
    else:
        pytest.skip("azure-identity installed; degrade path covered by the import-guard")


def test_azure_runsql_is_kql_named_for_protocol():
    pytest.importorskip("azure.identity")
    from adra.connectors.azure import AzureMonitorData
    # run_sql exists (Protocol-named) and the dialect is KQL — documented behaviour.
    assert callable(AzureMonitorData.run_sql)
    assert AzureMonitorData.name == "azure"
