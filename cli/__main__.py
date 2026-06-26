"""ADRA command-line interface.

Run a capability through the adversarial loop and print the artifacts — over a provided
intake, a **real GitHub PR**, or the offline **emulator**. Offline by default (the
deterministic ``mock`` provider — no API key); set ``ADRA_PROVIDER`` + a key for the
semantic layer, and ``--external`` to let tools/connectors call out (default: read-only).
Point ADRA at a client's governance suite with ``ADRA_CLIENT_DIR``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adra import Orchestrator, load_settings


def _read(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8") if path else ""


def _print_run(state, record) -> int:
    for name, body in state.artifacts.items():
        print(f"\n===== {name} =====\n{body}")
    if state.critic_history:
        blockers = state.critic_history[-1].blocking
        if blockers:
            print("\n----- blocking findings -----")
            for f in blockers:
                fd = f.to_dict()
                print(f"  [{fd.get('severity')}] {fd.get('category')}: {fd.get('message')}")
    print(f"\n[decision: {state.decision}]  run record: {record.run_id}.json")
    return 0 if state.decision == "accepted" else 2


def _run(skill: str, intake: dict, external: bool, **overrides) -> int:
    settings = load_settings(allow_external_calls=external, **overrides)
    state, record = Orchestrator(settings).run(skill, intake)
    return _print_run(state, record)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="adra", description="ADRA — Adversarial Dev Review Agent")
    p.add_argument("--external", action="store_true",
                   help="allow deterministic tools/connectors to call out (default: read-only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    rv = sub.add_parser("review", help="review a unified diff")
    rv.add_argument("diff", help="path to a .diff/.patch file")
    rv.add_argument("--ci-command", default=None, help="exact CI command to reproduce")

    pe = sub.add_parser("pr-eval", help="evaluate a branch/PR")
    pe.add_argument("--source", required=True, help="source branch")
    pe.add_argument("--target", default="main", help="target/integration branch")
    pe.add_argument("--repo", default=None, help="path to the local git repo")

    ex = sub.add_parser("experiment", help="run a validation experiment from a JSON spec")
    ex.add_argument("spec", help="path to a JSON intake spec")

    im = sub.add_parser("improve", help="propose a minimum-functional improvement")
    im.add_argument("context", help="what to improve (text)")

    do = sub.add_parser("document", help="render a doc from a run record / context")
    do.add_argument("--type", default="pr", help="page type: pr | experiment | methodology")
    do.add_argument("--title", default="", help="document title")

    de = sub.add_parser("decide", help="route analysis for a decision (human-owned)")
    de.add_argument("problem", help="the decision to make")
    de.add_argument("routes", nargs="+", help="candidate routes")

    gh = sub.add_parser("github-review", help="review a REAL GitHub PR (read-only by default)")
    gh.add_argument("repo", help="owner/repo")
    gh.add_argument("pr", type=int, help="PR number")
    gh.add_argument("--skill", default="code_review", choices=["code_review", "pr_eval"])
    gh.add_argument("--post", action="store_true",
                    help="post the verdict as a PR comment (requires --external + a token)")

    em = sub.add_parser("emu", help="run against the offline emulator (synthetic multi-industry PRs)")
    em.add_argument("action", choices=["list", "review"])
    em.add_argument("pr", nargs="?", type=int, help="emulator PR number (for review)")
    em.add_argument("--skill", default="pr_eval", choices=["code_review", "pr_eval"])
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ext = args.external

    if args.cmd == "review":
        intake: dict = {"diff": _read(args.diff)}
        if args.ci_command:
            intake["ci_command"] = args.ci_command
        return _run("code_review", intake, ext)
    if args.cmd == "pr-eval":
        intake = {"source_branch": args.source, "target_branch": args.target}
        over = {"repo_path": Path(args.repo)} if args.repo else {}
        return _run("pr_eval", intake, ext, **over)
    if args.cmd == "experiment":
        return _run("experiment", json.loads(_read(args.spec)), ext)
    if args.cmd == "improve":
        return _run("improve", {"context": args.context}, ext)
    if args.cmd == "document":
        return _run("document", {"doc_type": args.type, "title": args.title}, ext)
    if args.cmd == "decide":
        return _run("decide", {"problem": args.problem, "routes": args.routes}, ext)

    if args.cmd == "github-review":
        from adra.connectors import code_review_intake, get_repo_provider, pr_eval_intake
        owner, _, repo = args.repo.partition("/")
        prov = get_repo_provider({"provider": "github", "owner": owner, "repo": repo,
                                  "allow_external": ext})
        pr = prov.get_pull_request(args.pr)
        print(f"PR #{pr.number}: {pr.title}  [{pr.source_branch} -> {pr.target_branch}]  "
              f"by {pr.author}  ({len(pr.diff)} diff chars, {len(pr.files)} files)")
        intake = code_review_intake(pr) if args.skill == "code_review" else pr_eval_intake(pr)
        settings = load_settings(allow_external_calls=ext)
        state, record = Orchestrator(settings).run(args.skill, intake)
        code = _print_run(state, record)
        if args.post:
            if not ext:
                print("\n(--post needs --external to write to GitHub; skipped)")
            else:
                body = next(iter(state.artifacts.values()), "ADRA review")
                print("\nposted PR comment:", prov.comment_on_pull_request(pr.number, body))
        return code

    if args.cmd == "emu":
        from adra.connectors import code_review_intake, get_repo_provider, pr_eval_intake
        prov = get_repo_provider({"provider": "emulator"})
        if args.action == "list":
            for pr in prov.list_pull_requests():
                print(f"#{pr.number}  {pr.title}")
            return 0
        if args.pr is None:
            print("emu review <pr> — pass a PR number (see `adra emu list`)")
            return 1
        pr = prov.get_pull_request(args.pr)
        print(f"emulator PR #{pr.number}: {pr.title}")
        intake = code_review_intake(pr) if args.skill == "code_review" else pr_eval_intake(pr)
        return _run(args.skill, intake, ext)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
