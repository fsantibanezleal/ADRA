"""Content guard for ADR-0067: no em-dashes and no emoji in repository text.

The guard walks the text surfaces of this repository (README, CHANGELOG,
pyproject, the engine package, the CLI, the docs, the bibliography README,
the scripts, the Claude skill, the tests, the GitHub workflows, and the
root-level tracked text files such as the example env, the gitignore and
the requirements list), decodes every text file as UTF-8 and reports each
forbidden character with its file, line and column.

Two classes of finding:

* Violations, which fail the run with exit code 1: the em-dash (U+2014) and
  every emoji codepoint in the ranges U+1F000 to U+1FAFF, U+2600 to U+27BF,
  U+2B00 to U+2BFF, plus the emoji variation selector U+FE0F. A file that
  is not valid UTF-8 is also a violation, because it cannot be checked.

* Advisories, which never fail the run: directional arrows (U+2190, U+2192,
  U+2194, U+21D0, U+21D2, U+27F5, U+27F6) found in Markdown prose, that is,
  outside fenced code blocks and outside inline code spans. ADR-0067 allows
  arrows as notation (pipelines, renames, mappings) but not as a stand-in for
  words such as "leads to" or "means", so a reviewer reads the list and
  decides.

Usage:

    python scripts/check_content.py            # checks the repository root
    python scripts/check_content.py --root X   # checks another checkout

The module is import-safe: ``scan_tree`` and ``scan_text`` return typed
results and print nothing, so the test suite can assert on them directly.
Every forbidden codepoint is written as an escape sequence in this source so
the guard cannot flag itself.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

# Surfaces to walk, relative to the root. Directories are walked recursively;
# files are checked on their own. A missing entry is skipped silently so the
# same walk works on a partial checkout or a temporary fixture tree.
SURFACES: tuple[str, ...] = (
    "README.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "adra",
    "cli",
    "docs",
    "refs/README.md",
    "scripts",
    "skills",
    "tests",
    ".github",
    # Root-level tracked text files and the remaining small trees, so the
    # guard covers every git-tracked text surface as ADR-0067 requires.
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "VERSION",
    "examples",
    ".claude-plugin",
)

# Directory names skipped at any depth.
SKIP_DIRS: frozenset[str] = frozenset({
    ".venv",
    "venv",
    ".git",
    "node_modules",
    "__pycache__",
    "runs",
    "dist",
    "build",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
})

# File suffixes skipped before reading: bibliography sources and binaries.
SKIP_SUFFIXES: frozenset[str] = frozenset({
    ".bib",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".bmp",
    ".pdf",
    ".pyc", ".pyo", ".so", ".pyd", ".dll", ".exe",
    ".whl", ".zip", ".gz", ".tgz", ".tar", ".7z",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".db", ".sqlite", ".sqlite3", ".parquet",
})

EM_DASH: int = 0x2014
HORIZONTAL_BAR: int = 0x2015  # banned by ADR-0067 alongside the em-dash

EMOJI_RANGES: tuple[tuple[int, int], ...] = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0xFE0F, 0xFE0F),
)

ARROWS: frozenset[int] = frozenset({
    0x2190, 0x2192, 0x2194, 0x21D0, 0x21D2, 0x27F5, 0x27F6,
})

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_INLINE_CODE_RE = re.compile(r"(`+)(.*?)\1")


@dataclass(frozen=True)
class Hit:
    """One finding: a forbidden or advisory character at a position."""

    path: Path
    line: int
    column: int
    codepoint: int
    kind: str

    def format(self, root: Path) -> str:
        try:
            shown = self.path.relative_to(root).as_posix()
        except ValueError:
            shown = self.path.as_posix()
        return f"{shown}:{self.line}:{self.column}: {self.kind} U+{self.codepoint:04X}"


@dataclass(frozen=True)
class Report:
    """The outcome of a scan: failing violations and non-failing advisories."""

    violations: tuple[Hit, ...]
    arrows: tuple[Hit, ...]
    files_checked: int

    @property
    def ok(self) -> bool:
        return not self.violations


def is_emoji(codepoint: int) -> bool:
    """True when the codepoint falls inside one of the emoji ranges."""
    return any(low <= codepoint <= high for low, high in EMOJI_RANGES)


def classify(codepoint: int) -> str | None:
    """Return the violation kind for a codepoint, or None when it is allowed."""
    if codepoint == EM_DASH:
        return "em-dash"
    if codepoint == HORIZONTAL_BAR:
        return "horizontal-bar"
    if is_emoji(codepoint):
        return "emoji"
    return None


def _blank_inline_code(line: str) -> str:
    """Replace inline code spans with spaces so columns stay aligned."""
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def scan_text(path: Path, text: str, *, markdown: bool | None = None) -> tuple[list[Hit], list[Hit]]:
    """Scan decoded text. Returns (violations, arrow advisories).

    ``markdown`` decides whether arrow advisories are collected; when None it
    is inferred from the file suffix.
    """
    if markdown is None:
        markdown = path.suffix.lower() == ".md"
    violations: list[Hit] = []
    arrows: list[Hit] = []
    in_fence = False
    for line_no, raw_line in enumerate(text.split("\n"), start=1):
        for col, ch in enumerate(raw_line, start=1):
            kind = classify(ord(ch))
            if kind is not None:
                violations.append(Hit(path, line_no, col, ord(ch), kind))
        if not markdown:
            continue
        if _FENCE_RE.match(raw_line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        prose = _blank_inline_code(raw_line)
        for col, ch in enumerate(prose, start=1):
            if ord(ch) in ARROWS:
                arrows.append(Hit(path, line_no, col, ord(ch), "arrow"))
    return violations, arrows


def _looks_binary(data: bytes) -> bool:
    return b"\x00" in data[:8192]


def scan_file(path: Path) -> tuple[list[Hit], list[Hit]] | None:
    """Scan one file. Returns None when the file is skipped as binary."""
    data = path.read_bytes()
    if _looks_binary(data):
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        # Line 1, column = byte offset + 1, codepoint = the offending byte.
        return [Hit(path, 1, exc.start + 1, data[exc.start], "not-utf-8")], []
    return scan_text(path, text)


def iter_files(root: Path, surfaces: Iterable[str] = SURFACES) -> Iterator[Path]:
    """Yield every candidate file under the configured surfaces, sorted."""
    for surface in surfaces:
        target = root / surface
        if target.is_file():
            if target.suffix.lower() not in SKIP_SUFFIXES:
                yield target
            continue
        if not target.is_dir():
            continue
        for candidate in sorted(target.rglob("*")):
            if not candidate.is_file():
                continue
            rel_parts = candidate.relative_to(root).parts
            if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in rel_parts):
                continue
            if candidate.suffix.lower() in SKIP_SUFFIXES:
                continue
            yield candidate


def scan_tree(root: Path, surfaces: Iterable[str] = SURFACES) -> Report:
    """Walk the surfaces under ``root`` and collect every finding."""
    violations: list[Hit] = []
    arrows: list[Hit] = []
    checked = 0
    for path in iter_files(root, surfaces):
        result = scan_file(path)
        if result is None:
            continue
        checked += 1
        file_violations, file_arrows = result
        violations.extend(file_violations)
        arrows.extend(file_arrows)
    return Report(tuple(violations), tuple(arrows), checked)


def render(report: Report, root: Path) -> str:
    """Render a report as the text the CLI prints."""
    lines: list[str] = []
    if report.violations:
        lines.append(f"ADR-0067 violations ({len(report.violations)}):")
        lines.extend("  " + hit.format(root) for hit in report.violations)
    else:
        lines.append("ADR-0067 violations: none")
    if report.arrows:
        lines.append("")
        lines.append(
            f"Arrows in Markdown prose ({len(report.arrows)}), review that each one is notation:"
        )
        lines.extend("  " + hit.format(root) for hit in report.arrows)
    lines.append("")
    lines.append(f"Files checked: {report.files_checked}")
    lines.append("Result: " + ("PASS" if report.ok else "FAIL"))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ADR-0067 content guard: no em-dash, no emoji.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repository root to check (default: the parent of scripts/)",
    )
    args = parser.parse_args(argv)
    root: Path = args.root.resolve()
    report = scan_tree(root)
    print(render(report, root))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
