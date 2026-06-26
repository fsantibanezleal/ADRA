# CASE-2024-061 — Choosing a route by blast radius and precedent

**Domain:** `catalog` · **Relates to:** ADR-0008

## What happened
A catalog refresh trigger needed a higher cadence. Two routes were on the table:
(a) edit the **shared `ndp-ci` trigger template** (touches every consuming repo), or
(b) change the cadence **in the catalog repo's own trigger**, matching an existing
precedent already present for a sibling trigger.

## Decision
Route (b) was chosen: smaller **blast radius**, reversible, and **justified against a
precedent** in the same repo (a sibling trigger already ran at the target cadence).
Route (a) was recorded as discarded with its trade-off (broad blast radius).

## Fix / rule
Codified ADR-0008: prefer the smallest reversible route; justify against convention
or a measured gap; assess blast radius explicitly.
