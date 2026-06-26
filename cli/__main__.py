"""ADRA command-line interface.

``adra <skill> ...`` runs one capability through the adversarial loop and prints the
artifacts. Offline by default (the deterministic ``mock`` provider — no API key); set
``ADRA_PROVIDER=anthropic`` + ``ANTHROPIC_API_KEY`` for the semantic layer, and
``--external`` to let the deterministic tools actually call git / CI / the warehouse
(the default is read-only / dry-run). Point ADRA at a client's governance suite with
``ADRA_CLIENT_DIR``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adra import Orchestrator, load_settings


def _read(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8") if path else ""


def _run(skill: str, intake: dict, external: bool) -> int:
    settings = load_settings(allow_external_calls=external)
    state, record = Orchestrator(settings).run(skill, intake)
    for name, body in state.artifacts.items():
        print(f"\n===== {name} =====\n{body}")
    print(f"\n[decision: {state.decision}]  run record: {record.run_id}.json")
    return 0 if state.decision == "accepted" else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="adra", description="ADRA — Adversarial Dev Review Agent")
    p.add_argument("--external", action="store_true",
                   help="allow deterministic tools to call git / CI / the warehouse (default: read-only)")
    sub = p.add_subparsers(dest="skill", required=True)

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
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ext = args.external

    if args.skill == "review":
        intake: dict = {"diff": _read(args.diff)}
        if args.ci_command:
            intake["ci_command"] = args.ci_command
        return _run("code_review", intake, ext)
    if args.skill == "pr-eval":
        intake = {"source_branch": args.source, "target_branch": args.target}
        if args.repo:
            intake["repo"] = args.repo
        return _run("pr_eval", intake, ext)
    if args.skill == "experiment":
        return _run("experiment", json.loads(_read(args.spec)), ext)
    if args.skill == "improve":
        return _run("improve", {"context": args.context}, ext)
    if args.skill == "document":
        return _run("document", {"doc_type": args.type, "title": args.title}, ext)
    if args.skill == "decide":
        return _run("decide", {"problem": args.problem, "routes": args.routes}, ext)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
