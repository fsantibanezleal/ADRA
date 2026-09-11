# Connections · how to reach each system

Default path uses the CLIs (`git`, `gh`, `az`, `databricks`); they are already
authenticated on the operator's machine and delegate auth safely. Read-only by
default; mutations need `--allow-external` **and** a confirmation.

## Contents

- Config and auth model
- git (local)
- GitHub (`gh`)
- Azure DevOps (`az`)
- Databricks (`databricks`)
- Azure (`az`)
- Resolving the production reference branch and CI command

## Config and auth model

Copy `assets/env.example` to a local, git-ignored `.env`. Endpoints, warehouse
ids, org/project, and the production reference branch are configuration. Auth is
delegated: `gh auth status`, `az login`, and `databricks` profiles. Never print,
rotate, or write a token; if auth fails, ask the operator to refresh it.

## git (local, read-only)

```bash
git -C <repo> fetch --all --prune
git -C <repo> merge-base <source> origin/<prod-ref>
git -C <repo> rev-list --count <base>..origin/<prod-ref>     # commits behind
git -C <repo> diff --name-status <base>..<source>            # D=deletion, R=rename
git -C <repo> diff <base>..<source>                          # unified diff
```

## GitHub (`gh`)

```bash
gh pr view <number|url> --repo <owner/repo> \
  --json number,title,state,baseRefName,headRefName,headRefOid,url,files,mergeable
gh pr diff <number|url> --repo <owner/repo>
gh pr checks <number|url> --repo <owner/repo>
gh issue view <number|url> --repo <owner/repo> --json number,title,body,state,labels
```

Gated writes (with `--allow-external` + confirmation):

```bash
gh pr comment <number|url> --repo <owner/repo> --body-file <file>
gh pr create --repo <owner/repo> --base <target> --head <source> \
  --title <title> --body-file <file>
```

## Azure DevOps (`az`, `azure-devops` extension)

Set `AZURE_DEVOPS_EXT_PAT` in the environment (or use `az login`).

```bash
az devops configure --defaults organization=$AZURE_DEVOPS_ORG project=$AZURE_DEVOPS_PROJECT
az repos pr show --id <pr-id> --output json     # sourceRefName, targetRefName, repository, lastMergeSourceCommit
az repos pr list --repository <repo> --status active --output json
az boards work-item show --id <id> --output json
```

Azure DevOps has no raw unified patch: fetch the repo locally and `git diff`
between the two refs for a real diff. Gated writes (comment thread, work-item
JSON-Patch) go through `az devops invoke`.

## Databricks (`databricks`)

Profiles are workspace-bound: `dev` cannot read `prod_*` and vice versa.

```bash
databricks current-user me --profile <dev|prod>
databricks warehouses list --profile <dev|prod> --output json
databricks warehouses get <warehouse_id> --profile <dev|prod>        # expect state RUNNING
databricks api post /api/2.0/sql/statements --profile <dev|prod> --json '{
  "warehouse_id":"<id>","statement":"<sql>","wait_timeout":"30s","format":"JSON_ARRAY"}'
databricks bundle validate -t <env>            # from the repo root; expect "Validation OK!"
```

Auth: dev = environment-profile PAT (read-only verify is fine); prod = OAuth
(`databricks auth login`). dev and prod are separate metastores; a prod→dev table
copy is a one-time flat export/import, never a cross-catalog CTAS or a bundle
deploy to dev. Run `preflight.py` before ever concluding "no access."

## Azure (`az`)

```bash
az account show --output json
az resource list --output json
az monitor log-analytics query --workspace <workspace-id> --analytics-query '<KQL>' --output json
```

Databricks cluster/job state is read via the `databricks` CLI, not `az`.

## Resolving the production reference branch and CI command

- **Production reference branch:** for an existing PR it is the PR's base
  (`baseRefName` / `targetRefName`); otherwise it is the team's configured
  production branch (`ADRA_PROD_REF_BRANCH`, `main` or `develop`). Never guess.
- **Exact CI command:** read it from the repo's pipeline files
  (`.github/workflows/*.yml`, `azure-pipelines*.yml`, or the shared CI template the
  repo references). Reproduce it verbatim; do not approximate.

`scripts/resolve_target.py` performs this resolution and returns repo + host +
prod-ref + source/target + diff + CI command as JSON.
