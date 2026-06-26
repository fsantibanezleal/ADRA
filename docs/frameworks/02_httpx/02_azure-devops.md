# httpx — the Azure DevOps connector (`AzureDevOpsRepo`)

`adra/connectors/azure_devops.py` is a thin, fully-owned Azure DevOps REST API **7.1** client
over `httpx`. It implements the same `RepoProvider` Protocol as the GitHub connector, so the
identical skills run against Azure DevOps with no engine change.

Landing: [02_httpx.md](./02_httpx.md).

## Why owned, not the `azure-devops` SDK (ADR-0008)

> The official `azure-devops` SDK is a stale, sync-only, untyped beta with no native Entra auth,
> so we own the few endpoints we need.

ADRA needs ~5 endpoints (list repos, list PRs, get PR + changes, post a comment thread, create a
work item). Owning them over `httpx` is smaller and more maintainable than a heavy, stale SDK, and
lets ADRA support both PAT and Entra bearer auth directly.

## Construction & auth

```python
AzureDevOpsRepo(organization, project, repo, token=None, *, bearer=False,
                base_url=None, allow_external=False)
```

- `import httpx` is inside `__init__`; missing → `RuntimeError("... pip install adra[azuredevops]
  (httpx).")`.
- Token resolution: `token=` → `AZURE_DEVOPS_EXT_PAT` → `AZURE_DEVOPS_PAT` →
  `AZURE_DEVOPS_TOKEN`. **BYOK, never logged.**
- Two auth modes:
  - **PAT (default)** → HTTP Basic with an empty username (`base64(":" + token)`), the Azure
    DevOps convention.
  - **Entra bearer** (`bearer=True`) → `Authorization: Bearer <token>`.
- `base_url` defaults to `https://dev.azure.com`; point it at an on-prem Azure DevOps Server
  collection URL when needed. Every call pins `api-version=7.1` (`_v`).

## Reads

| Method | Endpoint | Notes |
|---|---|---|
| `list_repositories()` | `GET …/git/repositories` | id + name + default branch + url |
| `list_pull_requests(state)` | `GET …/git/repositories/{repo}/pullrequests` | maps `open→active`, `closed→completed`, `all→all` |
| `get_pull_request(number)` | `GET …/pullrequests/{id}` + iterations + iteration changes | PR + changed paths + a path-level change summary |

### The diff difference (important)

Azure DevOps does **not** expose a raw unified patch. `_pr_changes` lists the **latest
iteration's changes** (path + change type) and builds a stable, diff-shaped summary string
(`"<changeType>\t<path>"`). So `PullRequest.diff` for ADO is a **path-level change summary**, not
a line-level patch. The deterministic discovery/contract checks (which key on *paths*, e.g.
test-discoverability) work directly; line-level semantic findings have less to chew on than with a
full GitHub patch. `_short_ref` strips `refs/heads/` from the branch names.

## Gated writes

Both call `_require_write()` (raises `PermissionError` unless `allow_external=True`):

| Method | Endpoint | Notes |
|---|---|---|
| `comment_on_pull_request(number, body)` | `POST …/pullrequests/{id}/threads` | posts a new comment thread |
| `create_issue(title, body)` | `POST …/wit/workitems/$Issue` (JSON-Patch) | creates a Work Item of type *Issue*; `Content-Type: application/json-patch+json` |

## Gotchas

- **`diff` is a change summary, not a patch** (see above) — don't expect line-level hunks from ADO.
- **PAT auth uses an empty username** in Basic auth — a non-obvious Azure DevOps convention.
- **Work-item creation uses a different API + content type** than Git, hence the dedicated call.
- **`api-version=7.1` is pinned on every request** via `_v`.

## What this IS and is NOT

- **IS** a minimal owned REST 7.1 client for the ADO surface ADRA needs, read-only by default.
- **IS NOT** a full ADO SDK; only the endpoints above are implemented (ADR-0008 status: the
  GitHub connector + emulator shipped first; the ADO/Databricks/Azure adapters followed).

## See also

- [01_github.md](./01_github.md) — the sibling GitHub connector.
- [../../data-contract/02_connector-shapes.md](../../data-contract/02_connector-shapes.md) — the
  `PullRequest` shape both connectors return.
- [../../security/security.md](../../security/security.md) — the gated-write posture.
