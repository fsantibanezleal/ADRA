# ADR-0006 — Documentation is generated from provenance

**Status:** Accepted

## Context
Documentation written from memory drifts from what actually shipped. Change history
was shallow: hard to answer *why* a change was made and *on what evidence*.

## Decision
- Documentation is **generated from the run record** (provenance), not authored from
  memory; pages cite evidence files and **commit-pinned** links (`?version=GC<sha>`).
- Change history has layers: a **PR change-control page** per merged PR, an
  **experiment page** per experiment, and a **methodology-history** that records only
  **architectural milestones** (contract / persistence / strategy / input changes).
- A **source-of-truth gap table** is kept when a change makes existing docs stale.
- Pages are **English, third person, no AI-session leak** (see `conventions.md`).

## Consequences
- Docs stay aligned with reality and are auditable.
