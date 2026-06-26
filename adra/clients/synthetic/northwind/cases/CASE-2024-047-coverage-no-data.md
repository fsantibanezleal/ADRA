# CASE-2024-047 — Coverage CI failed with "No data was collected"

**Domain:** `catalog` · **Relates to:** ADR-0004

## What happened
The `catalog` repo's coverage stage exited 1 with `Ran 0 tests` then
`CoverageWarning: No data was collected`. The only test-shaped file was
`py_aux_functions_v3_test.py` (a `*_test.py` **suffix**), which `unittest discover -p
"test*.py"` never collects. The product logic lived inside a notebook (excluded from
coverage, not importable).

## Diagnosis (second method)
Ran the **exact** CI command locally and confirmed 0 collected tests. Cross-checked a
sibling repo whose coverage passed: it had a discoverable `test*.py` exercising an
importable module — proving the difference, not guessing it.

## Fix / rule
Added an importable module + a discoverable `test*.py`; removed the dead suffix file.
Codified as ADR-0004 (discovery pattern + importable logic).
