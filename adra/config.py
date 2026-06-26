"""Runtime settings for ADRA.

Settings come from environment variables (a ``.env`` is loaded if present) with
safe defaults so the package runs offline out of the box. Nothing here reads or
stores secrets beyond the LLM key, which is only ever taken from the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from adra.utils import client_dir as _client_dir

# Default Anthropic model — claude-haiku-4-5 per ADR-0053 (cost-appropriate default for
# private/quality apps; switch to claude-sonnet-4-6 when reasoning depth matters). Overridable via ADRA_MODEL.
DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5"

# Built-in providers. Anthropic uses its native SDK; every entry below speaks the
# OpenAI-compatible Chat Completions API, so OpenAI, Groq, xAI, Mistral, DeepSeek,
# OpenRouter, Together AND local servers (Ollama / LM Studio / vLLM) all work — bring
# whatever you have, or run a local model for free. Any other OpenAI-compatible service
# works via ADRA_BASE_URL + ADRA_API_KEY.
PROVIDERS: dict[str, dict[str, str]] = {
    "openai":     {"base_url": "https://api.openai.com/v1",      "key_env": "OPENAI_API_KEY",     "default_model": "gpt-4o"},
    "groq":       {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY",       "default_model": "llama-3.3-70b-versatile"},
    "xai":        {"base_url": "https://api.x.ai/v1",            "key_env": "XAI_API_KEY",        "default_model": "grok-4"},
    "mistral":    {"base_url": "https://api.mistral.ai/v1",      "key_env": "MISTRAL_API_KEY",    "default_model": "mistral-large-latest"},
    "deepseek":   {"base_url": "https://api.deepseek.com/v1",    "key_env": "DEEPSEEK_API_KEY",   "default_model": "deepseek-chat"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",   "key_env": "OPENROUTER_API_KEY", "default_model": "openai/gpt-4o"},
    "together":   {"base_url": "https://api.together.xyz/v1",    "key_env": "TOGETHER_API_KEY",   "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo"},
    "ollama":     {"base_url": "http://localhost:11434/v1",      "key_env": "",                   "default_model": "llama3.1"},
}

# Auto-detect order when ADRA_PROVIDER is unset: a present key wins; else offline mock.
_AUTODETECT_ORDER = ("anthropic", "openai", "groq", "xai", "mistral", "deepseek", "openrouter", "together")


def default_model(provider: str) -> str:
    """The default model id for a provider (overridable with ADRA_MODEL)."""
    if provider in ("anthropic", "mock"):
        return DEFAULT_ANTHROPIC_MODEL
    info = PROVIDERS.get(provider)
    return info["default_model"] if info else DEFAULT_ANTHROPIC_MODEL


def _autodetect_provider() -> str:
    """Pick a provider from whichever API key is present; offline mock if none."""
    for name in _AUTODETECT_ORDER:
        key_env = "ANTHROPIC_API_KEY" if name == "anthropic" else PROVIDERS.get(name, {}).get("key_env", "")
        if key_env and os.environ.get(key_env):
            return name
    return "mock"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no external dependency).

    Only sets keys that are not already present in the environment, so explicit
    environment variables always win.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass
class Settings:
    """Resolved configuration for a run."""

    # LLM (the deterministic loop runs offline with NO key; a provider adds the semantic
    # layer). provider: mock | anthropic | openai | groq | xai | mistral | deepseek |
    # openrouter | together | ollama (local). See adra.config.PROVIDERS.
    provider: str = "mock"
    model: str = DEFAULT_ANTHROPIC_MODEL
    temperature: float = 0.0
    max_tokens: int = 4096
    # Per-role model overrides so one run can orchestrate across providers (e.g. a strong
    # model for the critic/judge, a cheaper/faster one for generation). Value per role is
    # "provider:model" or just "model" (provider inherits the default). Empty => default.
    role_models: dict[str, str] = field(default_factory=dict)

    # Adversarial loop
    max_rounds: int = 3  # generate -> critic -> revise iterations before escalation
    judge_swap_average: bool = True  # evaluate pairwise comparisons in both orders

    # Provenance
    runs_dir: Path = field(default_factory=lambda: Path("runs"))

    # Repo context (for deterministic tools); optional.
    repo_path: Path | None = None

    # Active client governance suite (conventions / ADRs / CI standards / cases) the
    # engine grounds on. Defaults to the bundled synthetic client; ADRA_CLIENT_DIR overrides.
    client_dir: Path = field(default_factory=_client_dir)

    # Safety: deterministic tools that mutate or call external services stay off
    # unless explicitly enabled (default is dry-run / read-only).
    allow_external_calls: bool = False

    def role(self, role: str) -> tuple[str, str]:
        """Resolve (provider, model) for a flow role: 'plan'|'generate'|'critic'|'judge'.

        Falls back to the run's default provider/model; overridden per role via
        ``role_models`` (``ADRA_MODEL_<ROLE>``), value ``"provider:model"`` or ``"model"``.
        """
        spec = self.role_models.get(role, "")
        if not spec:
            return self.provider, self.model
        if ":" in spec:
            prov, _, mdl = spec.partition(":")
            return (prov or self.provider), (mdl or self.model)
        return self.provider, spec

    def model_id(self, role: str) -> str:
        """``provider:model`` string for the given role (for logging / provenance)."""
        prov, mdl = self.role(role)
        return f"{prov}:{mdl}"

    @property
    def offline(self) -> bool:
        return self.provider == "mock"


def load_settings(**overrides) -> Settings:
    """Build :class:`Settings` from env + overrides.

    Provider auto-detects: if ``ADRA_PROVIDER`` is unset, the first provider with a
    present API key wins (Anthropic → OpenAI → Groq → xAI → ...); otherwise the offline
    ``mock`` provider. Model defaults per provider unless ``ADRA_MODEL`` is set; per-role
    overrides come from ``ADRA_MODEL_{PLAN,GENERATE,CRITIC,JUDGE}``.
    """
    _load_dotenv(Path(".env"))

    provider = os.environ.get("ADRA_PROVIDER") or _autodetect_provider()

    role_models: dict[str, str] = {}
    for role in ("plan", "generate", "critic", "judge"):
        spec = os.environ.get(f"ADRA_MODEL_{role.upper()}")
        if spec:
            role_models[role] = spec

    settings = Settings(
        provider=provider,
        model=os.environ.get("ADRA_MODEL") or default_model(provider),
        temperature=float(os.environ.get("ADRA_TEMPERATURE", "0.0")),
        max_tokens=int(os.environ.get("ADRA_MAX_TOKENS", "4096")),
        max_rounds=int(os.environ.get("ADRA_MAX_ROUNDS", "3")),
        allow_external_calls=os.environ.get("ADRA_ALLOW_EXTERNAL", "0") == "1",
        role_models=role_models,
    )
    repo = os.environ.get("ADRA_REPO_PATH")
    if repo:
        settings.repo_path = Path(repo)
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings
