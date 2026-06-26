"""Real Azure DevOps connector (REST API 7.1 over httpx).

A thin, fully-owned REST client (ADR-0008 / dossier §2: the official ``azure-devops``
SDK is a stale, sync-only, untyped beta with no native Entra auth, so we own the few
endpoints we need). Lists repositories and pull requests, fetches a PR with its unified
diff, and — only when ``allow_external`` is set (a deliberate, human-gated action) —
posts a pull-request comment thread.

Auth is a Personal Access Token (Basic auth, empty username) or an Entra bearer token;
the credential is read from the environment / passed in and is never logged. Requires the
``azuredevops`` extra: ``pip install adra[azuredevops]`` (httpx).

API reference:
- PRs:            GET  /{org}/{project}/_apis/git/repositories/{repo}/pullrequests
- PR by id:       GET  /{org}/{project}/_apis/git/repositories/{repo}/pullrequests/{id}
- PR iterations:  GET  .../pullrequests/{id}/iterations
- iteration diff: GET  .../pullrequests/{id}/iterations/{i}/changes
- comment thread: POST .../pullrequests/{id}/threads            (gated write)
All calls pin ``api-version=7.1``.
"""

from __future__ import annotations

import base64
import os

from adra.connectors.base import Issue, PullRequest

_API_VERSION = "7.1"
_DEFAULT_BASE = "https://dev.azure.com"


class AzureDevOpsRepo:
    """A single Azure DevOps Git repository as a :class:`RepoProvider`.

    ``repo`` is the repository name or id; ``organization`` + ``project`` scope it.
    ``base_url`` defaults to the cloud (``https://dev.azure.com``); point it at an
    on-prem Azure DevOps Server collection URL when needed.
    """

    name = "azure_devops"

    def __init__(
        self,
        organization: str,
        project: str,
        repo: str,
        token: str | None = None,
        *,
        bearer: bool = False,
        base_url: str | None = None,
        allow_external: bool = False,
    ) -> None:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - only when extra missing
            raise RuntimeError(
                "the Azure DevOps connector requires `pip install adra[azuredevops]` (httpx)."
            ) from exc
        self.organization = organization
        self.project = project
        self.repo = repo
        self.allow_external = allow_external
        self._token = (
            token
            or os.environ.get("AZURE_DEVOPS_EXT_PAT")
            or os.environ.get("AZURE_DEVOPS_PAT")
            or os.environ.get("AZURE_DEVOPS_TOKEN")
        )
        base = (base_url or _DEFAULT_BASE).rstrip("/")
        headers = {"Accept": "application/json", "User-Agent": "adra"}
        if self._token:
            if bearer:
                headers["Authorization"] = f"Bearer {self._token}"
            else:
                # PAT → HTTP Basic with an empty username (Azure DevOps convention).
                pair = base64.b64encode(f":{self._token}".encode()).decode()
                headers["Authorization"] = f"Basic {pair}"
        self._http = httpx
        self._client = httpx.Client(base_url=base, headers=headers, timeout=30.0)

    # ---- url helpers -------------------------------------------------------------------
    def _proj(self) -> str:
        return f"/{self.organization}/{self.project}/_apis"

    def _git(self) -> str:
        return f"{self._proj()}/git/repositories/{self.repo}"

    def _v(self, params: dict | None = None) -> dict:
        params = dict(params or {})
        params["api-version"] = _API_VERSION
        return params

    # ---- reads -------------------------------------------------------------------------
    def list_repositories(self) -> list[dict]:
        """List repositories in the project (id + name + default branch + url)."""
        r = self._client.get(f"{self._proj()}/git/repositories", params=self._v())
        r.raise_for_status()
        out = []
        for j in r.json().get("value", []):
            out.append({
                "id": j.get("id", ""),
                "name": j.get("name", ""),
                "default_branch": j.get("defaultBranch", ""),
                "url": j.get("webUrl") or j.get("remoteUrl", ""),
            })
        return out

    def list_pull_requests(self, state: str = "open") -> list[PullRequest]:
        status = {"open": "active", "closed": "completed", "all": "all"}.get(state, state)
        params = self._v({"searchCriteria.status": status, "$top": 50})
        r = self._client.get(f"{self._git()}/pullrequests", params=params)
        r.raise_for_status()
        return [self._to_pr(j) for j in r.json().get("value", [])]

    def get_pull_request(self, number: int) -> PullRequest:
        r = self._client.get(f"{self._git()}/pullrequests/{number}", params=self._v())
        r.raise_for_status()
        pr = self._to_pr(r.json())
        files, diff = self._pr_changes(number)
        pr.files = files
        pr.diff = diff
        return pr

    def _to_pr(self, j: dict) -> PullRequest:
        return PullRequest(
            number=j.get("pullRequestId", 0),
            title=j.get("title", ""),
            source_branch=_short_ref(j.get("sourceRefName", "")),
            target_branch=_short_ref(j.get("targetRefName", "")),
            author=(j.get("createdBy") or {}).get("displayName", ""),
            body=j.get("description") or "",
            url=j.get("url", ""),
        )

    def _pr_changes(self, number: int) -> tuple[list[str], str]:
        """Return (changed paths, a path-level change summary).

        Azure DevOps exposes per-iteration *changes* (path + change type), not a raw
        unified patch. We list the latest iteration's changes; the path list grounds the
        deterministic discovery/contract checks, and the summary is a stable, diff-shaped
        string the explainer can read without a live blob fetch.
        """
        it = self._client.get(f"{self._git()}/pullrequests/{number}/iterations",
                              params=self._v())
        it.raise_for_status()
        iters = it.json().get("value", [])
        if not iters:
            return [], ""
        last = max(i.get("id", 0) for i in iters)
        ch = self._client.get(
            f"{self._git()}/pullrequests/{number}/iterations/{last}/changes",
            params=self._v(),
        )
        ch.raise_for_status()
        files, lines = [], []
        for c in ch.json().get("changeEntries", []) or ch.json().get("changes", []):
            path = (c.get("item") or {}).get("path", "")
            kind = c.get("changeType", "edit")
            if path:
                files.append(path.lstrip("/"))
                lines.append(f"{kind}\t{path}")
        return files, "\n".join(lines)

    # ---- gated writes ------------------------------------------------------------------
    def _require_write(self) -> None:
        if not self.allow_external:
            raise PermissionError(
                "write blocked: set allow_external=True (and confirm) to post PR comment threads."
            )

    def comment_on_pull_request(self, number: int, body: str) -> str:
        """Post a new comment thread on a pull request (gated write)."""
        self._require_write()
        payload = {
            "comments": [{"parentCommentId": 0, "content": body, "commentType": "text"}],
            "status": "active",
        }
        r = self._client.post(f"{self._git()}/pullrequests/{number}/threads",
                              params=self._v(), json=payload)
        r.raise_for_status()
        j = r.json()
        return f"{self._git()}/pullrequests/{number}/threads/{j.get('id', '')}"

    def create_issue(self, title: str, body: str) -> Issue:
        """Create a work item of type *Issue* in the project (gated write).

        Uses the Work Item Tracking REST API (JSON-Patch document); the URL field shape
        differs from Git, hence the dedicated client call.
        """
        self._require_write()
        ops = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": body},
        ]
        r = self._client.post(
            f"/{self.organization}/{self.project}/_apis/wit/workitems/$Issue",
            params=self._v(),
            headers={"Content-Type": "application/json-patch+json"},
            json=ops,
        )
        r.raise_for_status()
        j = r.json()
        return Issue(number=j.get("id", 0), title=title,
                     url=(j.get("_links", {}).get("html", {}) or {}).get("href", j.get("url", "")))


def _short_ref(ref: str) -> str:
    """``refs/heads/feature/x`` -> ``feature/x``."""
    return ref.removeprefix("refs/heads/") if ref else ""
