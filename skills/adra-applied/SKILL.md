---
name: adra-applied
description: >-
  Deterministic-first, adversarial workflow for the software lifecycle across git
  (GitHub or Azure DevOps), Databricks, and Azure. Use when reviewing or validating
  a pull request or diff, checking a reported issue, evaluating the state of a
  table / pipeline / job / cloud resource, running a validation or refutation
  experiment against a SQL warehouse, documenting an experiment or code, or
  proposing an improvement PR. Runs deterministic checks (merge-base health, exact
  CI, bundle validate, SQL probes, language/leak scan) first as ground truth, keeps
  writes dry-run by default, and escalates unresolved blockers to a human.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
metadata:
  version: 0.1.0
---

# ADRA Applied

Drive the software lifecycle with one rule:

> **Deterministic tools run first and are ground truth. You are additive: add
> only findings the tools cannot settle, and never contradict them.** When you
> cannot verify something with a tool or a second method, the honest output is
> "unknown."

Any deterministic blocker forces "changes requested." Never silently approve;
unresolved blockers **escalate to a human**. Every high-consequence decision stays
human-owned.

## Prerequisites and configuration

Tools this skill drives (confirm presence with the command in parentheses):
`git` (`git --version`), GitHub CLI `gh` (`gh auth status`), Azure CLI `az` with
the `azure-devops` extension (`az extension list`), Databricks CLI `databricks`
(`databricks --version`), Python 3 (`python --version`).

Configuration is a local, git-ignored `.env`. Copy `assets/env.example` to `.env`
and fill it. Endpoints (hosts, warehouse ids, catalogs, org/project) and the
**production reference branch** (`main` or `develop`, per the team) are
configuration: never guessed, never committed. See
[reference/connections.md](reference/connections.md).

## Safety defaults (do not skip)

- **Read-only / dry-run by default.** Scripts do not mutate unless invoked with
  `--allow-external`.
- **Confirm outward actions.** Even with `--allow-external`, ask the operator
  before anything a team can see: `git push`, `bundle deploy`, PR
  create/complete/comment, wiki push.
- **Never handle raw secrets.** Auth is delegated to `gh`, `az`, and `databricks`
  profiles. Do not print, rotate, or write tokens. If auth fails, ask the operator
  to refresh it.
- **Everything you write is English, third person, with no authoring-tool leak**
  (no tool/vendor names, no "co-authored-by", no "generated with AI"). Run the
  language scan on any text before it is committed.

## The loop

```
plan -> ground -> generate -> CRITIC -> (revise -> CRITIC)* -> decide
```

1. **plan**: decide which deterministic checks apply to the input.
2. **ground**: run them (the scripts in `scripts/`). Their results are the
   evidence and the ground truth.
3. **generate**: draft the artifact, reading the grounding first; add only what
   the tools cannot settle.
4. **critic**: re-attack the draft against the rubric
   ([reference/rubric.md](reference/rubric.md)). Any surviving blocker means it is
   not clean.
5. **revise**: feed surviving findings back and redraft.
6. **decide**: clean → accept; blockers after the round budget → escalate to a
   human with the evidence.

Record the run (plan, grounding, drafts, critic rounds, decision) with
`scripts/provenance.py` so documentation and the audit trail come from facts.

## Phase 0 · resolve the target

From a PR (id/URL), an issue, or a comment/symptom, resolve repo + host +
production reference branch + source/target + diff + exact CI command before any
analysis:

```bash
python scripts/resolve_target.py --input "<pr-url | owner/repo#123 | issue-url>" \
  [--repo-path <local path>] [--prod-ref <main|develop>]
```

It prefers `gh` for GitHub and `az repos` for Azure DevOps, and reads the CI
command from the repo's pipeline files. Details:
[reference/connections.md](reference/connections.md).

## Phase router

Pick the phase from the request and follow its playbook:

- **Review** a PR / diff / reported issue → [reference/workflow.md](reference/workflow.md) (Review).
  Ground with merge-base health, bundle validate (if `resources/` changed), the
  exact CI command, test discovery, and the language scan; add semantic findings;
  any blocker → changes requested.
- **Experiment**: confirm/refute a hypothesis or evaluate data/pipeline/job/
  resource → [reference/experiments.md](reference/experiments.md). Ranked
  falsifiable hypotheses, probes on the shared SQL warehouse, the 8-point access
  preflight, persisted rows, conclude only what the rows support, synthesize.
- **Document** an experiment / code / merged PR from provenance →
  [reference/documentation.md](reference/documentation.md). Experiment page set,
  PR change-control page, methodology history, gap table; publish under the
  two-phase gate (draft in a writable place, show the diff, get explicit approval,
  stage only specific files, then push).
- **Propose** an improvement PR or comment on one →
  [reference/pr-authoring.md](reference/pr-authoring.md). Smallest reversible
  change, blast radius assessed, PR template followed, labels applied, links
  commit-pinned.

## Deterministic tools

Run these from the skill directory; each is dry-run unless `--allow-external`,
accepts `--fixture <json>` to replay offline, and prints JSON.

| Script | Grounds | Reference |
|---|---|---|
| `scripts/merge_base_health.py` | stale base, deletions, `.yml`→`.yml.t` renames | ADR-0002/0003 |
| `scripts/run_ci.py` | exact CI command; test count, coverage, "no data collected" | ADR-0004 |
| `scripts/bundle_validate.py` | `databricks bundle validate -t <env>` verdict | ADR-0003 |
| `scripts/sql_probe.py` | a SQL statement on the shared warehouse; captured rows | ADR-0005 |
| `scripts/preflight.py` | the 8-point catalog access checklist | ADR-0005 |
| `scripts/lang_scan.py` | English-only + authoring-tool-leak scan | conventions |
| `scripts/resolve_target.py` | PR/issue/branch → repo + branches + diff + CI | n/a |
| `scripts/provenance.py` | append-only run record | ADR-0006 |

Usage detail and flags: [reference/workflow.md](reference/workflow.md).

## The rubric

The checks are eight architecture decisions and five incident cases, referenced by
id and portable across clients. Apply them in the critic step; treat every
`BLOCKER` and `MAJOR` as blocking. Full list:
[reference/rubric.md](reference/rubric.md).

## When to stop and escalate

Escalate to a human, do not fabricate a pass, when: a deterministic blocker
cannot be resolved; access still fails after the full 8-point preflight; a
conclusion would go beyond what the evidence supports; or an outward action needs
approval. Hand back the evidence and a clear recommendation.
