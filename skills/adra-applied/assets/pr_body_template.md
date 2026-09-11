<!-- PR body template. Fixed section order. Replace every <...>. If the repo has its
     own PR template (.azuredevops/pull_request_template*.md or .github/PULL_REQUEST_TEMPLATE*),
     that template wins where it differs; keep these sections as the baseline.
     English on disk; reference other PRs by full URL; use commit-pinned file links. -->

## Objective

<what this PR achieves, in one or two sentences, and why>

## Changes

- <concrete change 1>
- <concrete change 2>

## What is NOT touched

- <explicit non-scope, to bound the blast radius>

## Validation

```
<exact CI command output: the real command, not an approximation>
```

- Coverage: <N>% (gate <M>%)
- `databricks bundle validate -t <env>`: <Validation OK! | n/a: no resources/ change>

## Risks / mitigations

- <risk> -> <mitigation>
- Rollback: <the named rollback for the smallest reversible change>

## Test plan

- <how a reviewer confirms it works>

## Work Item

<ticket id / full link>
