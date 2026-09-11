"""Tests for the ADR-0067 content guard (scripts/check_content.py).

The guard is loaded as a module from its file so the test does not depend
on scripts/ being importable as a package. Everything runs offline; the
forbidden characters are built from codepoints so the guard never flags
this file itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = REPO_ROOT / "scripts" / "check_content.py"

EM_DASH = chr(0x2014)
EMOJI = chr(0x1F600)
VARIATION_SELECTOR = chr(0xFE0F)
RIGHT_ARROW = chr(0x2192)


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_content", GUARD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    return _load_guard()


def test_repository_has_no_violations(guard: ModuleType) -> None:
    report = guard.scan_tree(REPO_ROOT)
    rendered = "\n".join(hit.format(REPO_ROOT) for hit in report.violations)
    assert report.files_checked > 0
    assert report.violations == (), f"ADR-0067 violations:\n{rendered}"


def test_em_dash_in_temporary_file_is_flagged(guard: ModuleType, tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    target.write_text(f"first line\nsecond {EM_DASH} line\n", encoding="utf-8")
    violations, arrows = guard.scan_file(target)
    assert arrows == []
    assert [(h.line, h.column, h.codepoint, h.kind) for h in violations] == [
        (2, 8, 0x2014, "em-dash"),
    ]


def test_emoji_and_variation_selector_are_flagged(guard: ModuleType, tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text(f'MSG = "ok {EMOJI}{VARIATION_SELECTOR}"\n', encoding="utf-8")
    violations, _ = guard.scan_file(target)
    assert [(h.codepoint, h.kind) for h in violations] == [
        (0x1F600, "emoji"),
        (0xFE0F, "emoji"),
    ]


def test_arrows_are_advisory_and_skip_code(guard: ModuleType, tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text(
        "\n".join([
            f"prose a {RIGHT_ARROW} b",
            f"inline `x {RIGHT_ARROW} y` kept quiet",
            "```",
            f"fenced {RIGHT_ARROW} ignored",
            "```",
            f"after fence {RIGHT_ARROW} reported",
            "",
        ]),
        encoding="utf-8",
    )
    violations, arrows = guard.scan_file(target)
    assert violations == []
    assert [(h.line, h.column) for h in arrows] == [(1, 9), (6, 13)]


def test_main_exit_codes(guard: ModuleType, tmp_path: Path) -> None:
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "README.md").write_text("plain text\n", encoding="utf-8")
    assert guard.main(["--root", str(clean)]) == 0

    dirty = tmp_path / "dirty"
    (dirty / "docs").mkdir(parents=True)
    (dirty / "docs" / "page.md").write_text(f"bad {EM_DASH} here\n", encoding="utf-8")
    assert guard.main(["--root", str(dirty)]) == 1
