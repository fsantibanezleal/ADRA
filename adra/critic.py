"""The adversarial critic (blocking).

The formalization of "don't infer — diagnose". The critic *attacks* the draft, not
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
        ``(findings, notes)`` — findings are MAJOR semantic issues the model raised.
    """
    user = (
        "Adversarially review this draft against the criteria. Try to BREAK it. "
        "Return JSON {clean: bool, blocking: [str], notes: str}.\n\n"
        f"SKILL: {state.skill}\nGROUNDING: {state.to_dict()['grounding']}\nDRAFT: {state.draft}")
    data = parse_json(invoke_text(model, system, user, node=Node.CRITIC))
    findings = [finding(Severity.MAJOR, "semantic", str(msg), source="critic-llm")
                for msg in data.get("blocking", [])]
    return findings, str(data.get("notes", ""))


def criticize(model: ChatModel, state: RunState) -> CriticVerdict:
    """Full critic pass: deterministic rubric (hard floor) + LLM semantic attacks.

    Args:
        model: The chat model for the semantic pass.
        state: The current run state (grounding already executed).

    Returns:
        A :class:`~adra.state.CriticVerdict`; ``clean`` is True only when no blocking
        finding survives. Findings are deduped by (category, message).
    """
    system = _system(state.skill)
    llm_findings, notes = llm_critique(model, system, state)
    seen: set[tuple[str, str]] = set()
    blocking: list[Finding] = []
    for f in deterministic_attacks(state) + llm_findings:
        key = (f.category, f.message)
        if key not in seen:
            seen.add(key)
            blocking.append(f)
    attacks = [it.id for it in rubric.for_skill(state.skill)]
    return CriticVerdict(clean=not blocking, blocking=blocking, attacks_tried=attacks, notes=notes)
