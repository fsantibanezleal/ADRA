# 01 · Read-only by default

ADRA is **dry-run / read-only out of the box.** No deterministic tool runs an external command and
no connector writes unless external calls are explicitly enabled. This is the single most important
safety property: you can point ADRA at a repo/PR/warehouse and it will *read and reason*, never
*act*, until you opt in.

Landing: [security.md](./security.md).

## The `allow_external` gate

`Settings.allow_external_calls` defaults to `False` (`adra/config.py`); set it with
`ADRA_ALLOW_EXTERNAL=1` or the CLI's `--external`. With it off:

| Tool / connector | Behavior when off |
|---|---|
| `ci_tools.run_ci_command` | `ran=False, reason="external calls disabled (dry-run); pass allow_external=True"` — the CI command is **not executed** |
| `bundle_tools.bundle_validate` | same — `databricks bundle validate` not run |
| `sql_tools.sql_probe` | `ran=False` unless `allow_external` **and** a `warehouse_id` — replays a `fixture` if given, else returns the access preflight |
| `DatabricksData._guard` | rejects DDL/DML statements with `PermissionError` |
| connector `_require_write()` | raises `PermissionError` on any write |

Reads (fetching a PR + diff, listing PRs, replaying fixtures, running `git` inspection on a local
repo path) work without the gate; **actions** do not.

## The LLM cannot overturn the floor

Read-only-by-default is reinforced by deterministic-first (ADR-0001): the tools run first and a
blocking finding **stands regardless of the model's opinion**. The critic's first pass is
deterministic and non-overridable (`critic.deterministic_attacks`), and `pr_eval` forces
`changes-requested` whenever any grounding tool reports a blocker. So even a compromised or
hallucinating model cannot turn a real blocker into an approval.

## Why dry-run by default (ToolEmu)

High-impact agent actions must be gated (ToolEmu, Ruan 2023, `arXiv:2309.15817`): an agent reading
untrusted content with standing write capability is the classic agentic-risk shape. ADRA inverts
it — **read by default, act only on an explicit, confirmed opt-in** — so the dangerous capability is
never the default.

## What this IS and is NOT

- **IS** a read-first engine: analysis and verdicts with zero side effects until you opt in.
- **IS NOT** an agent with ambient write access. `--external` is a deliberate, per-invocation
  choice, and writes need a further human confirmation (next page).

## See also

- [02_gated-writes.md](./02_gated-writes.md) — the write gates in detail.
- [../methodologies/04_deterministic-first.md](../methodologies/04_deterministic-first.md) — why the
  floor, not the model, carries the verdict.
- [../guides/02_the-cli.md](../guides/02_the-cli.md) — `--external`.
