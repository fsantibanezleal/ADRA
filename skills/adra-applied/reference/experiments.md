# Experiments — confirm or refute, against data

Use this to validate a reported issue, evaluate the state of a table / pipeline /
job / resource, or test any hypothesis against the data platform. The discipline
is ADR-0005 (shared warehouse, falsifiable hypotheses, persisted rows, the 8-point
preflight) and ADR-0001 (conclude only from a second-method proof).

## Contents

- Ground before hypothesizing
- State falsifiable, ranked hypotheses
- The test plan and iterations
- The access preflight
- Conclude and synthesize

## Ground before hypothesizing

Two deterministic sources, before any hypothesis is trusted:

1. **The real code**, cited line by line (file:line), not paraphrased.
2. **SQL / system tables**, run on the **shared SQL warehouse** via
   `scripts/sql_probe.py` — never a fresh interactive cluster. Pick the profile
   that matches the catalog env (`prod` for `prod_*`, `dev` for `dev_*`).

## State falsifiable, ranked hypotheses

A ranked table, not prose. Each hypothesis is falsifiable, carries a probability
and an impact-if-true, and is tied to a standalone probe.

```
| # | Hypothesis | Probability | Impact if true | Probe |
|---|-----------|-------------|----------------|-------|
| H1 | ...       | High        | ...            | 01_<name>.sql |
```

## The test plan and iterations

1. Run the prioritized probes on `prod` and `dev` with `sql_probe.py`.
2. Persist raw rows to `runs/<NN>_<env>_<timestamp>.json` (via `provenance.py` or
   directly). Rows are the evidence; keep them.
3. For each confirmed hypothesis: write a quantitative finding, its impact, and a
   proposed patch with a unit test.
4. For each discarded hypothesis: record the discard **with the data** that
   discarded it.
5. Work one probe per iteration (`v00..vN`). Keep dead-ends and redirections
   visible — show how the evidence moved the conclusion.

## The access preflight

Before ever writing "no access," run all 8 steps with `scripts/preflight.py`:
profile/env match, `current-user me`, warehouse `RUNNING`, `SHOW CATALOGS`, `SHOW
SCHEMAS IN <c>`, `SHOW TABLES IN <c>.<s>`, `is_member('<group>')`, and the
service-principal grant if the warehouse runs as an SP. Only after 8/8 still fail
do you report it — with every output attached.

## Conclude and synthesize

- Conclude **only what the rows support**. If a conclusion needs live data you do
  not have, say so and stop.
- Record confirmed vs discarded hypotheses with numbers.
- Close with a synthesis: an actionable recommendation, the pending items, and the
  PR that promotes any fix. For a bug fix, add a post-deploy validation probe
  proving the fix in production (a pre/post table over identical buckets).

Document the result with the experiment page set in
[documentation.md](documentation.md); the parent, version, and synthesis templates
are in `assets/`.
