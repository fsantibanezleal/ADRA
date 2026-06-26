# ADR-0004 — Test discovery is `test*.py`; product logic must be importable

**Status:** Accepted

## Context
`ndp-ci` runs `unittest discover -s databricks -p "test*.py"` under coverage. Two
failure modes recur: test files that do not match the discovery pattern, and product
logic that lives only inside notebooks (excluded from coverage and not importable).

## Decision
- Test files **must match `test*.py`** (prefix). A `*_test.py` (suffix) file is never
  collected — it is dead code and must be renamed or removed.
- A test directory must contain `__init__.py` to be recursed into.
- Product logic that needs coverage must live in **importable, non-notebook** modules
  (plain `.py` outside `tests/`).
- `Ran 0 tests` / "No data was collected" is a **blocking** CI failure.

## Consequences
- Coverage measures real product code.
- See `cases/CASE-2024-047`.
