"""Provenance: the immutable run record (deep change history, evidence layer).

Every orchestrator step appends a timestamped event. On close, the full record is
written to ``runs/<run_id>.json``. Downstream, the ``document`` skill turns this
record into a PR doc / experiment page / methodology-history row, so the technical,
operational and functional history all trace back to one auditable artifact.

Reference: lineage (the journey) + provenance (origin/who/how/when) joined with
git for code/config, per current ML-governance practice (see wip research §E).
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RunRecord:
    """Append-only record of one ADRA run."""

    skill: str
    intake: dict[str, Any]
    run_id: str = field(default_factory=lambda: time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
    started_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    provider: str = "mock"
    model: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    final_decision: str = "pending"
    artifacts: dict[str, str] = field(default_factory=dict)

    def event(self, node: str, kind: str, payload: dict[str, Any] | None = None) -> None:
        """Append one step event (node = graph node, kind = generate/ground/critic/...)."""
        self.steps.append(
            {
                "t": time.strftime("%H:%M:%S"),
                "node": node,
                "kind": kind,
                "payload": payload or {},
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "skill": self.skill,
            "started_at": self.started_at,
            "provider": self.provider,
            "model": self.model,
            "intake": self.intake,
            "steps": self.steps,
            "final_decision": self.final_decision,
            "artifacts": self.artifacts,
        }

    def write(self, runs_dir: Path) -> Path:
        runs_dir.mkdir(parents=True, exist_ok=True)
        path = runs_dir / f"{self.run_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=True), encoding="utf-8")
        return path

    def summary(self) -> str:
        """One-line human summary for CLIs."""
        critics = [s for s in self.steps if s["kind"] == "critic"]
        last = critics[-1]["payload"] if critics else {}
        clean = last.get("clean")
        return (
            f"run {self.run_id} | skill={self.skill} | decision={self.final_decision} "
            f"| critic_passes={len(critics)} | last_clean={clean}"
        )
