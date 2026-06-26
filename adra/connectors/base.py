"""Connector layer — one Protocol family so the engine runs against a real platform
(GitHub, Azure DevOps, Databricks, Azure) or the self-contained offline emulator,
transparently. Read-only by default; every write is gated by ``allow_external`` and is
meant to sit behind an explicit human confirmation in interactive use.

This module is dependency-free; concrete adapters (``github`` needs ``httpx``) live in
sibling modules and are imported lazily by :func:`get_repo_provider`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class PullRequest:
    """A platform-agnostic pull/merge request."""

    number: int
    title: str
    source_branch: str
    target_branch: str
    diff: str = ""
    files: list[str] = field(default_factory=list)
    author: str = ""
    body: str = ""
    url: str = ""
    # Optional synthetic git state (emulator / fixtures) for pr_eval grounding.
    git_state: dict | None = None
    ci: dict | None = None

    def to_dict(self) -> dict:
        return {
            "number": self.number, "title": self.title, "source_branch": self.source_branch,
            "target_branch": self.target_branch, "files": self.files, "author": self.author,
            "url": self.url, "diff_len": len(self.diff),
        }


@dataclass
class Issue:
    number: int
    title: str
    url: str = ""


@runtime_checkable
class RepoProvider(Protocol):
    """Source-control surface ADRA reads (and, when gated, writes)."""

    name: str

    def list_pull_requests(self, state: str = "open") -> list[PullRequest]: ...
    def get_pull_request(self, number: int) -> PullRequest: ...
    def create_issue(self, title: str, body: str) -> Issue: ...                 # gated write
    def comment_on_pull_request(self, number: int, body: str) -> str: ...        # gated write


@runtime_checkable
class DataProvider(Protocol):
    """Read-only data/warehouse surface for experiments."""

    name: str

    def run_sql(self, sql: str) -> dict: ...   # -> {"columns": [...], "rows": [[...]]}


# --- intake builders: turn a PullRequest into an engine intake -------------------------

def code_review_intake(pr: PullRequest, ci_command: str | None = None) -> dict:
    """Build a ``code_review`` intake from a pull request."""
    intake: dict = {"diff": pr.diff}
    if ci_command:
        intake["ci_command"] = ci_command
    if pr.ci:
        intake.setdefault("ci_command", pr.ci.get("command", ""))
        intake["ci_fixture"] = pr.ci.get("fixture")
    return intake


def pr_eval_intake(pr: PullRequest) -> dict:
    """Build a ``pr_eval`` intake from a pull request (incl. synthetic git state if any)."""
    intake: dict = {
        "source_branch": pr.source_branch,
        "target_branch": pr.target_branch,
        "diff": pr.diff,
        "objective": pr.title,
    }
    if pr.git_state:
        intake["git_fixture"] = pr.git_state
    if pr.ci:
        intake["bundle_fixture"] = pr.ci.get("bundle_fixture")
    return intake
