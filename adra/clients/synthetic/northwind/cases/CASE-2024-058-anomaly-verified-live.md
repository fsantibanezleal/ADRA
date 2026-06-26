# CASE-2024-058 — Column-coverage anomaly traced to a config typo (verified live)

**Domain:** `orders` · **Relates to:** ADR-0001

## What happened
An orders-pipeline verification flagged 2 of 41 expected source columns as "missing"
from the refined stream. The tempting conclusion was "the source is incomplete".

## Diagnosis (second method)
A probe against the live table (~130M rows, last 7 days) showed 39/41 columns present
and the 2 "missing" ones used a malformed literal (absent for those two
columns) — a **config typo**, not missing data. The conclusion was only made *after*
the rows confirmed it.

## Fix / rule
Corrected the column literals. Codified ADR-0001: conclude from a second-method proof,
record confirmed vs discarded with numbers — never assert from the symptom.
