"""Real GitHub connector (REST v3 over httpx).

Reads pull requests + their unified diff, lists PRs, and — only when ``allow_external``
is set (a deliberate, human-gated action) — creates an issue or comments on a PR. The
token is read from the environment / passed in and is never logged. Requires the
``github`` extra: ``pip install adra[github]``.

This is intentionally a thin REST client (full control, small surface); a richer client
(githubkit) or GraphQL can back line-level review composition later.
"""

from __future__ import annotations

import os

from adra.connectors.base import Issue, PullRequest

_API = "https://api.github.com"
_JSON = "application/vnd.github+json"
_DIFF = "application/vnd.github.v3.diff"
_VER = "2022-11-28"


class GitHubRepo:
    """A single GitHub repository as a :class:`~adra.connectors.base.RepoProvider`."""

    name = "github"

    def __init__(self, owner: str, repo: str, token: str | None = None,
                 allow_external: bool = False) -> None:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - only when extra missing
            raise RuntimeError("the GitHub connector requires `pip install adra[github]` (httpx).") from exc
        self.owner = owner
        self.repo = repo
        self.allow_external = allow_external
        self._token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        headers = {"Accept": _JSON, "X-GitHub-Api-Version": _VER, "User-Agent": "adra"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        self._http = httpx
        self._client = httpx.Client(base_url=_API, headers=headers, timeout=30.0)

    # ---- reads -------------------------------------------------------------------------
    def _base(self) -> str:
        return f"/repos/{self.owner}/{self.repo}"

    def get_pull_request(self, number: int) -> PullRequest:
        r = self._client.get(f"{self._base()}/pulls/{number}")
        r.raise_for_status()
        j = r.json()
        d = self._client.get(f"{self._base()}/pulls/{number}", headers={"Accept": _DIFF})
        d.raise_for_status()
        files = [f["filename"] for f in self._paginate(f"{self._base()}/pulls/{number}/files")]
        return PullRequest(
            number=j["number"], title=j.get("title", ""),
            source_branch=j.get("head", {}).get("ref", ""),
            target_branch=j.get("base", {}).get("ref", ""),
            diff=d.text, files=files, author=j.get("user", {}).get("login", ""),
            body=j.get("body") or "", url=j.get("html_url", ""),
        )

    def list_pull_requests(self, state: str = "open") -> list[PullRequest]:
        out = []
        for j in self._paginate(f"{self._base()}/pulls", params={"state": state, "per_page": 50}):
            out.append(PullRequest(
                number=j["number"], title=j.get("title", ""),
                source_branch=j.get("head", {}).get("ref", ""),
                target_branch=j.get("base", {}).get("ref", ""),
                author=j.get("user", {}).get("login", ""), url=j.get("html_url", ""),
            ))
        return out

    def _paginate(self, path: str, params: dict | None = None) -> list[dict]:
        params = dict(params or {}); params.setdefault("per_page", 100)
        items, page = [], 1
        while True:
            params["page"] = page
            r = self._client.get(path, params=params)
            r.raise_for_status()
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            items.extend(batch)
            if len(batch) < params["per_page"]:
                break
            page += 1
        return items

    # ---- gated writes ------------------------------------------------------------------
    def _require_write(self) -> None:
        if not self.allow_external:
            raise PermissionError(
                "write blocked: set allow_external=True (and confirm) to create issues / comments."
            )

    def create_issue(self, title: str, body: str) -> Issue:
        self._require_write()
        r = self._client.post(f"{self._base()}/issues", json={"title": title, "body": body})
        r.raise_for_status()
        j = r.json()
        return Issue(number=j["number"], title=j.get("title", title), url=j.get("html_url", ""))

    def comment_on_pull_request(self, number: int, body: str) -> str:
        # A PR is an issue for the comments endpoint.
        self._require_write()
        r = self._client.post(f"{self._base()}/issues/{number}/comments", json={"body": body})
        r.raise_for_status()
        return r.json().get("html_url", "")
