# 02 · Connector shapes (Protocols + dataclasses)

All platform access goes through one **`Protocol` family** (`adra/connectors/base.py`), so the same
skills run against a real platform or the offline emulator transparently (ADR-0008). This page is
the exact shape of those Protocols and the dataclasses they pass.

Landing: [data-contract.md](./data-contract.md).

## The Protocols

```python
@runtime_checkable
class RepoProvider(Protocol):
    name: str
    def list_pull_requests(self, state: str = "open") -> list[PullRequest]: ...
    def get_pull_request(self, number: int) -> PullRequest: ...
    def create_issue(self, title: str, body: str) -> Issue: ...                # gated write
    def comment_on_pull_request(self, number: int, body: str) -> str: ...      # gated write

@runtime_checkable
class DataProvider(Protocol):
    name: str
    def run_sql(self, sql: str) -> dict: ...   # -> {"columns": [...], "rows": [[...]]}
```

A new platform needs only a `Protocol`-conformant adapter. Implementations:
`GitHubRepo` · `AzureDevOpsRepo` · `EmulatorRepo` (RepoProvider); `DatabricksData` ·
`AzureMonitorData` · `EmulatorData` (DataProvider). The factories `get_repo_provider(binding)` /
`get_data_provider(binding)` wire them from a client binding dict.

## `PullRequest` (platform-agnostic)

```python
@dataclass
class PullRequest:
    number: int
    title: str
    source_branch: str
    target_branch: str
    diff: str = ""              # unified patch (GitHub) OR path-level change summary (Azure DevOps)
    files: list[str] = []
    author: str = ""
    body: str = ""
    url: str = ""
    git_state: dict | None = None   # optional synthetic git state for pr_eval (emulator/fixtures)
    ci: dict | None = None          # optional CI fixture / command
```

`to_dict()` returns a compact view (it logs `diff_len`, not the full diff). Note the
platform-specific `diff` semantics: GitHub serves a real unified patch; Azure DevOps serves a
path-level change summary (see
[../frameworks/02_httpx/02_azure-devops.md](../frameworks/02_httpx/02_azure-devops.md)).

## `Issue`

```python
@dataclass
class Issue:
    number: int
    title: str
    url: str = ""
```

## The `DataProvider` table shape

`run_sql` always returns `{"columns": [...], "rows": [[...]]}` — across Databricks SQL (ANSI),
Azure Log Analytics (**KQL**, same method name), and the emulator's SQLite. The uniform shape is
what lets the `experiment` probe runner stay platform-agnostic.

## The intake builders (connector → engine)

```python
code_review_intake(pr, ci_command=None) -> dict   # {diff, ci_command?, ci_fixture?}
pr_eval_intake(pr) -> dict                          # {source_branch, target_branch, diff, objective,
                                                     #  git_fixture?, bundle_fixture?}
```

These bridge the connector shape to the [intake contract](./01_intake-contracts.md): `pr.git_state`
becomes `git_fixture`; `pr.ci` becomes `ci_command` + `ci_fixture` (or `bundle_fixture`).

## Gated writes

`create_issue` / `comment_on_pull_request` are **writes**: each adapter's `_require_write()` raises
`PermissionError` unless `allow_external=True`. See
[../security/02_gated-writes.md](../security/02_gated-writes.md).

## What this IS and is NOT

- **IS** one Protocol family with platform-agnostic dataclasses; adapters are interchangeable.
- **IS NOT** a leaky abstraction — except the documented `diff` difference (patch vs change
  summary), the skills don't know which platform they're on.

## See also

- [../frameworks/02_httpx/02_httpx.md](../frameworks/02_httpx/02_httpx.md) — the REST adapters.
- [../frameworks/05_stdlib-emulator/01_the-emulator.md](../frameworks/05_stdlib-emulator/01_the-emulator.md)
  — the offline implementations.
- [01_intake-contracts.md](./01_intake-contracts.md) — what the builders produce.
