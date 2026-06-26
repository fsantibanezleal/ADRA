# 03 · The immutable `RunRecord` (provenance)

Every ADRA run writes one immutable, JSON-serializable `RunRecord` to `runs/<run_id>.json`
(`adra/provenance.py`). It is the **deep change-history / evidence layer**: every step's inputs,
the tool evidence, the critic verdicts, the decision, and the artifacts — all traceable to one
auditable artifact (ADR-0006). The `document` skill renders it into the human history layers.

Landing: [data-contract.md](./data-contract.md).

## `RunRecord` schema

```python
@dataclass
class RunRecord:
    skill: str
    intake: dict
    run_id: str          # "<YYYYMMDD-HHMMSS>-<6 hex>"
    started_at: str      # ISO-ish "%Y-%m-%dT%H:%M:%S"
    provider: str        # "mock" | "anthropic" | ...
    model: str
    steps: list[dict]    # append-only event log (see below)
    final_decision: str  # "accepted" | "escalate" | "pending"
    artifacts: dict[str, str]   # filename -> markdown
```

`to_dict()` produces the on-disk JSON; `write(runs_dir)` creates `runs/` and writes it with
`ensure_ascii=True`. `summary()` returns a one-line view (`run … | skill=… | decision=… |
critic_passes=N | last_clean=…`).

## The event log (`steps`)

`event(node, kind, payload)` appends one timestamped step. The orchestrator records, in order:

| node | kind | payload highlights |
|---|---|---|
| `plan` | `plan` | the plan + resolved plan model id |
| `ground` | `ground` | each tool's `log_dict()` (findings + summarized data) |
| `generate` | `generate` | a clipped draft preview + generate model id |
| `critic` | `critic` | the `CriticVerdict` (clean/blocking/attacks_tried/notes) + critic model id — **one per pass** |
| `revise` | `revise` | round number + clipped draft preview (one per revise round) |
| `decide` | `decide` | the final `decision` |

`ToolResult.log_dict()` summarizes list-valued evidence (`<N items>`) so the record stays compact
while keeping every finding.

## The typed domain model it serializes (`adra/state.py`)

| Type | Key fields |
|---|---|
| `Severity` | `BLOCKER > MAJOR > MINOR > NIT`; `.is_blocking` (blocker/major) |
| `Finding` | `severity, category, message, location, evidence, suggested_fix, source` |
| `ToolResult` | `tool, ran, findings, data, reason`; `.blocking`, `.clean` |
| `CriticVerdict` | `clean, blocking, attacks_tried, notes`; `.messages` |
| `RunState` | `skill, intake, plan, grounding, draft, findings, critic_history, rounds, decision, artifacts` |

The `RunRecord` mirrors `RunState` as the append-only, on-disk log — `RunState` is the mutable
in-memory thread; `RunRecord` is the immutable persisted history.

## Why immutable / why it matters

Append-only provenance is the audit trail (internal-algorithmic-auditing + model-card practice;
W3C PROV — see [../../refs/README.md](../../refs/README.md) §6). Because every verdict carries its
tool evidence in this record, a run is **replayable and defensible** — the second-method proof is
on disk, not in the model's prose. The `document` skill turns the record into PR/experiment/
methodology pages (see [../use-cases/05_document.md](../use-cases/05_document.md)).

![One run record, five layers of history](../images/history_layers.svg)

## What this IS and is NOT

- **IS** an immutable, JSON, per-run evidence + change-history record.
- **IS NOT** a mutable log you edit. Steps are append-only; the file is written once at close.

## See also

- [../architecture/03_data-flow.md](../architecture/03_data-flow.md) — the contracts that flow into
  the record.
- [../use-cases/05_document.md](../use-cases/05_document.md) — rendering the record to docs.
- [../adr/ADR-0006-immutable-provenance.md](../adr/ADR-0006-immutable-provenance.md)
