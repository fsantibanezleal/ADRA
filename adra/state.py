"""Domain model for ADRA — the typed contracts shared across the package.

Everything an orchestrated run produces is expressed with these dataclasses, and
they are all JSON-serializable so a full run can be replayed and audited (the
"evidence layer" of the change-history chain):

- :class:`Severity` / :class:`Finding` — one reviewable issue, grounded in evidence.
- :class:`ToolResult` — the uniform return type of every deterministic tool
  (findings + raw evidence). Tools never return bare dicts; the critic and the
  skills consume :class:`Finding` objects, not loosely-shaped dictionaries.
- :class:`CriticVerdict` — the outcome of one adversarial-critic pass.
- :class:`RunState` — the mutable state threaded through the orchestrator graph.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Finding severity, ordered most-to-least serious."""

    BLOCKER = "blocker"
    MAJOR = "major"
    MINOR = "minor"
    NIT = "nit"

    @property
    def is_blocking(self) -> bool:
        """True for severities that must stop acceptance (blocker / major)."""
        return self in (Severity.BLOCKER, Severity.MAJOR)


@dataclass
class Finding:
    """A single reviewable issue.

    Attributes:
        severity: How serious the issue is (see :class:`Severity`).
        category: Stable machine label, e.g. ``"merge-base"``, ``"language"``.
        message: Human-readable description of the problem.
        location: ``"path/to/file.py:42"`` when the issue maps to a place.
        evidence: The second-method proof backing the claim (tool output, counts).
        suggested_fix: Concrete remediation, when known.
        source: Where the finding came from, e.g. a tool name or ``"critic"``.
    """

    severity: Severity
    category: str
    message: str
    location: str = ""
    evidence: str = ""
    suggested_fix: str = ""
    source: str = ""

    @property
    def is_blocking(self) -> bool:
        """True when this finding must block acceptance."""
        return self.severity.is_blocking

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["severity"] = self.severity.value
        return d


def finding(severity: Severity, category: str, message: str, **kw: Any) -> Finding:
    """Convenience factory for :class:`Finding` (keeps tool code terse)."""
    return Finding(severity=severity, category=category, message=message, **kw)


@dataclass
class ToolResult:
    """Uniform result of a deterministic tool.

    A tool reports *findings* (typed issues) and *data* (raw evidence such as row
    counts or command output). Both feed the LLM as grounding and are persisted to
    the provenance record.

    Attributes:
        tool: Tool identifier, e.g. ``"merge_base_health"``.
        ran: Whether the tool actually executed (False in dry-run / missing dep).
        findings: Issues discovered, as :class:`Finding` objects.
        data: Raw evidence (JSON-serializable scalars / lists).
        reason: Why the tool did not run, when ``ran`` is False.
    """

    tool: str
    ran: bool = True
    findings: list[Finding] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    @property
    def blocking(self) -> list[Finding]:
        """The subset of findings that must block acceptance."""
        return [f for f in self.findings if f.is_blocking]

    @property
    def clean(self) -> bool:
        """True when there are no blocking findings."""
        return not self.blocking

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "ran": self.ran,
            "reason": self.reason,
            "findings": [f.to_dict() for f in self.findings],
            "data": self.data,
        }

    def log_dict(self) -> dict[str, Any]:
        """Compact view for the provenance log (list values are summarized)."""
        data = {k: (f"<{len(v)} items>" if isinstance(v, (list, tuple)) else v)
                for k, v in self.data.items()}
        return {"tool": self.tool, "ran": self.ran, "reason": self.reason,
                "findings": [f.to_dict() for f in self.findings], "data": data}


@dataclass
class CriticVerdict:
    """Result of one adversarial-critic pass over a draft artifact."""

    clean: bool
    blocking: list[Finding] = field(default_factory=list)
    attacks_tried: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def messages(self) -> list[str]:
        """Human-readable blocking messages (for CLIs / logs / tests)."""
        return [f.message for f in self.blocking]

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "blocking": [f.to_dict() for f in self.blocking],
            "attacks_tried": self.attacks_tried,
            "notes": self.notes,
        }


@dataclass
class RunState:
    """Mutable state threaded through the orchestrator graph for one run."""

    skill: str
    intake: dict[str, Any]
    plan: dict[str, Any] = field(default_factory=dict)
    grounding: dict[str, ToolResult] = field(default_factory=dict)
    draft: Any = None
    findings: list[Finding] = field(default_factory=list)
    critic_history: list[CriticVerdict] = field(default_factory=list)
    rounds: int = 0
    decision: str = "pending"  # "accepted" | "escalate" | "pending"
    artifacts: dict[str, str] = field(default_factory=dict)

    def grounding_findings(self) -> list[Finding]:
        """All findings produced by the deterministic grounding tools, flattened."""
        return [f for r in self.grounding.values() for f in r.findings]

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill": self.skill,
            "intake": self.intake,
            "plan": self.plan,
            "grounding": {k: v.to_dict() for k, v in self.grounding.items()},
            "draft": self.draft,
            "findings": [f.to_dict() for f in self.findings],
            "critic_history": [v.to_dict() for v in self.critic_history],
            "rounds": self.rounds,
            "decision": self.decision,
            "artifacts": self.artifacts,
        }
