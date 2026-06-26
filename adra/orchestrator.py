"""The orchestrator: a small explicit state machine implementing the spine

    plan -> ground -> generate -> CRITIC -> (revise -> CRITIC)* -> decide

The graph is deliberately a readable, framework-free state machine rather than a
heavy agent runtime; node contracts stay stable if it is ever wrapped. The critic is
mandatory and blocking: an artifact is only ``accepted`` when the critic returns
clean; otherwise the loop revises up to ``max_rounds`` and then ``escalate``s to a
human (it never silently approves). Every node writes a provenance event.
"""

from __future__ import annotations

from adra import critic as critic_mod
from adra.config import Settings
from adra.llm import ChatModel, ModelRouter
from adra.provenance import RunRecord
from adra.skills import SKILLS
from adra.state import RunState
from adra.utils import clip


class Orchestrator:
    """Runs one skill through the adversarial loop and returns the run record."""

    def __init__(self, settings: Settings, model: ChatModel | None = None):
        self.settings = settings
        # An explicit model (tests / single-model runs) wins for every role; otherwise the
        # router resolves a model per role, so the flow can orchestrate across providers.
        self._fixed = model
        self.router = ModelRouter(settings)

    def _model(self, role: str) -> ChatModel:
        return self._fixed or self.router.for_role(role)

    def _model_id(self, role: str) -> str:
        return "fixed" if self._fixed is not None else self.settings.model_id(role)

    def run(self, skill: str, intake: dict) -> tuple[RunState, RunRecord]:
        if skill not in SKILLS:
            raise ValueError(f"unknown skill {skill!r}; available: {sorted(SKILLS)}")
        impl = SKILLS[skill]
        state = RunState(skill=skill, intake=intake)
        record = RunRecord(
            skill=skill, intake=intake,
            provider=self.settings.provider, model=self.settings.model,
        )

        # plan -> ground -> generate
        state.plan = impl.plan(self._model("plan"), self.settings, state)
        record.event("plan", "plan", {**(state.plan or {}), "model": self._model_id("plan")})

        state.grounding = impl.ground(self.settings, state)
        record.event("ground", "ground",
                     {k: v.log_dict() for k, v in state.grounding.items()})

        state.draft = impl.generate(self._model("generate"), self.settings, state)
        record.event("generate", "generate",
                     {"draft_preview": clip(state.draft), "model": self._model_id("generate")})

        # CRITIC -> revise loop
        while True:
            verdict = critic_mod.criticize(self._model("critic"), state)
            state.critic_history.append(verdict)
            record.event("critic", "critic", {**verdict.to_dict(), "model": self._model_id("critic")})
            if verdict.clean:
                state.decision = "accepted"
                break
            if state.rounds >= self.settings.max_rounds:
                state.decision = "escalate"
                break
            state.rounds += 1
            state.draft = impl.revise(self._model("generate"), self.settings, state, verdict)
            record.event("revise", "revise",
                         {"round": state.rounds, "draft_preview": clip(state.draft)})

        # finalize artifacts (skill renders the accepted/escalated draft)
        state.artifacts = impl.finalize(self.settings, state)
        record.final_decision = state.decision
        record.artifacts = state.artifacts
        record.event("decide", "decide", {"decision": state.decision})
        record.write(self.settings.runs_dir)
        return state, record
