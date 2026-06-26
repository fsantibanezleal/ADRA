"""LLM provider factory and the offline mock.

ADRA owns a tiny chat-model seam (:class:`ChatModel`) instead of depending on a
heavy agent framework. The orchestrator is a hand-rolled deterministic state machine
(see :mod:`adra.orchestrator`); this module is the only place that touches a provider.
Two adapters ship:

- ``anthropic`` — a real provider via the native ``anthropic`` SDK (lazy import).
- ``mock`` — a deterministic offline model so the whole loop runs, and the test
  suite passes, with **no API key**.

The mock is deliberately a *formatter*, not a reasoner: the substance of every run
comes from the deterministic tools and the deterministic red-team critic, so the
offline path still exercises real adversarial validation. Connecting a provider adds
the semantic layer on top of that deterministic floor. New providers
(``openai`` / ``groq`` / ``xai``) are one small :class:`ChatModel` subclass each — the
rest of the engine only knows :class:`ChatModel`.
"""

from __future__ import annotations

import json
import os
import re

from adra.config import PROVIDERS, Settings
from adra.nodes import Node

# The node tag the mock reads to pick a canned shape, embedded in the system turn.
_NODE_TAG = re.compile(r"\[\[ADRA-NODE:([a-z_]+)\]\]")

# Canned, node-keyed responses. They are merged with the deterministic tool
# findings (the real substance) by each skill, so the offline demo stays honest.
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
    """Minimal chat-model seam: one system + user turn returns text.

    Keeping the seam ADRA-owned (rather than importing a framework's base class)
    keeps the dependency surface small and the offline mock trivial to construct.
    """

    def generate(self, system: str, user: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class MockChatModel(ChatModel):
    """Deterministic offline chat model for keyless runs and tests."""

    def generate(self, system: str, user: str) -> str:
        match = _NODE_TAG.search(system) or _NODE_TAG.search(user)
        node = Node(match.group(1)) if match else Node.CODE_REVIEW
        return _CANNED.get(node, _CANNED[Node.CODE_REVIEW])


class AnthropicChatModel(ChatModel):
    """Real provider via the native ``anthropic`` SDK (lazy import)."""

    def __init__(self, model: str, temperature: float, max_tokens: int) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - only when extra missing
            raise RuntimeError(
                "provider=anthropic requires `pip install anthropic` and "
                "ANTHROPIC_API_KEY in the environment."
            ) from exc
        self._client = anthropic.Anthropic()
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, system: str, user: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in message.content
            if getattr(block, "type", None) == "text"
        )


class OpenAICompatChatModel(ChatModel):
    """Any OpenAI-compatible Chat Completions endpoint.

    Covers OpenAI, Groq, xAI, Mistral, DeepSeek, OpenRouter, Together — and **local,
    free** servers (Ollama / LM Studio / vLLM) — selected by base URL. Requires the
    ``openai`` SDK (``pip install adra[openai]``).
    """

    def __init__(self, model: str, temperature: float, max_tokens: int,
                 base_url: str, api_key: str | None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - only when extra missing
            raise RuntimeError(
                "this provider requires `pip install openai` (or `pip install adra[openai]`)."
            ) from exc
        # Local servers (Ollama / LM Studio) accept any non-empty key.
        self._client = OpenAI(base_url=base_url, api_key=api_key or "not-needed")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""


def make_chat_model_for(provider: str, model: str, temperature: float, max_tokens: int) -> ChatModel:
    """Build a :class:`ChatModel` for an explicit provider + model.

    ``mock`` (offline, no key) and ``anthropic`` (native SDK) are built in; every other
    provider in :data:`adra.config.PROVIDERS` (OpenAI, Groq, xAI, Mistral, DeepSeek,
    OpenRouter, Together, local Ollama/LM Studio/vLLM) is reached over the
    OpenAI-compatible API. Override the endpoint of any other compatible service with
    ``ADRA_BASE_URL`` + ``ADRA_API_KEY``.

    Raises:
        RuntimeError: for an unknown provider, or if the needed SDK extra is missing.
    """
    if provider == "mock":
        return MockChatModel()
    if provider == "anthropic":
        return AnthropicChatModel(model, temperature, max_tokens)
    info = PROVIDERS.get(provider)
    if info is None:
        known = ", ".join(["mock", "anthropic", *PROVIDERS])
        raise RuntimeError(f"unknown provider {provider!r}; known: {known}")
    base_url = os.environ.get("ADRA_BASE_URL") or info["base_url"]
    api_key = os.environ.get("ADRA_API_KEY") or (
        os.environ.get(info["key_env"]) if info["key_env"] else None)
    return OpenAICompatChatModel(model, temperature, max_tokens, base_url, api_key)


def make_chat_model(settings: Settings) -> ChatModel:
    """Build the default chat model for ``settings`` (provider + model)."""
    return make_chat_model_for(
        settings.provider, settings.model, settings.temperature, settings.max_tokens)


class ModelRouter:
    """Resolve a :class:`ChatModel` per flow role so a single run can orchestrate across
    providers — e.g. a strong model for the critic/judge, a cheaper/faster one for
    generation. Models are cached by ``(provider, model)`` and built lazily.
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
    """Invoke ``model`` with a system+user turn tagged for the offline mock.

    Args:
        model: The chat model.
        system: System prompt (role / rules).
        user: User turn (the actual request + context).
        node: The graph node this call serves (drives the offline mock).

    Returns:
        The model's text response.
    """
    tagged = f"{system}\n\n[[ADRA-NODE:{node.value}]]"
    return model.generate(tagged, user)
