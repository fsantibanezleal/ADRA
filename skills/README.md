# ADRA as a Claude Code skill

This directory delivers the ADRA method as a portable **Claude Code Agent Skill**,
`adra-applied`. It is distinct from the engine's internal capabilities in
`adra/skills/` (those are the Python `Skill` classes the engine runs). This is the
same method delivered into an interactive coding agent.

## adra-applied

A deterministic-first, adversarial workflow for the software lifecycle across git
(GitHub or Azure DevOps), Databricks, and Azure: review or validate a PR/diff/issue,
run a validation or refutation experiment against a SQL warehouse, evaluate a
pipeline / job / resource, document an experiment or code, or propose an improvement
PR. It runs deterministic checks first as ground truth, keeps writes dry-run by
default, and escalates unresolved blockers to a human.

- [`adra-applied/SKILL.md`](adra-applied/SKILL.md) — the skill (frontmatter + lean body).
- [`adra-applied/reference/`](adra-applied/reference/) — phase playbooks (workflow, connections, rubric, experiments, documentation, pr-authoring), loaded on demand.
- [`adra-applied/scripts/`](adra-applied/scripts/) — deterministic tools (stdlib Python, dry-run by default, `--fixture` for offline replay): `resolve_target`, `merge_base_health`, `run_ci`, `bundle_validate`, `sql_probe`, `preflight`, `lang_scan`, `provenance`.
- [`adra-applied/assets/`](adra-applied/assets/) — `env.example` + PR/experiment templates.
- [`adra-applied/docs/diagrams/`](adra-applied/docs/diagrams/) — architecture, control loop, entry/router, components, connections, experiment lifecycle, and safety diagrams (SVG).

## Skill vs engine

| | engine (`adra/`, `pip install adra`) | skill (`skills/adra-applied/`) |
|---|---|---|
| Runtime | its own (multi-provider LLM / offline mock) | the Claude Code harness is the runtime |
| Loop | coded state machine | the host agent runs it, guided by the playbooks |
| Connectors | httpx / SDK, bring-your-own token | already-authenticated CLIs (`gh` / `az` / `databricks` / `git`) |
| Install | `pip install adra[...]` + provider keys | copy the folder; have the CLIs |
| Best for | automation, CI gates, headless, the console | a developer working interactively in Claude Code |

Both share the same rubric (the 8 ADRs + 5 incident CASES under
`adra/clients/`), the same deterministic checks, and the same discipline:
deterministic tools are ground truth, the critic blocks, and the agent escalates
rather than fabricating a pass.

## Install

Copy the skill into your personal skills directory:

```bash
cp -r skills/adra-applied ~/.claude/skills/adra-applied
```

Or enable this repository as a plugin (it carries a `.claude-plugin/plugin.json`).
Then copy `adra-applied/assets/env.example` to a local, git-ignored `.env` and fill
it. Prerequisites: `git`, GitHub CLI `gh`, Azure CLI `az` (+ `azure-devops`
extension), the `databricks` CLI, and Python 3.11+.

## Prerequisites and safety

Read-only / dry-run by default. Scripts touch a live system only with
`--allow-external`, and outward actions (push, PR create/complete/comment, bundle
deploy, wiki push) require an explicit human confirmation. Auth is delegated to the
CLIs; no tokens live in the scripts.