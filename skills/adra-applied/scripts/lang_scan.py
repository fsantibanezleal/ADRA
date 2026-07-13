"""lang_scan.py — English-only and authoring-tool-leak scan (always safe).

Flags two things that must never reach a code repo or PR:
  * authoring-tool / AI-session leak (BLOCKER): tool or vendor names, "co-authored-by",
    "generated with AI", "as an AI".
  * non-English content (MAJOR): Spanish accent characters and a conservative set of
    unambiguous Spanish words. Note: the team wiki is intentionally Spanish, so a
    MAJOR here is expected only for wiki prose and should be ignored there.

Usage:
    python lang_scan.py --path <file-or-dir>
    python lang_scan.py --text "<string>"

Exit 1 if any leak (BLOCKER) is found.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402

# Authoring-tool / AI leak markers (BLOCKER). Case-insensitive.
_LEAK = re.compile(
    r"(co-?authored-?by"
    r"|generated with .*(?:claude|ai|copilot|gpt)"
    r"|\bas an ai\b"
    r"|\banthropic\b"
    r"|\bclaude\b"
    r"|\bchatgpt\b|\bopenai\b|\bcopilot\b)",
    re.IGNORECASE,
)

# Spanish accent / punctuation characters (MAJOR), via unicode escapes (ASCII source).
_ACCENT = re.compile("[áéíóúüñ"
                     "ÁÉÍÓÚÜÑ¿¡]")

# A conservative set of unambiguous Spanish words (MAJOR).
_ES_WORDS = re.compile(
    r"\b(porque|también|según|además|entonces|aunque|mientras"
    r"|archivo|datos|usuario|función|código|ejemplo|mediante|debe"
    r"|puede|siguiente|resultado|prueba|cambios)\b",
    re.IGNORECASE,
)

_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".attachments", "runs"}
_TEXT_EXT = {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".sql", ".sh",
             ".ps1", ".cfg", ".ini", ".toml", ".js", ".ts", ".tsx"}
_MAX_FINDINGS = 100


def scan_text(text: str, where: str, findings: list) -> None:
    for i, line in enumerate(text.splitlines(), start=1):
        if len(findings) >= _MAX_FINDINGS:
            return
        m = _LEAK.search(line)
        if m:
            findings.append(c.finding(
                c.BLOCKER, "language_leak",
                f"authoring-tool/AI leak marker: '{m.group(0)}'",
                location=f"{where}:{i}", evidence=line.strip()[:200], source="lang_scan"))
        if _ACCENT.search(line) or _ES_WORDS.search(line):
            findings.append(c.finding(
                c.MAJOR, "non_english",
                "possible non-English (Spanish) content on disk",
                location=f"{where}:{i}", evidence=line.strip()[:200], source="lang_scan"))


def iter_files(path: str):
    if os.path.isfile(path):
        yield path
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for name in files:
            if os.path.splitext(name)[1].lower() in _TEXT_EXT:
                yield os.path.join(root, name)


def main() -> int:
    ap = argparse.ArgumentParser(description="English-only + authoring-tool-leak scan.")
    ap.add_argument("--path")
    ap.add_argument("--text")
    args = ap.parse_args()

    findings: list = []
    scanned = 0
    if args.text is not None:
        scan_text(args.text, "<text>", findings)
        scanned = 1
    elif args.path:
        for fp in iter_files(args.path):
            if len(findings) >= _MAX_FINDINGS:
                break
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    scan_text(fh.read(), fp, findings)
                scanned += 1
            except (OSError, UnicodeDecodeError):
                continue
    else:
        return c.emit(c.result("lang_scan", False, reason="pass --path or --text"))

    data = {"files_scanned": scanned,
            "leak": sum(1 for f in findings if f["category"] == "language_leak"),
            "non_english": sum(1 for f in findings if f["category"] == "non_english"),
            "truncated": len(findings) >= _MAX_FINDINGS}
    return c.emit(c.result("lang_scan", True, findings, data))


if __name__ == "__main__":
    raise SystemExit(main())
