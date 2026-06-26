# 05 · `document`

Turn a run record (or any change description) into house documentation: a wiki **PR-XXXXX**
change-control page, an **experiment** page, or a **methodology-history** milestone. Documentation
is generated **from provenance**, so the technical, operational, and functional history all trace
back to one auditable run.

Landing: [use-cases.md](./use-cases.md). Code: `adra/skills/document.py`,
prompt `adra/prompts/document.md`.

## Input → grounding → output

| Stage | Detail |
|---|---|
| **Input** (intake) | `doc_type` (`pr` \| `experiment` \| `lesson`/methodology) + the record/context fields (`pr`, `title`, `status`, `summary`, `source`, `target`, `head`, `base`, `date`, `evidence`, `contracts`, …) |
| **plan** | records `doc_type` |
| **ground** (deterministic) | `doc_gap` (the source-of-truth gap table from `doc_gaps`) + `lang_tools.scan_language(summary)` — a leak scan of the material about to be written |
| **generate** | for `doc_type == "pr"`, fills the `PR_DOC_TEMPLATE` (Summary / Links / Metadata / Code changes (evidence) / Outputs-contracts impacted / Validation checklist); otherwise the model writes the page from the record (house style, English, third person, no AI-session leak) |
| **output** | `PR-<pr>.md` / `<slug>.md` (experiment) / `<slug>.md` (lesson) |

## The rubric items it enforces

| id | severity · kind | what it catches |
|---|---|---|
| `overclaim_language` | MAJOR · semantic | doc text claiming to "detect/predict/guarantee/prevent" — frame as likelihood/risk/recommendation |
| `language_leak` | BLOCKER · deterministic (cross-cutting) | English-only + **no AI-authorship leak** (no "Claude", "co-authored-by") |
| `unverified_claim` | MAJOR · deterministic (cross-cutting) | a documented cause asserted without a second method |

The leak scan is load-bearing here: `document` is the skill most likely to write text to disk, so
the cross-cutting `language_leak` BLOCKER guards every generated page before it lands.

## Why "from provenance"

Each ADRA run writes an immutable `RunRecord`; `document` renders that record into the human history
layers (ADR-0006). This mirrors internal-algorithmic-auditing and model-card practice — documents
generated **from evidence, not memory** — so the change history is reproducible.

![One run record, five layers of history](../images/history_layers.svg)

## Worked example (offline demo)

`{doc_type:"pr", pr:"1487", title:"…parallel task", status:"Merged", summary:"Split the
current-state table into its own task."}` → a `PR-1487.md` page from the template → **accepted**
(clean leak scan).

## Invoke

```bash
adra document --type pr --title "Estado-despacho parallel task"
```

## What this IS and is NOT

- **IS** evidence-derived documentation in house style, leak-scanned before it lands.
- **IS NOT** free-form prose that can overclaim or leak AI authorship — both are blocking checks.

## See also

- [../architecture/03_data-flow.md](../architecture/03_data-flow.md) — the `RunRecord` it renders.
- [../data-contract/03_run-record.md](../data-contract/03_run-record.md) — the record schema.
- [02_pr-eval.md](./02_pr-eval.md) — produces the verdict this documents.
