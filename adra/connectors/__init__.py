"""ADRA connector layer: one Protocol family, real adapters + the offline emulator.

    get_repo_provider({"provider": "github", "owner": "...", "repo": "...", "token": "..."})
    get_repo_provider({"provider": "emulator"})

Read-only by default; writes need ``allow_external=True`` (a gated, human-confirmed action).
"""

from __future__ import annotations

from adra.connectors.base import (
    DataProvider,
    Issue,
    PullRequest,
    RepoProvider,
    code_review_intake,
    pr_eval_intake,
)

__all__ = [
    "PullRequest", "Issue", "RepoProvider", "DataProvider",
    "code_review_intake", "pr_eval_intake",
    "get_repo_provider", "get_data_provider",
]


def get_repo_provider(binding: dict) -> RepoProvider:
    """Wire a repo provider from a client binding."""
    provider = binding.get("provider", "emulator")
    if provider == "github":
        from adra.connectors.github import GitHubRepo
        return GitHubRepo(
            binding["owner"], binding["repo"],
            token=binding.get("token"), allow_external=binding.get("allow_external", False),
        )
    if provider == "emulator":
        from adra.connectors.emulator import EmulatorRepo
        return EmulatorRepo()
    raise ValueError(f"unknown repo provider {provider!r}; known: github, emulator")


def get_data_provider(binding: dict) -> DataProvider:
    """Wire a data provider from a client binding (read-only probes)."""
    provider = binding.get("provider", "emulator")
    if provider == "emulator":
        from adra.connectors.emulator import EmulatorData
        return EmulatorData()
    raise ValueError(f"unknown data provider {provider!r}; known: emulator")
