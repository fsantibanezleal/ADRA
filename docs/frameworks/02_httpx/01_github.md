# httpx — the GitHub connector (`GitHubRepo`)

`adra/connectors/github.py` is a thin GitHub REST v3 client over `httpx`. It implements the
`RepoProvider` Protocol: read pull requests and their unified diff, list PRs, and — only when
gated — create an issue or comment on a PR.

Landing: [02_httpx.md](./02_httpx.md).

## Construction & auth

```python
GitHubRepo(owner, repo, token=None, allow_external=False)
```

- `import httpx` is inside `__init__`; missing → `RuntimeError("the GitHub connector requires
  pip install adra[github] (httpx).")`.
- Token resolution: explicit `token=` → `GITHUB_TOKEN` → `GH_TOKEN` (env). **BYOK** — read from
  the environment, set as `Authorization: Bearer <token>`, and **never logged**.
- One client: `httpx.Client(base_url="https://api.github.com", headers=..., timeout=30.0)` with
  `Accept: application/vnd.github+json` and `X-GitHub-Api-Version: 2022-11-28`.

## Reads

| Method | Endpoint(s) | Returns |
|---|---|---|
| `get_pull_request(number)` | `GET /repos/{o}/{r}/pulls/{n}` (JSON) + the same with `Accept: …v3.diff` (unified diff) + paginated `…/files` | a `PullRequest` with `number`, `title`, `source_branch`, `target_branch`, `diff`, `files`, `author`, `body`, `url` |
| `list_pull_requests(state="open")` | paginated `GET /repos/{o}/{r}/pulls` | a list of `PullRequest` (metadata only; no diff) |

`_paginate` walks `page`/`per_page` until a short page, so `list`/`files` return the full set.

## Gated writes

Both call `_require_write()` first, which raises `PermissionError` unless `allow_external=True`:

| Method | Endpoint | Gate |
|---|---|---|
| `create_issue(title, body)` | `POST /repos/{o}/{r}/issues` | `allow_external` |
| `comment_on_pull_request(number, body)` | `POST /repos/{o}/{r}/issues/{n}/comments` (a PR is an issue for comments) | `allow_external` |

The CLI surfaces this: `adra github-review owner/repo PR# --post` only writes when `--external`
is also passed (`cli/__main__.py`); otherwise it prints "(--post needs --external to write to
GitHub; skipped)".

## The intake builders

`code_review_intake(pr)` / `pr_eval_intake(pr)` (`adra/connectors/base.py`) turn a fetched
`PullRequest` into the dict a skill expects — wiring the diff, CI fixture, and synthetic git
state through. See [../../data-contract/01_intake-contracts.md](../../data-contract/01_intake-contracts.md).

## Gotchas

- **The diff is fetched via the `v3.diff` Accept header**, not parsed from the JSON — so the
  exact unified patch the deterministic tools expect is what GitHub serves.
- **`list_pull_requests` carries no diff** (it is a cheap metadata listing); `get_pull_request`
  fetches the diff + files.
- **Read-only is the default**; `--post` + `--external` + a token are all required to write.

## What this IS and is NOT

- **IS** a small, auditable read path plus two gated writes.
- **IS NOT** line-level review composition — that (GraphQL / githubkit) is deferred per ADR-0008.

## See also

- [02_azure-devops.md](./02_azure-devops.md) — the sibling Azure DevOps connector.
- [../../use-cases/01_code-review.md](../../use-cases/01_code-review.md) ·
  [../../use-cases/02_pr-eval.md](../../use-cases/02_pr-eval.md) — the skills that consume it.
