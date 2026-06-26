# 03 · `experiment`

A hypothesis-driven validation experiment in the house format: a hypothesis table (probability /
impact / probe), standalone SQL probes against the shared warehouse, and a synthesis that
**concludes only what the probe rows support**.

Landing: [use-cases.md](./use-cases.md). Code: `adra/skills/experiment.py`,
prompt `adra/prompts/experiment.md`.

## Input → grounding → output

| Stage | Detail |
|---|---|
| **Input** (intake) | `slug`, optional `warehouse_id`, `probes: [{sql, profile, fixture?}]` |
| **plan** | declares tool: `sql_probe` |
| **ground** (deterministic) | one `sql_tools.sql_probe(sql, warehouse_id, profile, allow_external, fixture)` per probe → `probe_01`, `probe_02`, … |
| **generate** | model returns `{title, hypotheses:[{id,hypothesis,probability,impact,probe}], design, synthesis}` |
| **output** | `<slug>.md` (title + hypotheses table + design) and `<slug>__v0X-synthesis.md` (synthesis + evidence: probe count + total rows) |

## Probe execution: fixture vs live

`sql_probe` runs in three modes (`adra/tools/sql_tools.py`):

- **fixture** — replays `{"rows": [...]}` offline (reproducible; the demo uses this).
- **live** — only when `allow_external=True` **and** `warehouse_id` is set: posts the statement via
  the `databricks` CLI (`/api/2.0/sql/statements`), parses `result.data_array`.
- **dry-run** — neither → `ran=False, reason="external calls disabled or no warehouse_id"`, and
  returns the **8-point access `PREFLIGHT`** in `data` (so "no access" is never concluded blindly).

A probe carries **no findings** — it gathers evidence; the skill and critic interpret it.

## The rubric items it enforces

| id | severity · kind | what it catches |
|---|---|---|
| `unverifiable_no_access` | MAJOR · deterministic | "no access" concluded without exhausting the profile/warehouse/grants preflight |
| `conclusion_beyond_evidence` | MAJOR · semantic | a conclusion the probe rows don't support; record discarded hypotheses too |
| `unverified_claim` | MAJOR · deterministic (cross-cutting) | a cause asserted without a second method |
| `overclaim_language` | MAJOR · semantic | "detect/predict/guarantee/prevent" framing |
| `language_leak` | BLOCKER · deterministic (cross-cutting) | English-only + no AI-session leak |

The critic specifically links the draft text to grounding: if the draft says "no access" /
"permission denied" and the matching `sql_probe` returned no rows but carries a `preflight`, the
`unverifiable_no_access` blocker fires.

## Worked example (offline demo)

A single probe `SELECT count(*) FROM prod_orders_fulfilment.refined.order_stream` with a fixture of
`[["130000000"]]` → grounding has one probe, 1 row; the synthesis concludes only what that row
supports → **accepted**.

## Invoke

```bash
adra experiment spec.json          # offline (fixtures); add --external for live SQL
python scripts/run_experiment.py spec.json --external
```

Spec shape: see [02_the-cli.md](../guides/02_the-cli.md) and
[../data-contract/01_intake-contracts.md](../data-contract/01_intake-contracts.md).

## What this IS and is NOT

- **IS** a refutation-minded validation experiment: probe first, conclude only from the rows,
  record what you discarded.
- **IS NOT** a model "explaining" an anomaly from priors. A conclusion needing live data you don't
  have must say so and stop (`conclusion_beyond_evidence`).

## See also

- [../frameworks/03_databricks-sdk/01_usage-and-safety.md](../frameworks/03_databricks-sdk/01_usage-and-safety.md)
  — the live read-only `DataProvider`.
- [../data-contract/04_missing-and-outlier-data.md](../data-contract/04_missing-and-outlier-data.md)
  — the access preflight + degrade lanes.
- [../methodologies/04_deterministic-first.md](../methodologies/04_deterministic-first.md)
