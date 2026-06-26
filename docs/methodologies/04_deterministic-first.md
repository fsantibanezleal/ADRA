# 04 · Deterministic-first grounding ("don't infer — diagnose")

The methodological core (ADR-0001): deterministic tools run **before** the LLM, are **ground
truth**, and **carry the verdict**. The model adds only what the tools cannot settle. This page is
the methodology framing; the architecture framing is
[architecture/05_why-deterministic-first.md](../architecture/05_why-deterministic-first.md).

Read order: 03 → **04** → 05. Landing: [methodologies.md](./methodologies.md).

## The principle in one line

> Don't infer — **diagnose**. Settle everything a tool can settle with the tool; for the rest,
> verify with an independent second method or say **"unknown"**.

This is encoded as the cross-cutting `unverified_claim` rubric item, and enforced mechanically by
the critic's `_UNVERIFIED_RE` scan (`probably`, `i assume`, `likely`, `should be fine`, `seems to`,
`no access`, `can't read`, `must be because`, `that's because`) — any such phrase in a draft is a
blocking finding demanding the second method or an explicit "unknown".

## Why it is non-negotiable (the theory)

| Failure mode | Source | ADRA's response |
|---|---|---|
| Hallucination is **intrinsic** to calibrated LMs | *Why LMs Hallucinate* (Kalai 2025, `arXiv:2509.04664`); *Calibrated LMs Must Hallucinate* (Kalai & Vempala 2023, `arXiv:2311.14648`) | the model is never the arbiter; tools settle what they can, the rest is "verify or unknown" |
| Ungrounded self-refinement **games its reward** | *Spontaneous Reward Hacking* (`arXiv:2407.04549`) | the critic's first pass is deterministic and non-overridable |
| Reproduce the **exact thing**; conclude only what evidence supports | Kapoor & Narayanan 2023 (leakage, `arXiv:2207.07048`) | the exact CI command, `bundle validate`, second-method probes |

## The deterministic floor (the tools)

Each tool returns a typed `ToolResult` (findings + raw evidence), used **twice**: as grounding the
model may not contradict, and as the second-method proof in the provenance record.

| Tool | Settles, mechanically |
|---|---|
| `git_tools.merge_base_health` | stale base (`behind`), hidden deletions, `.yml → .yml.t` resource drops |
| `ci_tools.run_ci_command` | the **exact** CI command's result — non-zero exit, `Ran 0 tests`, coverage `No data` |
| `bundle_tools.bundle_validate` | `databricks bundle validate` returned `Validation OK` (or not) |
| `lang_tools.scan_language` | Spanish content (MAJOR) + AI-session leak (BLOCKER) |
| `discovery_tools.check_test_discovery` | a `*_test.py` suffix CI's `test*.py` glob never collects |
| `sql_tools.sql_probe` | warehouse rows (+ the 8-point access preflight so "no access" is never asserted blindly) |

A tool that cannot run (missing CLI, external calls disabled) returns `ToolResult(ran=False,
reason=...)` — it degrades, it doesn't fabricate. NaN-safe and missing-data handling are detailed
in [../data-contract/04_missing-and-outlier-data.md](../data-contract/04_missing-and-outlier-data.md).

## Ordering is the architecture

`ground` runs before `generate`/`critic`; a blocking finding raised by a tool **stands regardless
of the model's opinion** (`pr_eval` even forces `changes-requested` whenever any grounding tool
reports a blocker). Because the floor carries the verdict, the whole loop — and the test suite —
runs **offline with the `mock` provider**. Connecting a real provider only adds the semantic
layer; it can never overturn a deterministic blocker.

## What this IS and is NOT

- **IS** a discipline of ordering and authority: tools decide what they can, the model decides
  only the rest, a human decides anything high-consequence.
- **IS NOT** anti-LLM. The semantic pass is where swallowed errors and contract drift are caught —
  it is *additive on top of* a hard, evidence-backed floor.

## References

Kalai 2025 (`arXiv:2509.04664`) · Kalai & Vempala 2023 (`arXiv:2311.14648`) · Spontaneous Reward
Hacking (`arXiv:2407.04549`) · Kapoor & Narayanan 2023 (`arXiv:2207.07048`). See
[../../refs/README.md](../../refs/README.md) §4, §7.

## See also

- [../architecture/05_why-deterministic-first.md](../architecture/05_why-deterministic-first.md)
- [03_shared-rubric.md](./03_shared-rubric.md) · [05_human-escalation.md](./05_human-escalation.md)
- [../adr/ADR-0001-deterministic-first-grounding.md](../adr/ADR-0001-deterministic-first-grounding.md)
