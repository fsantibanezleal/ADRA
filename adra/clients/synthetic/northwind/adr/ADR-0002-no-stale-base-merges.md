# ADR-0002 — No stale-base merges (merge-base health)

**Status:** Accepted

## Context
A pull request whose branch is based on an outdated `main` can, on merge, silently
revert or delete work that landed in the meantime — including notebooks and bundle
resources — because its diff is computed against an old base.

## Decision
- Every PR is checked for **merge-base health**: compute the merge-base and the
  number of commits the branch is **behind** `main`.
- A branch behind a fresh `main` must be **rebased or recreated** before review.
- The diff against the merge-base is scanned for the destructive signature:
  **file deletions** and **resource renames** (see `ADR-0003`). Both are blocking
  until explicitly confirmed.

## Consequences
- Destructive merges are caught before they land.
- See `cases/CASE-2024-031`.
