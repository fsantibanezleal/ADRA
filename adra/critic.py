"""The adversarial critic (blocking).

The formalization of "don't infer, diagnose". The critic *attacks* the draft, not
approves it. It runs a deterministic red-team pass first (the hard floor), then an
LLM pass for the semantic criteria. Both passes are driven by the **same shared
rubric** (:mod:`adra.rubric`), so "what we check" never diverges between code and
prompt. The critic's role prompt is externalized (`prompts/critic.md`).
"""

from __future__ import annotations

import re

from adra import rubric
from adra.llm import ChatModel, invoke_text
from adra.nodes import Node
from adra.state import CriticVerdict, Finding, RunState, Severity, finding
from adra.tools import lang_tools
from adra.utils import load_prompt, parse_json

# Phrases that assert a cause/outcome without evidence -> demand a second method.
_UNVERIFIED_RE = re.compile(
    r"\b(probably|i assume|likely|should be fine|seems? to|no access|can'?t read|"
    r"must be because|that'?s because)\b", re.IGNORECASE)


def _draft_text(state: RunState) -> str:
    """Flatten the current draft (str or structured) to searchable text."""
    draft = state.draft
    if isinstance(draft, dict):
        return " ".join(str(v) for v in draft.values())
    return str(draft or "")


def deterministic_attacks(state: RunState) -> list[Finding]:
    """Run the deterministic red-team pass over draft + grounding (the hard floor).

    Combines (a) blocking findings already raised by the grounding tools and (b) the
    critic-level rubric checks that need the draft text or the skill context. Every
    finding's text comes from the shared rubric, so messages are single-sourced.

    Returns:
        Blocking :class:`~adra.state.Finding` objects; empty means the pass cleared.
    """
    blocking: list[Finding] = []

    # (a) Unresolved blocking findings from the deterministic tools.
    for result in state.grounding.values():
        blocking.extend(result.blocking)

    text = _draft_text(state)

    # (b) Critic-level rubric checks.
    if _UNVERIFIED_RE.search(text):
        m = _UNVERIFIED_RE.search(text)
        blocking.append(rubric.get("unverified_claim").to_finding(evidence=f"'{m.group(0)}'"))

    if state.skill in ("code_review", "pr_eval"):
        ci = state.grounding.get("ci_command")
        if ci is None or not ci.ran:
            blocking.append(rubric.get("exact_ci_repro").to_finding(evidence="CI not reproduced (dry-run)"))

    if "no access" in text.lower() or "permission denied" in text.lower():
        # Probes are stored per-hypothesis (probe_01, probe_02, …), so scan all grounding
        # for any SQL probe that carries a preflight checklist but returned no rows.
        for res in state.grounding.values():
            if res.tool == "sql_probe" and not res.data.get("rows") and "preflight" in res.data:
                blocking.append(rubric.get("unverifiable_no_access").to_finding())
                break

    # Language + AI-session-leak scan over the draft text itself.
    blocking.extend(lang_tools.scan_language(text).blocking)
    return blocking


def _system(skill: str) -> str:
    """Build the critic system prompt: the externalized role + the skill's rubric."""
    base = load_prompt("critic") or "You are an adversarial reviewer. Break the draft."
    return f"{base}\n\n## Criteria for `{skill}` (the rubric)\n{rubric.prompt_block(skill)}"


def llm_critique(model: ChatModel, system: str, state: RunState) -> tuple[list[Finding], str]:
    """Ask the model for semantic attacks the deterministic pass cannot encode.

    Returns:
        ``(findings, notes)``: findings are MAJOR semantic issues the model raised.
    """
    user = (
        "Adversarially review this draft against the criteria. Try to BREAK it. "
        "Return JSON {clean: bool, blocking: [str], notes: str}.\n\n"
        f"SKILL: {state.skill}\nGROUNDING: {state.to_dict()['grounding']}\nDRAFT: {state.draft}")
    data = parse_json(invoke_text(model, system, user, node=Node.CRITIC))
    findings = [finding(Severity.MAJOR, "semantic", str(msg), source="critic-llm")
                for msg in data.get("blocking", [])]
    return findings, str(data.get("notes", ""))


_SEVERITY_RANK = {Severity.BLOCKER: 0, Severity.MAJOR: 1, Severity.MINOR: 2, Severity.NIT: 3}


def _rank(findings: list[Finding]) -> list[Finding]:
    """Order findings most-severe first (stable within a severity)."""
    return sorted(findings, key=lambda f: _SEVERITY_RANK.get(f.severity, 9))


def _dedupe(findings: list[Finding]) -> list[Finding]:
    """Drop duplicates by (category, message), preserving order."""
    seen: set[tuple[str, str]] = set()
    out: list[Finding] = []
    for f in findings:
        key = (f.category, f.message)
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def refute_candidates(refuter: ChatModel, state: RunState,
                      candidates: list[Finding]) -> list[Finding]:
    """Refutation gate (the "kill mandate"): try to DISPROVE each semantic candidate.

    For every candidate finding the refuter is asked to prove it false, already
    handled, or unsupported by the evidence; only candidates it CANNOT refute survive.
    This trades a little recall for precision (LLMs optimize plausibility, not
    correctness), following the Refute-or-Promote pattern. Pair it with a cross-family
    refuter (``ADRA_MODEL_REFUTE``) to catch correlated blind spots. Deterministic
    findings never reach here: the hard floor is ground truth and is never re-litigated.

    Returns:
        The surviving (non-refuted) findings, in their original order.
    """
    if not candidates:
        return candidates
    system = load_prompt("refute") or (
        "You are a refuter. Try to DISPROVE the candidate finding. It survives only if "
        "it cannot be refuted with an independent second method.")
    survivors: list[Finding] = []
    for f in candidates:
        user = (
            "Try to REFUTE this candidate finding. Return JSON {refuted: bool, reason: str}. "
            "It is refuted only if it is false, already handled, or unsupported by the "
            "evidence in the grounding/draft.\n\n"
            f"SKILL: {state.skill}\nGROUNDING: {state.to_dict()['grounding']}\n"
            f"DRAFT: {state.draft}\nCANDIDATE: {f.message}")
        data = parse_json(invoke_text(refuter, system, user, node=Node.CRITIC))
        if not bool(data.get("refuted", False)):
            survivors.append(f)
    return survivors


def criticize(model: ChatModel, state: RunState, settings=None,
              refuter: ChatModel | None = None) -> CriticVerdict:
    """Full critic pass: deterministic rubric (hard floor) + LLM semantic attacks,
    optionally aggregated over several passes and filtered by a refutation gate.

    Args:
        model: The chat model for the semantic pass.
        state: The current run state (grounding already executed).
        settings: Optional run settings. When given, ``critic_runs`` aggregates that
            many independent semantic passes (self-consistency, higher recall) and
            ``refute`` enables the refutation gate (higher precision). When omitted,
            behaves as a single semantic pass (backward compatible).
        refuter: Optional chat model for the refutation gate; defaults to ``model``.
            Set a different family (``ADRA_MODEL_REFUTE``) for the Cross-Model Critic.

    Returns:
        A :class:`~adra.state.CriticVerdict`; ``clean`` is True only when no finding
        survives. Findings are deduped by (category, message) and ranked most-severe first.
    """
    system = _system(state.skill)
    runs = max(1, getattr(settings, "critic_runs", 1)) if settings is not None else 1

    # Semantic candidates, optionally aggregated over independent passes (recall).
    semantic: list[Finding] = []
    notes_parts: list[str] = []
    for _ in range(runs):
        found, notes = llm_critique(model, system, state)
        semantic.extend(found)
        if notes:
            notes_parts.append(notes)
    semantic = _dedupe(semantic)

    # Refutation gate over the SEMANTIC candidates only (precision); the deterministic
    # hard floor is never refuted. Skipped offline (mock) where refutation is a no-op.
    if (settings is not None and getattr(settings, "refute", False)
            and getattr(settings, "provider", "mock") != "mock"):
        semantic = refute_candidates(refuter or model, state, semantic)

    blocking = _rank(_dedupe(deterministic_attacks(state) + semantic))
    attacks = [it.id for it in rubric.for_skill(state.skill)]
    return CriticVerdict(clean=not blocking, blocking=blocking,
                         attacks_tried=attacks, notes=" ".join(notes_parts))
