# ADR-0007 — Decision-support outputs avoid overclaiming

**Status:** Accepted

## Context
`analytics` products are decision support: demand and risk forecasts, anomaly scores,
prioritization. Language that claims a model "detects", "predicts", "guarantees" or
"prevents" an outcome overstates what the model does and creates liability exposure when
the outcome differs from the claim.

## Decision
- `analytics` / decision-support outputs are framed as **likelihoods, risk scores and
  recommendations** that carry their evidence — never as guaranteed detection or prediction.
- Documentation, code comments, UI strings and PR text use non-overclaiming framing.
- The high-consequence decision stays **human-owned**; the model prepares the evidence.

## Consequences
- Claims match what the models actually do (calibration honesty).
- The `overclaim_language` rubric item flags violations on any decision-support deliverable.
