"""LLM layer — the house standard: pydantic-ai over a `provider:model` seam (ADR-0007
lane-c, ADR-0053), multi-provider/agnostic, with a deterministic offline fallback (ADR-0052).

- Real providers go through **pydantic-ai** (`Agent`): `anthropic` / `openai` / `groq` /
  `google` / `mistral` natively, and the OpenAI-compatible long tail (`xai` / `deepseek` /
  `openrouter` / `together` / local `ollama`) via an OpenAI-compatible base URL — the same
  LiteLLM-class seam. Models are `provider:model` strings chosen by env (ADR-0053).
- `mock` is the deterministic, keyless fallback so the engine + tests run offline; nothing
  here is tied to a model version (the `temperature`/params are pydantic-ai's concern).

New provider/model = config (`ADRA_PROVIDER` / `ADRA_MODEL` / `ADRA_MODEL_<ROLE>`), never
engine logic. A thin `ChatModel` seam keeps the rest of the engine decoupled from pydantic-ai.
"""

from __future__ import annotations

import json
import os
import re

from adra.config import PROVIDERS, Settings
from adra.nodes import Node

_NODE_TAG = re.compile(r"\[\[ADRA-NODE:([a-z_]+)\]\]")

# pydantic-ai native model-string prefixes per provider (others go via OpenAI-compatible base).
_PYDANTIC_AI_PREFIX = {
    "anthropic": "anthropic",
    "openai": "openai",
    "groq": "groq",
    "mistral": "mistral",
    "google": "google-gla",
}

# Canned, node-keyed responses for the deterministic offline mock. They are merged with the
# deterministic tool findings (the real substance) by each skill, so the offline demo stays honest.
_CANNED: dict[Node, str] = {
    Node.PLAN: json.dumps({"ok": True, "note": "classify intake, select grounding tools"}),
    Node.CODE_REVIEW: json.dumps({
        "summary": "Offline review: deterministic findings carry the verdict; connect a "
                   "provider for semantic findings (e.g. swallowed errors, contract drift).",
        "semantic_findings": [],
    }),
    Node.PR_EVAL: json.dumps({
        "verdict": "changes-requested",
        "summary": "Offline PR evaluation; see deterministic grounding for blockers.",
    }),
    Node.EXPERIMENT: json.dumps({
        "title": "Offline experiment",
        "hypotheses": [{"id": "H1", "hypothesis": "The reported anomaly is real in prod.",
                        "probability": "medium", "impact": "high", "probe": "01_reproduce.sql"}],
        "design": "Run probes in prod and dev, persist runs/*.json, then synthesize.",
        "synthesis": "Conclude only what the probe rows support.",
    }),
    Node.IMPROVE: json.dumps({
        "proposal": "Minimum-functional change: keep only what advances the result.",
        "rationale": "Prune filler even if copied from the standard; validate with the exact CI command.",
        "minimal_change": "(diff sketch)", "dead_code_removed": [], "validation_command": "",
    }),
    Node.DOCUMENT: "## Generated documentation (offline)\n\nRendered from the run record; "
                   "connect a provider for richer prose. Structure and evidence come from the "
                   "provenance log either way.",
    Node.DECIDE: json.dumps({
        "problem": "Offline route analysis.",
        "routes": [
            {"name": "Route A — scoped change", "summary": "change only the owning repo",
             "effort": "low", "blast_radius": "low (single repo)", "reversibility": "high",
             "risk": "low", "precedent": "sibling pattern in the repo"},
            {"name": "Route B — shared template", "summary": "edit the shared ndp-ci template",
             "effort": "low", "blast_radius": "high (every consumer)", "reversibility": "low",
             "risk": "high", "precedent": "none"}],
        "recommendation": "Route A",
        "rationale": "Smallest reversible scope, justified against an existing precedent (ADR-0008).",
        "open_question": "Confirm no other consumer needs the same cadence.",
        "decision_owner": "human"}),
    Node.CRITIC: json.dumps({"clean": True, "blocking": [],
                             "notes": "Offline critic defers to the deterministic red-team checklist."}),
    Node.JUDGE: json.dumps({"scores": {}, "notes": "offline rubric judge"}),
}


class ChatModel:
    """Minimal chat-model seam: one system + user turn returns text. Decouples the engine
    from the concrete LLM framework (pydantic-ai) behind it."""

    def generate(self, system: str, user: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class MockChatModel(ChatModel):
    """Deterministic offline chat model for keyless runs and tests (ADR-0052 fallback)."""

    def generate(self, system: str, user: str) -> str:
        match = _NODE_TAG.search(system) or _NODE_TAG.search(user)
        node = Node(match.group(1)) if match else Node.CODE_REVIEW
        return _CANNED.get(node, _CANNED[Node.CODE_REVIEW])


class PydanticAIChatModel(ChatModel):
    """Real provider via **pydantic-ai** (ADR-0007 lane-c). Native providers use a
    ``provider:model`` string; the OpenAI-compatible long tail uses an OpenAI base URL.
    """

    def __init__(self, provider: str, model: str, max_tokens: int) -> None:
        try:
            from pydantic_ai import Agent
        except ImportError as exc:  # pragma: no cover - only when extra missing
            raise RuntimeError(
                "real providers require `pip install adra[llm]` (pydantic-ai)."
            ) from exc
        self._agent = Agent(self._model(provider, model), retries=1)

    @staticmethod
    def _model(provider: str, model: str):
        if provider in _PYDANTIC_AI_PREFIX:
            return f"{_PYDANTIC_AI_PREFIX[provider]}:{model}"
        info = PROVIDERS.get(provider)
        if info is None:
            known = ", ".join(["mock", *_PYDANTIC_AI_PREFIX, *PROVIDERS])
            raise RuntimeError(f"unknown provider {provider!r}; known: {known}")
        # OpenAI-compatible base (xai / deepseek / openrouter / together / local ollama).
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
        api_key = os.environ.get("ADRA_API_KEY") or (
            os.environ.get(info["key_env"]) if info["key_env"] else "not-needed")
        base_url = os.environ.get("ADRA_BASE_URL") or info["base_url"]
        return OpenAIChatModel(model, provider=OpenAIProvider(base_url=base_url, api_key=api_key))

    def generate(self, system: str, user: str) -> str:
        # System carries the node tag + role rules; pass it ahead of the user turn so the
        # adapter stays framework-version-agnostic (no per-call system_prompt API).
        result = self._agent.run_sync(f"{system}\n\n---\n\n{user}")
        return str(getattr(result, "output", "") or "")


def make_chat_model_for(provider: str, model: str, temperature: float, max_tokens: int) -> ChatModel:
    """Build a :class:`ChatModel` for an explicit provider + model.

    ``mock`` is the deterministic offline fallback; every real provider goes through
    pydantic-ai (native ``provider:model`` or an OpenAI-compatible base for the long tail).
    """
    if provider == "mock":
        return MockChatModel()
    return PydanticAIChatModel(provider, model, max_tokens)


def make_chat_model(settings: Settings) -> ChatModel:
    """Build the default chat model for ``settings`` (provider + model)."""
    return make_chat_model_for(
        settings.provider, settings.model, settings.temperature, settings.max_tokens)


class ModelRouter:
    """Resolve a :class:`ChatModel` per flow role so one run can orchestrate across providers
    — a strong model for the critic/judge, a cheaper/faster one for generation. Cached by
    ``(provider, model)`` and built lazily.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cache: dict[tuple[str, str], ChatModel] = {}

    def for_role(self, role: str) -> ChatModel:
        provider, model = self.settings.role(role)
        key = (provider, model)
        if key not in self._cache:
            self._cache[key] = make_chat_model_for(
                provider, model, self.settings.temperature, self.settings.max_tokens)
        return self._cache[key]


def invoke_text(model: ChatModel, system: str, user: str, node: Node) -> str:
    """Invoke ``model`` with a system+user turn tagged for the offline mock."""
    tagged = f"{system}\n\n[[ADRA-NODE:{node.value}]]"
    return model.generate(tagged, user)
