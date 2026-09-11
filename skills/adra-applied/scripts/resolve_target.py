"""resolve_target.py · turn an entry point into a concrete target.

Given a PR (id/URL), an issue (URL), or a branch, resolve the repo, host,
production reference branch, source/target branches, head sha, the command to
fetch the diff, and candidate CI commands read from the repo's pipeline files.
Reads only (gh / az repos / git); safe to run unattended.

Usage:
    python resolve_target.py --input "https://github.com/owner/repo/pull/123"
    python resolve_target.py --input "owner/repo#123" [--repo-path <path>]
    python resolve_target.py --input "https://dev.azure.com/org/proj/_git/repo/pullrequest/45"
    python resolve_target.py --input "<branch>" --repo-path <path> --prod-ref develop
    python resolve_target.py --fixture fixture.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402

_GH_URL = re.compile(r"github\.com/([^/]+)/([^/]+)/(pull|issues)/(\d+)")
_GH_SHORT = re.compile(r"^([^/\s]+)/([^/\s#]+)#(\d+)$")
_ADO_URL = re.compile(r"dev\.azure\.com/([^/]+)/([^/]+)/_git/([^/]+)/pullrequest/(\d+)")

_CI_HINTS = ("coverage run", "unittest discover", "pytest", "bundle validate",
             "coverage report", "tox", "nox")


def discover_ci(repo_path: str | None) -> list:
    if not repo_path or not os.path.isdir(repo_path):
        return []
    candidates: list = []
    patterns = [".github/workflows/*.yml", ".github/workflows/*.yaml",
                "azure-pipelines*.yml", "azure-pipelines*.yaml", "**/azure-pipelines*.yml"]
    seen = set()
    for pat in patterns:
        for fp in glob.glob(os.path.join(repo_path, pat), recursive=True):
            if fp in seen:
                continue
            seen.add(fp)
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    for line in fh:
                        low = line.lower()
                        if any(h in low for h in _CI_HINTS):
                            cmd = line.strip().lstrip("-").strip().strip('"').strip()
                            if cmd and cmd not in [x["command"] for x in candidates]:
                                candidates.append({"command": cmd,
                                                   "file": os.path.relpath(fp, repo_path)})
            except OSError:
                continue
    return candidates[:20]


def resolve_github_pr(owner: str, repo: str, number: str) -> dict:
    full = f"{owner}/{repo}"
    view = c.run_cmd(["gh", "pr", "view", number, "--repo", full, "--json",
                      "number,title,state,baseRefName,headRefName,headRefOid,url,mergeable"])
    out = {}
    if view["returncode"] == 0:
        try:
            out = json.loads(view["stdout"])
        except ValueError:
            pass
    return {
        "host": "github", "repo": full, "kind": "pr", "number": int(number),
        "title": out.get("title", ""), "state": out.get("state", ""),
        "target_branch": out.get("baseRefName", ""),
        "source_branch": out.get("headRefName", ""),
        "head_sha": out.get("headRefOid", ""), "url": out.get("url", ""),
        "mergeable": out.get("mergeable", ""),
        "diff_command": f"gh pr diff {number} --repo {full}",
        "resolved": view["returncode"] == 0,
        "note": "" if view["returncode"] == 0 else view["stderr"].strip()[:200],
    }


def resolve_github_issue(owner: str, repo: str, number: str) -> dict:
    full = f"{owner}/{repo}"
    view = c.run_cmd(["gh", "issue", "view", number, "--repo", full, "--json",
                      "number,title,state,labels,url"])
    out = {}
    if view["returncode"] == 0:
        try:
            out = json.loads(view["stdout"])
        except ValueError:
            pass
    return {"host": "github", "repo": full, "kind": "issue", "number": int(number),
            "title": out.get("title", ""), "state": out.get("state", ""),
            "url": out.get("url", ""), "resolved": view["returncode"] == 0,
            "note": "" if view["returncode"] == 0 else view["stderr"].strip()[:200]}


def resolve_ado_pr(org: str, project: str, repo: str, number: str) -> dict:
    org_url = f"https://dev.azure.com/{org}"
    show = c.run_cmd(["az", "repos", "pr", "show", "--id", number,
                      "--org", org_url, "--output", "json"])
    out = {}
    if show["returncode"] == 0:
        try:
            out = json.loads(show["stdout"])
        except ValueError:
            pass
    src = (out.get("sourceRefName") or "").replace("refs/heads/", "")
    tgt = (out.get("targetRefName") or "").replace("refs/heads/", "")
    return {"host": "azure_devops", "org": org, "project": project, "repo": repo,
            "kind": "pr", "number": int(number),
            "title": out.get("title", ""), "state": out.get("status", ""),
            "source_branch": src, "target_branch": tgt,
            "head_sha": (out.get("lastMergeSourceCommit", {}) or {}).get("commitId", ""),
            "diff_note": "Azure DevOps has no raw patch; fetch the refs locally and "
                         "use git diff <base>..<source>",
            "resolved": show["returncode"] == 0,
            "note": "" if show["returncode"] == 0 else show["stderr"].strip()[:200]}


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve a PR/issue/branch into a target.")
    ap.add_argument("--input", required=False)
    ap.add_argument("--repo-path")
    ap.add_argument("--prod-ref", default=os.environ.get("ADRA_PROD_REF_BRANCH", "main"))
    ap.add_argument("--fixture")
    args = ap.parse_args()

    fx = c.load_fixture(args.fixture)
    if fx is not None:
        fx["ci_candidates"] = discover_ci(args.repo_path)
        return c.emit(c.result("resolve_target", True, [], fx))

    if not args.input:
        return c.emit(c.result("resolve_target", False, reason="pass --input or --fixture"))

    text = args.input.strip()
    target: dict
    m = _ADO_URL.search(text)
    if m:
        target = resolve_ado_pr(*m.groups())
    elif _GH_URL.search(text):
        owner, repo, kind, num = _GH_URL.search(text).groups()
        repo = repo.replace(".git", "")
        target = (resolve_github_pr(owner, repo, num) if kind == "pull"
                  else resolve_github_issue(owner, repo, num))
    elif _GH_SHORT.match(text):
        owner, repo, num = _GH_SHORT.match(text).groups()
        target = resolve_github_pr(owner, repo, num)
    else:
        target = {"host": "local", "kind": "branch", "source_branch": text,
                  "target_branch": args.prod_ref, "resolved": bool(args.repo_path),
                  "note": "" if args.repo_path else "provide --repo-path for a bare branch"}

    target.setdefault("target_branch", args.prod_ref)
    target["prod_ref"] = target.get("target_branch") or args.prod_ref
    target["ci_candidates"] = discover_ci(args.repo_path)
    return c.emit(c.result("resolve_target", True, [], target))


if __name__ == "__main__":
    raise SystemExit(main())
