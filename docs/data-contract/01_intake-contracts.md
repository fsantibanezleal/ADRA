# 01 · Intake contracts (per skill)

The **intake** is the dict a caller passes to `Orchestrator.run(skill, intake)`. It is the only
loosely-typed boundary in ADRA; each skill reads a documented set of keys (from the skill's
`ground`/`generate`). Missing optional keys degrade cleanly (a tool returns `ran=False`), not
crash.

Landing: [data-contract.md](./data-contract.md).

## `code_review`

| Key | Req | Type | Meaning |
|---|---|---|---|
| `diff` | ✅ | str | unified diff / patch text (`+++ b/<path>` lines drive `added_paths`) |
| `ci_command` | – | str | the **exact** CI command to reproduce |
| `ci_fixture` | – | `{stdout, returncode}` | replay a captured CI result offline |

## `pr_eval`

| Key | Req | Type | Meaning |
|---|---|---|---|
| `source_branch` | ✅ | str | branch under review (default `HEAD`) |
| `target_branch` | – | str | integration branch (default `develop`) |
| `objective` | – | str | PR objective (fills the body) |
| `git_fixture` | – | `{behind:int, deletions:[str], renames:[str]}` | replay merge-base health offline |
| `bundle_target` | – | str | DAB target (default `dev`) |
| `bundle_fixture` | – | `{stdout, returncode}` | replay `bundle validate` offline |
| `pr_body_draft` | – | str | scanned for language/leak |
| `work_item` | – | str | ticket id |

## `experiment`

| Key | Req | Type | Meaning |
|---|---|---|---|
| `slug` | – | str | artifact base name (default `experiment`) |
| `warehouse_id` | – | str | SQL warehouse id (required for live execution) |
| `probes` | ✅ | `[{sql, profile, fixture?}]` | one probe per entry |
| &nbsp;&nbsp;`probes[].sql` | ✅ | str | the SQL statement |
| &nbsp;&nbsp;`probes[].profile` | – | str | `prod` / `dev` (default `prod`) |
| &nbsp;&nbsp;`probes[].fixture` | – | `{rows:[[...]]}` | replay rows offline |

## `improve`

| Key | Req | Type | Meaning |
|---|---|---|---|
| `context` | ✅ | str | what to improve (also scanned for language/leak) |

## `document`

| Key | Req | Type | Meaning |
|---|---|---|---|
| `doc_type` | – | str | `pr` (default) \| `experiment` \| `lesson`/methodology |
| `summary` | – | str | scanned for AI-session leak before writing |
| `doc_gaps` | – | list | source-of-truth gap table |
| `pr`,`title`,`status`,`source`,`target`,`head`,`base`,`date`,`evidence`,`contracts`,`files`,`pr_url`,`slug` | – | str | fill the PR/experiment/lesson template |

## `decide`

| Key | Req | Type | Meaning |
|---|---|---|---|
| `problem` | ✅ | str | the decision to make (also scanned) |
| `routes` | ✅ | `[str]` | candidate routes (≥1) |

## How the CLI / connectors build intakes

- The CLI (`cli/__main__.py`) builds these dicts from flags.
- The connector intake builders (`adra/connectors/base.py`) turn a fetched `PullRequest` into a
  `code_review` / `pr_eval` intake: `code_review_intake(pr)` wires `diff` (+ CI command/fixture from
  `pr.ci`); `pr_eval_intake(pr)` wires `source_branch` / `target_branch` / `diff` / `objective`
  (+ `git_fixture` from `pr.git_state`, `bundle_fixture` from `pr.ci`).

## Units & conventions

- `behind` is an integer **commit count**.
- `returncode` is a process exit code (`0` = ok).
- All text is expected **English** (the language scan flags Spanish + AI-leak).
- `fixture` keys make any tool reproducible offline without changing its decision logic — see
  [04_missing-and-outlier-data.md](./04_missing-and-outlier-data.md).

## What this IS and is NOT

- **IS** the precise, code-verified key set each skill reads.
- **IS NOT** a rigid schema object — intake is an open dict; unknown keys are ignored, missing
  optional keys degrade (not crash).

## See also

- [02_connector-shapes.md](./02_connector-shapes.md) — where `PullRequest` → intake.
- [../use-cases/use-cases.md](../use-cases/use-cases.md) — what each skill does with the intake.
