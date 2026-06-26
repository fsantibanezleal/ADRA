# 04 · Missing & outlier data — degrade lanes and gating

How ADRA handles inputs that are absent, unavailable, or pathological. The principle (ADR-0001):
**never fabricate** — a data gap becomes an honest "unknown" or a `ran=False` tool result, gated so
it cannot silently pass as success.

Landing: [data-contract.md](./data-contract.md).

## The degrade lane: `ToolResult(ran=False, reason=...)`

Every deterministic tool degrades gracefully when its dependency or permission is missing — it
returns `ran=False` with a `reason`, never a fabricated finding:

| Situation | Tool result |
|---|---|
| no repo path | `merge_base_health(ran=False, reason="no repo path provided")` |
| external calls disabled (dry-run) | `ci_command` / `bundle_validate` / `sql_probe` → `ran=False, reason="external calls disabled (dry-run); pass allow_external=True"` |
| missing CLI (git/databricks) | the `subprocess` call fails → empty output → tool returns no findings (degrades, doesn't crash) |
| missing connector extra | adapter `__init__` raises a clear `RuntimeError` naming the `pip install adra[...]` |
| missing creds / warehouse / workspace | `RuntimeError` at construction/probe time (Databricks/Azure), never opaque |

Because the package's verdict is carried by the deterministic floor, a `ran=False` tool simply
contributes no blocker — and the run continues honestly rather than asserting a green it cannot
prove.

## Fixtures: reproduce the exact decision logic offline

Each tool accepts an injected `fixture` so the offline path exercises the **same decision logic** as
a live run, without external calls:

- `git_fixture = {behind, deletions, renames}` → `merge_base_health`
- `ci_fixture` / `bundle_fixture` = `{stdout, returncode}` → `run_ci_command` / `bundle_validate`
- probe `fixture = {rows: [[...]]}` → `sql_probe`

This is how the emulator's synthetic PRs carry real, catchable failure modes offline (see
[../frameworks/05_stdlib-emulator/01_the-emulator.md](../frameworks/05_stdlib-emulator/01_the-emulator.md)).

## Outlier / pathological values (NaN-safe gating)

The deterministic checks are written to reject pathological inputs, not just normal ones:

- **Coverage / test parsing** keys on regex matches; a *missing* count is `None` (not `0`), so the
  "0 tests" blocker fires only on an actual `Ran 0 tests`, and "no data" on an actual
  `No data was collected` — absence is distinguished from zero.
- **Severity predicates** are explicit (`is_blocking` ∈ {BLOCKER, MAJOR}); a `MINOR`/`NIT` never
  blocks, so a low-severity outlier doesn't escalate.
- **The unverified-claim scan** turns hedging language (`probably`, `seems to`, `no access`, …)
  into a blocker — so a draft that *papers over* missing data with vague wording is rejected.

> Engineering note (portfolio rule): numeric guards must reject NaN — use `!(x > 0)` rather than
> `x <= 0`, since `NaN <= 0` is false. ADRA's parsers avoid the trap by distinguishing `None`
> (no match) from `0`; any new numeric tool check should follow the same NaN-safe pattern.

## The access preflight (the "no access" gate)

`sql_probe` carries an 8-point `PREFLIGHT` in its `data` whenever it can't run live (profile↔env
match, `current-user`, warehouse RUNNING, catalog/schema/table existence, group membership, SP
grant). The rubric item `unverifiable_no_access` then **blocks** any draft that concludes "no
access" while the probe returned no rows but carries that preflight — so a missing-grant config is
never reported as a data finding (illustrative case Northwind `CASE-2024-052`). The companion semantic item
`conclusion_beyond_evidence` blocks concluding anything the probe rows don't support.

## Untrusted intake

The intake (diff, PR body, issue text) is **untrusted** repo/PR content. The deterministic floor
(language/leak scan, merge-base, CI, bundle) runs over it without giving it authority, and the
connector phase adds the dual-LLM / capability split + sandboxing (see
[../security/03_untrusted-content.md](../security/03_untrusted-content.md)).

## What this IS and is NOT

- **IS** explicit degrade-and-gate behavior: missing data → `ran=False` / "unknown", pathological
  values rejected by NaN-safe checks, "no access" gated behind a preflight.
- **IS NOT** silent imputation. ADRA never fills a gap with a guess; it reports the gap and, if a
  conclusion depends on data it doesn't have, it stops (`conclusion_beyond_evidence`).

## See also

- [../methodologies/04_deterministic-first.md](../methodologies/04_deterministic-first.md) — the
  "diagnose, don't infer" principle.
- [03_run-record.md](./03_run-record.md) — `ran`/`reason` are persisted in the record.
- [../use-cases/03_experiment.md](../use-cases/03_experiment.md) — the preflight in action.
