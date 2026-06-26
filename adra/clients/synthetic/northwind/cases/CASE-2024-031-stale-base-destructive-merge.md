# CASE-2024-031 — Stale-base PR dropped a notebook and bundle resources

**Domain:** `orders` · **Relates to:** ADR-0002, ADR-0003

## What happened
A PR for the orders bundle was opened from a branch based on a `main` that was ~12
commits stale. Because the diff was computed against the old merge-base, the PR:
- deleted `nb-priority-coverage.py` (which had landed on `main` in the meantime), and
- renamed `bundle.resources.schemas.yml` and `…volumes.yml` to `.yml.t`, dropping
  both resources from the bundle.

`databricks bundle validate` would have failed, but it was not run.

## Root cause
Stale merge-base + no destructive-diff review + no bundle validation.

## Fix / rule
Rebuilt the change cleanly on a fresh `main`. Codified as ADR-0002 (merge-base
health + destructive-diff scan) and ADR-0003 (resources stay `.yml`).
