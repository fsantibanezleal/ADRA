# 02 · httpx — the GitHub + Azure DevOps REST connectors

**httpx** is the HTTP client behind ADRA's two **thin, fully-owned REST connectors**: GitHub
(REST v3) and Azure DevOps (REST 7.1). ADR-0008 records the decision to own the few endpoints
ADRA needs over a `httpx.Client` rather than depend on a vendor SDK (githubkit, or the stale
`azure-devops` SDK).

## At a glance

| | |
|---|---|
| Package | `httpx` |
| Pin | `>=0.27` |
| Install | `pip install adra[github]` and/or `pip install adra[azuredevops]` (both pull `httpx`) |
| ADRA modules | `adra/connectors/github.py` (`GitHubRepo`) · `adra/connectors/azure_devops.py` (`AzureDevOpsRepo`) |
| Implements | the `RepoProvider` Protocol (`adra/connectors/base.py`) |
| Decision | ADR-0008 |
| Posture | read-only by default; every write gated by `allow_external` (a human-confirmed action) |

## Read in order

1. [01_github.md](./01_github.md) — the GitHub connector: reads (PRs + unified diff + files),
   gated writes (issue, PR comment), auth, and the REST surface.
2. [02_azure-devops.md](./02_azure-devops.md) — the Azure DevOps connector: REST 7.1, PAT vs
   Entra bearer auth, iteration-changes (no raw patch), gated comment thread + work item.

## Why a thin REST client over httpx (ADR-0008)

> Adapters: GitHub via a **thin REST client over `httpx`** (read PRs + diff, issues, comments;
> writes gated) — githubkit/GraphQL optional later for line-level review composition; Azure DevOps
> via **raw REST 7.1 over `httpx`** (the official `azure-devops` SDK is a stale, sync-only, untyped
> beta with no native Entra auth, so we own the few endpoints we need).

- **Full control, small surface.** ADRA reads a handful of endpoints and writes two; a thin client
  is easier to audit (and to gate) than a large SDK.
- **One client, two platforms.** Both connectors are `httpx.Client(base_url=..., headers=...,
  timeout=30.0)` with auth headers set once; the read/write methods are a dozen lines each.
- **Lazy + degrade-clean.** `import httpx` is inside each connector's `__init__`; a missing extra
  raises a clear `RuntimeError` telling you `pip install adra[github]` / `adra[azuredevops]`. The
  engine never requires it.

## What this IS and is NOT

- **IS** a minimal, owned REST integration for exactly the GitHub/Azure-DevOps surface ADRA needs,
  read-only by default.
- **IS NOT** a general SDK wrapper. ADRA does not expose the full GitHub/ADO API; line-level
  review composition (GraphQL / githubkit) is explicitly deferred (ADR-0008).

## See also

- [../../data-contract/02_connector-shapes.md](../../data-contract/02_connector-shapes.md) — the
  `PullRequest` / `Issue` shapes these connectors return.
- [../../security/02_gated-writes.md](../../security/02_gated-writes.md) — how `allow_external`
  gates `create_issue` / `comment_on_pull_request`.
- [../../guides/02_the-cli.md](../../guides/02_the-cli.md) — `adra github-review owner/repo PR#`.
