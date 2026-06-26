# Architecture

ADRA is a small, **explicit, framework-free state machine** (no LangChain / LangGraph / agent
runtime) built on three layered ideas: **deterministic-first grounding**, an **adversarial
generate → critic → revise loop**, and an **immutable provenance record**. The LLM is reached
through a tiny ADRA-owned `ChatModel` seam (`adra/llm.py`); the loop itself is plain, readable
Python (`adra/orchestrator.py`) whose node contracts stay stable even if it is ever wrapped.

This folder is the deep architecture wiki. Read it in order, or jump to the page you need.

## Read in order

1. [01_overview.md](./01_overview.md) — the orchestrated loop (`plan → ground → generate →
   CRITIC → revise* → decide`), why a hand-rolled state machine, and the one-screen mental
   model.
2. [02_layered-design.md](./02_layered-design.md) — the three layers (deterministic floor ·
   adversarial loop · provenance) and the module map: how `state` / `rubric` / `tools` /
   `skills` / `critic` / `judge` / `orchestrator` / `provenance` interrelate.
3. [03_data-flow.md](./03_data-flow.md) — what crosses each boundary: the single typed contract
   (`ToolResult` / `Finding` / `CriticVerdict` / `RunState`), grounding-as-evidence, and how
   the offline mock stays honest.
4. [04_run-sequence.md](./04_run-sequence.md) — a `pr_eval` run step by step, from intake to the
   written `RunRecord`, including the decision branch (`accepted` vs `escalate`).
5. [05_why-deterministic-first.md](./05_why-deterministic-first.md) — the theory: why the
   deterministic floor carries the verdict, the failure modes it closes (hallucination, reward
   hacking), and what that buys (offline, evidence-backed, auditable).

## One-screen architecture

![ADRA adversarial loop](../images/loop.svg)

The critic is **mandatory and blocking**: an artifact is `accepted` only when the critic is
clean; otherwise it revises up to `max_rounds` and then **escalates to a human** — it never
silently approves.

## The module map

![Module interrelations](../images/module_map.svg)

Everything flows through one typed contract (`adra/state.py`): tools and skills return
`ToolResult` / `Finding`; the critic returns a `CriticVerdict`; the orchestrator threads a
`RunState` and writes a `RunRecord`.

## What this layer IS and is NOT

- **IS** a readable, auditable orchestration of a fixed pipeline with a hard, evidence-backed
  floor. The graph is small enough to read in one sitting (`orchestrator.run` is ~45 lines).
- **IS NOT** a general-purpose agent runtime, a planner that invents arbitrary tool sequences,
  or a multi-agent debate system. The node set is fixed (`adra/nodes.py`); skills differ only
  by prompt + grounding tools.

## See also

- [../README.md](../README.md) — documentation index.
- [methodologies/](../methodologies/methodologies.md) — the *why* behind the loop (adversarial
  validation, the rubric, the judge, escalation).
- [data-contract/](../data-contract/data-contract.md) — the exact shapes of every artifact that
  crosses a boundary here.
- [adr/](../adr/README.md) — ADR-0001 (deterministic-first), ADR-0002 (hand-rolled
  orchestrator), ADR-0005 (blocking critic), ADR-0006 (provenance).
