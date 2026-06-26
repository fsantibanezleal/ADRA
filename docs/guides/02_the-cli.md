# 02 · The CLI

The `adra` command (`cli/__main__.py`) runs a capability through the adversarial loop and prints
the artifacts — over a provided intake, a **real GitHub PR**, or the offline **emulator**. Offline
by default (the `mock` provider). `--external` (a global flag) lets tools/connectors call out;
default is read-only.

Read order: 01 → **02** → 03. Landing: [guides.md](./guides.md).

## Commands

| Command | Purpose | Key args |
|---|---|---|
| `adra review <diff>` | Review a unified diff | `--ci-command '<exact CI cmd>'` |
| `adra pr-eval --source <branch>` | Evaluate a branch/PR | `--target main` · `--repo <path>` |
| `adra experiment <spec.json>` | Run a validation experiment | a JSON intake spec |
| `adra improve "<context>"` | Minimum-functional improvement proposal | text |
| `adra document [--type pr]` | Render a doc from a record/context | `--type pr\|experiment\|methodology` · `--title` |
| `adra decide "<problem>" <route> <route> …` | Route analysis (human-owned) | problem + ≥1 routes |
| `adra github-review <owner/repo> <PR#>` | Review a **real** GitHub PR (read-only) | `--skill code_review\|pr_eval` · `--post` |
| `adra emu list` / `adra emu review <PR#>` | Run against the offline emulator | `--skill code_review\|pr_eval` |

`--external` is global (place it before the subcommand: `adra --external github-review …`).

## Exit codes & output

`_print_run` prints each artifact, then the blocking findings (if any), then
`[decision: <accepted|escalate>]  run record: <id>.json`. The process exits **0** when accepted,
**2** otherwise — so escalation is detectable in CI.

## Examples

```bash
# Review a diff against your exact CI command (reproduces it only with --external)
adra --external review my.diff \
  --ci-command 'python -m coverage run -m unittest discover -s . -p "test*.py"'

# Decide between two routes (human-owned)
adra decide "Raise the refresh cadence" "edit the shared CI template" "change it in the owning repo"

# Review a real GitHub PR, read-only (needs adra[github] + a token in the env)
adra github-review owner/repo 42 --skill pr_eval

# …and post the verdict as a PR comment (needs BOTH --external and a token)
adra --external github-review owner/repo 42 --skill pr_eval --post

# The offline emulator (synthetic multi-industry PRs)
adra emu list
adra emu review 102                 # stale-base PR → blocked + escalated
adra emu review 101 --skill code_review
```

## The `experiment` spec (JSON)

```json
{
  "slug": "2024-09-tag-coverage-check",
  "warehouse_id": "",
  "probes": [
    {"sql": "SELECT count(*) FROM prod_orders_fulfilment.refined.order_stream",
     "profile": "prod",
     "fixture": {"rows": [["130000000"]]}}
  ]
}
```

Without `--external`, probes replay their `fixture` (offline). With `--external` + a valid
`warehouse_id`, they run live via the `databricks` CLI. See
[../use-cases/03_experiment.md](../use-cases/03_experiment.md) and the
[data contract](../data-contract/01_intake-contracts.md).

## Read-only by default

- No subcommand writes or runs external commands without `--external`.
- `github-review --post` additionally prints "(--post needs --external to write to GitHub;
  skipped)" if `--external` is absent.
- See [../security/02_gated-writes.md](../security/02_gated-writes.md).

## What this IS and is NOT

- **IS** a single CLI surface over all six skills, the GitHub connector, and the emulator.
- **IS NOT** a daemon/service. Each invocation is one run; the connected web experience is the
  separate private console (ADR-0009).

## See also

- [03_multi-provider-routing.md](./03_multi-provider-routing.md) — add the semantic layer.
- [05_local-scripts.md](./05_local-scripts.md) — `scripts/` wrappers around the same calls.
- [../use-cases/use-cases.md](../use-cases/use-cases.md) — what each skill checks.
