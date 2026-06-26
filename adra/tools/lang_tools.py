"""Language / session-leak scanner (deterministic).

Enforces two binding rules without an LLM:

- Everything written to disk is English (no Spanish).
- No AI-session leak (no "Claude", "co-authored-by", etc.) in commits / PRs / docs.

These are exactly the checks we already apply by hand; here they are mechanical so
the critic can rely on them as ground truth.
"""

from __future__ import annotations

import re

from adra.state import Severity, ToolResult, finding

# High-signal Spanish markers (function words). Kept conservative to avoid flagging
# Spanish proper nouns embedded in otherwise-English text.
_SPANISH_WORDS = {
    "el", "la", "los", "las", "una", "unos", "unas", "del", "para", "pero",
    "porque", "cuando", "donde", "esto", "esta", "este", "como", "mas", "muy",
    "sin", "con", "sobre", "tambien", "ademas", "segun", "cada", "entre",
    "cambio", "cambios", "archivo", "archivos", "salida", "fuente", "fuentes",
    "validacion", "objetivo", "resumen", "tarea", "tareas",
}
_ACCENTS = re.compile(r"[áéíóúñ¿¡]", re.IGNORECASE)
_LEAK_PATTERNS = [
    re.compile(r"co-?authored-?by", re.IGNORECASE),
    re.compile(r"\bclaude\b", re.IGNORECASE),
    re.compile(r"anthropic", re.IGNORECASE),
    re.compile(r"generated with .*(claude|ai)", re.IGNORECASE),
    re.compile(r"\bas an ai\b", re.IGNORECASE),
]


def scan_language(text: str) -> ToolResult:
    """Scan ``text`` for Spanish content and AI-session-leak markers.

    Args:
        text: The content destined for disk (a diff, PR body, doc, commit message).

    Returns:
        A :class:`~adra.state.ToolResult` with a MAJOR finding for Spanish content
        and a BLOCKER finding for any AI-session leak.
    """
    lowered = text.lower()
    spanish = sorted(w for w in _SPANISH_WORDS
                     if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", lowered))
    accents = bool(_ACCENTS.search(text))
    leaks = sorted({p.pattern for p in _LEAK_PATTERNS if p.search(text)})

    findings = []
    if spanish or accents:
        findings.append(finding(
            Severity.MAJOR, "language",
            "Spanish content detected; the deliverable must be English.",
            evidence=f"markers={spanish} accents={accents}", source="lang_scan"))
    if leaks:
        findings.append(finding(
            Severity.BLOCKER, "session-leak",
            "AI-session leak detected; scrub before any commit / PR.",
            evidence=f"patterns={leaks}", source="lang_scan"))
    return ToolResult(tool="lang_scan", findings=findings,
                      data={"spanish_markers": spanish, "has_accents": accents, "leaks": leaks})
