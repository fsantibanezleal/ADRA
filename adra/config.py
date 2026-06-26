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

# Default model id: keep aligned with the latest Claude Opus available to the team.
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-8"


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

    # LLM
    provider: str = "mock"  # "mock" | "anthropic"
    model: str = DEFAULT_ANTHROPIC_MODEL
    temperature: float = 0.0
    max_tokens: int = 4096

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

    @property
    def offline(self) -> bool:
        return self.provider == "mock"


def load_settings(**overrides) -> Settings:
    """Build :class:`Settings` from env + overrides.

    Provider auto-detects: if ``ADRA_PROVIDER`` is unset, use ``anthropic`` when an
    API key is present, otherwise fall back to the offline ``mock`` provider.
    """
    _load_dotenv(Path(".env"))

    provider = os.environ.get("ADRA_PROVIDER")
    if provider is None:
        provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "mock"

    settings = Settings(
        provider=provider,
        model=os.environ.get("ADRA_MODEL", DEFAULT_ANTHROPIC_MODEL),
        temperature=float(os.environ.get("ADRA_TEMPERATURE", "0.0")),
        max_tokens=int(os.environ.get("ADRA_MAX_TOKENS", "4096")),
        max_rounds=int(os.environ.get("ADRA_MAX_ROUNDS", "3")),
        allow_external_calls=os.environ.get("ADRA_ALLOW_EXTERNAL", "0") == "1",
    )
    repo = os.environ.get("ADRA_REPO_PATH")
    if repo:
        settings.repo_path = Path(repo)
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings
