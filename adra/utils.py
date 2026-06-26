"""Small, dependency-free helpers shared across the package."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_FENCE = re.compile(r"^```[a-zA-Z]*\n?|\n?```$")
_PROMPTS = Path(__file__).resolve().parent / "prompts"
# The bundled fictional client (Northwind). Its directory IS the standards suite
# (README / conventions / ci-standards / glossary / adr/ / cases/).
_DEFAULT_CLIENT = Path(__file__).resolve().parent / "clients" / "synthetic" / "northwind"


def client_dir() -> Path:
    """Resolve the active client's standards directory.

    Defaults to the bundled synthetic client; override with ``ADRA_CLIENT_DIR`` to
    ground ADRA on any client's governance suite (the engine stays client-agnostic).
    """
    env = os.environ.get("ADRA_CLIENT_DIR")
    return Path(env) if env else _DEFAULT_CLIENT


def load_prompt(name: str) -> str:
    """Load a prompt template from ``adra/prompts/<name>.md`` ('' if absent)."""
    path = _PROMPTS / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_standard(relpath: str) -> str:
    """Load a client governance document from the ``standards/`` suite.

    Args:
        relpath: Path relative to ``standards/``, e.g. ``"conventions.md"`` or
            ``"adr/ADR-0002-no-stale-base-merges.md"``.

    Returns:
        The document text, or '' if it does not exist. Point ADRA at a different client
        with the ``ADRA_CLIENT_DIR`` environment variable (or ``Settings.client_dir``).
    """
    path = client_dir() / relpath
    return path.read_text(encoding="utf-8") if path.exists() else ""


def parse_json(text: str) -> dict[str, Any]:
    """Best-effort parse of a JSON object from an LLM response.

    Tolerates markdown code fences and leading/trailing prose by extracting the
    first balanced ``{...}`` object.

    Args:
        text: Raw model output.

    Returns:
        The decoded object, or an empty dict if nothing parseable is found.
    """
    text = _FENCE.sub("", text.strip()).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start == -1:
        return {}
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


def clip(text: str, limit: int = 300) -> str:
    """Truncate ``text`` to ``limit`` characters with an ellipsis marker."""
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "…"
