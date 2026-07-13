"""merge_base_health.py — stale-base and destructive-diff detection (ADR-0002/0003).

Read-only git. Computes the merge-base against the production reference branch,
how many commits the source branch is behind, and scans the merge-base diff for
the destructive signature: file deletions and resource renames off ``.yml``.

Usage:
    python merge_base_health.py --repo <path> --source <branch> --target <prod-ref>
    python merge_base_health.py --fixture fixture.json

Fixture shape (offline replay):
    {"merge_base": "<sha>", "behind": 12,
     "name_status": "D\\tsrc/nb.py\\nR100\\ta.yml\\ta.yml.t\\n"}

Exit 1 if any blocking finding (deletion or dropped bundle resource).
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402


def analyze(behind: int, name_status: str) -> list:
    findings = []
    if behind and behind > 0:
        findings.append(c.finding(
            c.MAJOR, "stale_merge_base",
            f"branch is {behind} commit(s) behind the production reference; "
            "rebase or recreate before review",
            evidence=f"commits_behind={behind}", source="merge_base_health",
        ))
    for line in (name_status or "").splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            continue
        fields = line.split("\t")
        code = fields[0].strip()
        if code.startswith("D"):
            findings.append(c.finding(
                c.BLOCKER, "destructive_deletions",
                "file deletion vs the merge-base; confirm this is intended",
                evidence=line, source="merge_base_health",
            ))
        if code.startswith("R") and len(fields) >= 3:
            old_path, new_path = fields[1].strip(), fields[2].strip()
            if old_path.lower().endswith(".yml") and not new_path.lower().endswith(".yml"):
                findings.append(c.finding(
                    c.BLOCKER, "dropped_bundle_resource",
                    "bundle resource renamed off .yml; the resource is dropped "
                    "from the bundle on deploy",
                    evidence=f"{old_path} -> {new_path}", source="merge_base_health",
                ))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge-base health and destructive-diff scan.")
    ap.add_argument("--repo")
    ap.add_argument("--source", default="HEAD")
    ap.add_argument("--target", default="main", help="production reference branch")
    ap.add_argument("--fixture")
    args = ap.parse_args()

    fx = c.load_fixture(args.fixture)
    if fx is not None:
        behind = int(fx.get("behind", 0))
        name_status = fx.get("name_status", "")
        base = fx.get("merge_base", "")
        data = {"merge_base": base, "behind": behind, "source": "fixture"}
        return c.emit(c.result("merge_base_health", True, analyze(behind, name_status), data))

    if not args.repo:
        return c.emit(c.result("merge_base_health", False, reason="no --repo and no --fixture"))

    target_ref = f"origin/{args.target}"
    c.run_cmd(["git", "-C", args.repo, "fetch", "--all", "--prune"], timeout=60)
    mb = c.run_cmd(["git", "-C", args.repo, "merge-base", args.source, target_ref])
    if mb["returncode"] != 0:
        return c.emit(c.result(
            "merge_base_health", False,
            reason=f"git merge-base failed: {mb['stderr'].strip() or mb['stdout'].strip()}"))
    base = mb["stdout"].strip()
    rc = c.run_cmd(["git", "-C", args.repo, "rev-list", "--count", f"{base}..{target_ref}"])
    behind = int((rc["stdout"].strip() or "0")) if rc["returncode"] == 0 else 0
    ns = c.run_cmd(["git", "-C", args.repo, "diff", "--name-status", f"{base}..{args.source}"])
    name_status = ns["stdout"] if ns["returncode"] == 0 else ""
    data = {"merge_base": base, "behind": behind,
            "target_ref": target_ref, "source": args.source}
    return c.emit(c.result("merge_base_health", True, analyze(behind, name_status), data))


if __name__ == "__main__":
    raise SystemExit(main())
