"""The adversarial rubric — a single, shared source of truth for the criteria.

Each :class:`RubricItem` is a concrete adversarial check, learned from a real
incident in our history. The rubric is consumed in two places so the "what we
check" never diverges between code and prompts:

- :func:`deterministic_findings` — the items whose ``kind == "deterministic"`` are
  enforced mechanically by the critic (the hard floor).
- :func:`prompt_block` — the items applicable to a skill are rendered into the
  critic's system prompt, so the LLM pass attacks the *same* criteria.

``applies_to`` is empty for cross-cutting items (they apply to every skill).
"""

from __future__ import annotations

from dataclasses import dataclass

from adra.state import Finding, Severity, finding


@dataclass(frozen=True)
class RubricItem:
    """One adversarial criterion.

    Attributes:
        id: Stable identifier, e.g. ``"stale_merge_base"``.
        title: Short label.
        severity: How serious a violation is.
        category: Machine label shared with :class:`~adra.state.Finding`.
        kind: ``"deterministic"`` (a tool or the critic settles it) or
            ``"semantic"`` (the LLM critic must judge it).
        applies_to: Skills this item applies to; empty tuple == all skills.
        method: How to check it — the operational depth, also shown to the LLM.
        incident: The real case it was learned from.
    """

    id: str
    title: str
    severity: Severity
    category: str
    kind: str
    applies_to: tuple[str, ...]
    method: str
    incident: str

    def to_finding(self, evidence: str = "", source: str = "critic") -> Finding:
        return finding(self.severity, self.category, f"{self.title}: {self.method}",
                       evidence=evidence, source=source)


RUBRIC: tuple[RubricItem, ...] = (
    RubricItem(
        "stale_merge_base", "Stale merge-base", Severity.MAJOR, "merge-base",
        "deterministic", ("pr_eval",),
        "Compute the merge-base and commits-behind vs `main`; a branch behind a fresh "
        "`main` must be rebased/recreated before review.",
        "CASE-2024-031 — a stale-base PR dropped a notebook and bundle resources (ADR-0002)."),
    RubricItem(
        "destructive_deletions", "Hidden deletions", Severity.BLOCKER, "destructive",
        "deterministic", ("pr_eval", "code_review"),
        "Every file deletion in the diff must be explicitly intended; stale-base diffs "
        "silently remove notebooks / resources.",
        "CASE-2024-031 — an unintended notebook deletion via a stale-base diff (ADR-0002)."),
    RubricItem(
        "dropped_bundle_resource", "Dropped bundle resource", Severity.BLOCKER, "bundle",
        "deterministic", ("pr_eval",),
        "Renames away from `.yml` (e.g. `.yml.t`) drop a resource from the DAB bundle; "
        "schemas / volumes / jobs must stay `.yml`.",
        "CASE-2024-031 — resources renamed to .yml.t left the bundle (ADR-0003)."),
    RubricItem(
        "bundle_validate", "Bundle validation", Severity.BLOCKER, "bundle",
        "deterministic", ("pr_eval",),
        "Validate with the build's own tool: `databricks bundle validate -t <env>` "
        "must return Validation OK.",
        "ADR-0003 / ci-standards — bundle changes must pass `bundle validate`."),
    RubricItem(
        "exact_ci_repro", "Exact CI command reproduced", Severity.MAJOR, "ci",
        "deterministic", ("code_review", "pr_eval"),
        "A 'green' verdict requires reproducing the exact CI command, not an "
        "approximation; otherwise the build state is unverified.",
        "CASE-2024-047 — a coverage failure understood only by running the exact CI command (ADR-0001)."),
    RubricItem(
        "zero_tests_no_data", "Zero tests / no coverage data", Severity.BLOCKER, "coverage",
        "deterministic", ("code_review",),
        "0 collected tests makes coverage report no data; product logic must be "
        "importable (non-notebook) and exercised by a discoverable test.",
        "CASE-2024-047 — `unittest discover` collected 0 tests → coverage exit 1 (ADR-0004)."),
    RubricItem(
        "test_discoverability", "Test discoverability", Severity.MAJOR, "ci",
        "deterministic", ("code_review",),
        "Test files must match the CI discovery pattern (`test*.py` prefix); a "
        "`*_test.py` suffix file is never collected and is dead code.",
        "CASE-2024-047 — a `*_test.py` suffix file was never collected (ADR-0004)."),
    RubricItem(
        "unverified_claim", "Claim without a second method", Severity.MAJOR, "unverified",
        "deterministic", (),
        "Don't infer — diagnose: a cause or outcome asserted without a second-method "
        "proof is rejected; verify with an independent method or say 'unknown'.",
        "ADR-0001 — causes asserted without a second-method proof."),
    RubricItem(
        "unverifiable_no_access", "Unverifiable 'no access'", Severity.MAJOR, "access",
        "deterministic", ("experiment",),
        "Never declare 'no access' to a catalog without exhausting the 6-point "
        "profile / warehouse / grants preflight.",
        "CASE-2024-052 — 'no access' concluded on a profile/env mismatch (ADR-0005)."),
    RubricItem(
        "conclusion_beyond_evidence", "Conclusion beyond the evidence", Severity.MAJOR,
        "evidence", "semantic", ("experiment",),
        "Conclude only what the probe rows support; if a conclusion needs live data "
        "you do not have, say so explicitly and stop. Record discarded hypotheses too.",
        "CASE-2024-058 — a 'missing data' claim was a config typo, found only on live verification (ADR-0001)."),
    RubricItem(
        "convention_conformance", "Convention conformance", Severity.MAJOR, "conformance",
        "semantic", ("pr_eval", "improve"),
        "A change is defensible only against an existing repo convention or a measured "
        "gap; cite a concrete precedent already present in the repo.",
        "CASE-2024-061 — a cadence change justified against an existing precedent (ADR-0008)."),
    RubricItem(
        "contract_drift", "Contract drift", Severity.MAJOR, "contract",
        "semantic", ("code_review", "pr_eval"),
        "Flag changes that widen or narrow a public contract — a UC table schema, a "
        "function signature, a job output, a data-contract column.",
        "ADR-0006 — silent schema changes break downstream consumers."),
    RubricItem(
        "swallowed_error", "Swallowed error", Severity.MAJOR, "error-handling",
        "semantic", ("code_review",),
        "Flag silently swallowed exceptions / timeouts / retries that a caller relies "
        "on, and broad excepts that hide failures.",
        "Recurring — swallowed timeouts hide partial pipeline failures."),
    RubricItem(
        "minimum_functional", "Filler beyond minimum-functional", Severity.MINOR,
        "minimum-functional", "semantic", ("improve", "code_review"),
        "Keep only what advances the result; prove removed code is dead (not collected "
        "/ unreferenced) rather than asserting it; prune filler even from a standard.",
        "CASE-2024-047 / ADR-0008 — a dead suffix test file removed once proven uncollected."),
    RubricItem(
        "blast_radius", "Blast radius / reversibility", Severity.MAJOR, "risk",
        "semantic", ("decide", "pr_eval"),
        "Assess blast radius: shared CI templates, cross-domain libraries, prod data, "
        "irreversible ops. Prefer the smallest-scope, reversible route; name the rollback.",
        "CASE-2024-061 — editing shared ndp-ci templates affects every consuming repo (ADR-0008)."),
    RubricItem(
        "language_leak", "Language / AI-session leak", Severity.BLOCKER, "session-leak",
        "deterministic", (),
        "Everything written to disk is English; nothing reveals AI authorship "
        "(no 'Claude', 'co-authored-by', etc.). Scrub before any commit / PR / doc.",
        "conventions.md / ADR-0006 — binding rule; real leaks have occurred."),
    RubricItem(
        "overclaim_language", "Overclaiming decision-support output", Severity.MAJOR, "framing",
        "semantic", ("document", "code_review", "experiment"),
        "Decision-support outputs must not claim to 'detect', 'predict', 'guarantee' or "
        "'prevent' an outcome; frame as likelihood / risk / recommendation with its evidence.",
        "ADR-0007 — outputs are decision support, not guaranteed event detection."),
)

_BY_ID = {item.id: item for item in RUBRIC}


def get(item_id: str) -> RubricItem:
    """Return the rubric item with ``item_id`` (raises KeyError if unknown)."""
    return _BY_ID[item_id]


def for_skill(skill: str, kind: str | None = None) -> list[RubricItem]:
    """Items applicable to ``skill`` (cross-cutting items included).

    Args:
        skill: The skill name.
        kind: Optional filter, ``"deterministic"`` or ``"semantic"``.
    """
    out = [it for it in RUBRIC if not it.applies_to or skill in it.applies_to]
    return [it for it in out if kind is None or it.kind == kind]


def prompt_block(skill: str) -> str:
    """Render the criteria applicable to ``skill`` for injection into a prompt."""
    lines = []
    for it in for_skill(skill):
        tag = "MUST-BLOCK" if it.severity.is_blocking else "FLAG"
        lines.append(f"- [{tag}] {it.title} — {it.method} (learned: {it.incident})")
    return "\n".join(lines)
