"""ADRA — Adversarial Dev Review Agent.

A client-agnostic, deterministic-first, adversarial-validation engine that supports the
software lifecycle. It formalizes six capabilities a team runs informally under
adversarial human direction:

    code_review | pr_eval | experiment | improve | document | decide

The design spine is *adversarial validation*: every generated artifact is passed through
a blocking, tool-grounded adversarial critic before it is accepted, and every run emits
an immutable provenance record (the deep change history). Deterministic tools
(git / CI / SQL / static analysis) are ground truth; the LLM only adds what tools cannot
settle. Connectors (GitHub / Azure DevOps / Databricks / Azure) and a self-contained
offline emulator sit behind one Protocol, so the same engine runs against a real
platform or a synthetic one.

The package runs offline with a deterministic ``mock`` provider (no API key required)
and switches to a real provider (e.g. Anthropic Claude) when its key is present.
"""

from adra.config import Settings, load_settings
from adra.orchestrator import Orchestrator
from adra.state import CriticVerdict, Finding, RunState, Severity, ToolResult

__all__ = [
    "Settings",
    "load_settings",
    "Orchestrator",
    "Finding",
    "Severity",
    "ToolResult",
    "CriticVerdict",
    "RunState",
]

__version__ = "0.3.0"  # PEP 440 package version; display/tag version is v0.03.000 (see VERSION)
