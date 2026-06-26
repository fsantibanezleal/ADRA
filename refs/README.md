# ADRA — references (annotated bibliography)

The research base for ADRA, grouped by the agent's pillars. Each entry notes **why
it matters for ADRA**. A small set of core papers is kept locally in
[`papers/`](papers/) (short filenames, shown as `→ papers/<file>`); the rest are
cited with their public links. Full machine-readable citations are in
[`references.bib`](references.bib).

> Local PDFs are third-party academic works kept for internal reading only.

---

## 1. Agent foundations — the reason-act loop

- **ReAct: Synergizing Reasoning and Acting in Language Models** — Yao et al., 2023
  (`arXiv:2210.03629`). → `papers/react-reason-act.pdf`. The interleaved
  reason→act→observe pattern under ADRA's `plan → ground → generate`.
- **A Survey on LLM-based Autonomous Agents** — Wang et al., 2024
  (`arXiv:2308.11432`). → `papers/survey-llm-agents.pdf`. Planning / memory / tool-use
  taxonomy framing the orchestrator + skills.
- **Toolformer** — Schick et al., 2023 (`arXiv:2302.04761`). Tool-use as a
  first-class capability (the deterministic tools).

## 2. Adversarial validation — generator / critic / judge

- **Reflexion: Language Agents with Verbal Reinforcement Learning** — Shinn et al.,
  2023 (`arXiv:2303.11366`). Tool-grounded self-critique → the generate→critic→revise loop.
- **Self-Refine: Iterative Refinement with Self-Feedback** — Madaan et al., 2023
  (`arXiv:2303.17651`). The revise loop and its limits.
- **Constitutional AI** — Bai et al., 2022 (`arXiv:2212.08073`). Critiquing against an
  explicit written set of principles — inspiration for ADRA's shared rubric.
- **Improving Factuality via Multi-Agent Debate** — Du et al., 2023
  (`arXiv:2305.14325`). Adversarial cross-examination.
- **Spontaneous Reward Hacking in Iterative Self-Refinement** — (`arXiv:2407.04549`).
  *Why the critic must be tool-grounded:* ungrounded self-refinement games its reward.

## 3. The judge — LLM-as-a-judge and its biases

- **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena** — Zheng et al., 2023
  (`arXiv:2306.05685`). → `papers/llm-as-judge-mtbench.pdf`. Defines position /
  verbosity / self-preference bias → swap-and-average + reference anchoring.
- **Position Bias in Rubric-Based LLM-as-a-Judge** — (`arXiv:2602.02219`). Rubric
  ordering induces bias; mitigations the judge applies.

## 4. Grounding — "don't infer, diagnose"

- **Why Language Models Hallucinate** — Kalai et al., 2025 (`arXiv:2509.04664`).
  → `papers/why-llms-hallucinate.pdf`. The statistical case for the deterministic
  floor + "verify or say unknown".
- **Calibrated Language Models Must Hallucinate** — Kalai & Vempala, 2023
  (`arXiv:2311.14648`). Hallucination is intrinsic → tool grounding is non-optional.
- **A Survey on Hallucination in LLMs** — Huang et al., 2023 (`arXiv:2311.05232`).

## 5. Guardrails — agent safety & risk

- **Identifying the Risks of LM Agents with an LM-Emulated Sandbox (ToolEmu)** — Ruan
  et al., 2023 (`arXiv:2309.15817`). → `papers/agent-risks-sandbox.pdf`. Why writes
  are dry-run by default and high-impact actions are gated.
- **NIST AI RMF — Generative AI Profile (AI 600-1)** — NIST, 2024.
  → `papers/nist-ai-rmf-genai.pdf`. Govern / map / measure / manage.
- **Compromising Real-World LLM-Integrated Apps with Indirect Prompt Injection** —
  Greshake et al., 2023 (`arXiv:2302.12173`). Untrusted content as an attack surface.
- **OWASP Top 10 for LLM Applications (2025)** and **Top 10 for Agentic Applications
  (Dec 2025)**. The red-team threat catalog behind the rubric.

## 6. Governance, provenance & decision support

- **Closing the AI Accountability Gap: Internal Algorithmic Auditing** — Raji et al.,
  2020 (`arXiv:2001.00973`). → `papers/internal-algorithmic-auditing.pdf`. The
  end-to-end audit trail = ADRA's provenance + change-history layers.
- **Model Cards for Model Reporting** — Mitchell et al., 2019 (`arXiv:1810.03993`).
  → `papers/model-cards.pdf`. Structured, evidence-linked documentation from facts.
- **Stop Explaining Black Box Models for High-Stakes Decisions** — Rudin, 2019
  (`arXiv:1811.10154`). → `papers/interpretable-models-highstakes.pdf`. The
  decision-support, never event-detection framing (ADR-0007).
- **Datasheets for Datasets** — Gebru et al., 2018 (`arXiv:1803.09010`).

## 7. Evaluation, evidence & minimum-functional

- **Leakage and the Reproducibility Crisis in ML-based Science** — Kapoor &
  Narayanan, 2023 (`arXiv:2207.07048`). → `papers/leakage-reproducibility.pdf`.
  Reproduce the exact thing; conclude only what the evidence supports.
- **Reporting Standards for ML-Based Science** — Kapoor et al., 2024
  (`arXiv:2308.07832`). Checklists behind the experiment artifact.

## 8. Code-review & SWE agents (application domain)

- **SWE-bench** — Jimenez et al., 2024 (`arXiv:2310.06770`); **SWE-agent** — Yang et
  al., 2024 (`arXiv:2405.15793`). Agent–computer interface for repo-scale tasks.
- **Sphinx: Benchmarking & Modeling for LLM-Driven Pull-Request Review** —
  (`arXiv:2601.04252`).
- **From Industry Claims to Empirical Reality: Code-Review Agents in PRs** —
  (`arXiv:2604.03196`). Empirical limits → deterministic-first + human gate.
