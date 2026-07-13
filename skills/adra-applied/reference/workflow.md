# Workflow — the loop, the tools, and the Review phase

## Contents

- The loop, restated
- Running the deterministic tools
- Phase: Review (PR / diff / issue)
- Provenance
- Escalation

## The loop, restated

`plan → ground → generate → CRITIC → (revise → CRITIC)* → decide`. Ground first
with the scripts below; their output is the evidence. Draft only after reading it.
Attack the draft with [rubric.md](rubric.md). Accept only a clean draft; escalate
unresolved blockers.

## Running the deterministic tools

All scripts live in `scripts/`, print JSON to stdout, exit non-zero on a blocking
condition, are **dry-run unless `--allow-external`**, and accept `--fixture
<path-or-json>` to replay a captured result offline (no network, no secrets).

```bash
# stale base + destructive diff (read-only git; safe to run anytime)
python scripts/merge_base_health.py --repo <path> --source <branch> --target <prod-ref>

# exact CI reproduction (mutating-capable → needs --allow-external to actually run)
python scripts/run_ci.py --repo <path> --command "<exact CI command>" --allow-external

# DAB validation (read-only validate; --allow-external to reach a live workspace)
python scripts/bundle_validate.py --repo <path> --target <env> --allow-external

# SQL probe on the shared warehouse (needs --allow-external + a warehouse id)
python scripts/sql_probe.py --profile <dev|prod> --warehouse-id <id> \
  --statement "SELECT count(*) FROM <catalog>.<schema>.<table>" --allow-external

# 8-point catalog access preflight (run before ever concluding "no access")
python scripts/preflight.py --profile <dev|prod> --warehouse-id <id> \
  --catalog <c> --schema <s> --table <t> --group <granting-group> --allow-external

# language + authoring-tool-leak scan (always safe; run on any text before commit)
python scripts/lang_scan.py --path <file-or-dir>        # or: --text "<string>"

# resolve an entry point into a concrete target
python scripts/resolve_target.py --input "<pr-url | owner/repo#123 | issue-url>"

# record the run (append-only provenance)
python scripts/provenance.py --skill review --event ground --payload '<json>'
```

Offline first: every script runs with `--fixture` and no `--allow-external`, so the
whole loop can be exercised and tested without touching a real system. Turn on
`--allow-external` only when the operator wants live results, and confirm before
any outward action.

## Phase: Review (PR / diff / issue)

1. **Resolve** the target (`resolve_target.py`): repo, host, production reference
   branch, source/target, diff, exact CI command.
2. **Ground**, in this order (the first is the destructive failure mode):
   - `merge_base_health.py` — if behind, require rebase/recreate; if deletions or
     `.yml`→`.yml.t` renames, block until confirmed.
   - `bundle_validate.py` — only if the diff touches `resources/`; require
     `Validation OK!`.
   - `run_ci.py` — reproduce the **exact** CI command; block on non-zero exit,
     `Ran 0 tests`, or "No data was collected"; note coverage vs the gate.
   - test discovery — `test*.py` prefix, `__init__.py` present, coverable logic in
     importable non-notebook modules.
   - `lang_scan.py` — over the diff and any drafted text.
3. **Generate** the review. Read the grounding first and reference it; do not
   re-derive it. Add only what the tools cannot settle: swallowed errors, contract
   drift, hidden coupling/concurrency, minimum-functional violations, and (for
   geoscience) risk-pattern framing. For any "this is dead code" claim, cite the
   proof (not collected by discovery, unreferenced) — do not assert it.
4. **Critic + verdict.** Apply [rubric.md](rubric.md). Any blocker → **changes
   requested**. A clean run → **approve**, with the evidence attached.
5. **Output.** A review with a deterministic-findings section and a semantic
   section. If a PR body is needed, follow [pr-authoring.md](pr-authoring.md).

For evaluating a reported issue rather than a PR: treat the issue as the
hypothesis, resolve the relevant code/branch, and either review the suspected
change or run the Experiment phase to confirm/refute it against data.

## Provenance

Emit an event at each step with `provenance.py` (plan, ground, generate, critic,
revise, decide). The record is append-only JSON, carries the evidence, and never
contains secrets. The Document phase generates pages from it.

## Escalation

Stop and hand back to a human — with the evidence and a recommendation — when a
blocker cannot be resolved, access still fails after the full preflight, a
conclusion would exceed the evidence, or an outward action needs approval. Do not
fabricate a pass.
