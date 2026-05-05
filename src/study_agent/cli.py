from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cleanup import remove_all_caches, remove_temp_artifacts
from .codex_client import run_codex
from .config import load_config, save_config, validate_model_name, with_model
from .github_check import DEFAULT_REPO_URL, check_github_clone
from .pipeline import (
    execute_card_build,
    execute_export_note,
    execute_paper_attach,
    execute_workspace_index,
    execute_workspace_question,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            return run_analyze(args)
        if args.command == "index":
            return run_index(args)
        if args.command == "paper":
            return run_paper(args)
        if args.command == "ask":
            return run_ask(args)
        if args.command == "card":
            return run_card(args)
        if args.command == "export":
            return run_export(args)
        if args.command == "config":
            return run_config(args)
        if args.command == "codex":
            return run_codex_command(args)
        if args.command == "cleanup":
            return run_cleanup(args)
        if args.command == "github":
            return run_github_command(args)
    except Exception as exc:
        print(f"study-agent: error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="study-agent", description="Code-first VLA research copilot")
    subparsers = parser.add_subparsers(dest="command")

    analyze = subparsers.add_parser("analyze", help="Deprecated wrapper: index repo, optionally attach paper, ask overview, export note")
    analyze.add_argument("--paper", help="Local PDF or local text/markdown file")
    analyze.add_argument("--repo", required=True, help="GitHub URL or local repository path")
    analyze.add_argument("--focus", default="", help="Comma-separated optional retrieval hints")
    analyze.add_argument("--out", required=True, help="Markdown output path")
    analyze.add_argument("--engine", choices=["codex", "offline"], default="offline")

    index = subparsers.add_parser("index", help="Index a repository into a research workspace")
    index.add_argument("--repo", required=True, help="GitHub URL or local repository path")
    index.add_argument("--workspace", required=True, help="Workspace name")

    paper = subparsers.add_parser("paper", help="Manage workspace papers")
    paper_sub = paper.add_subparsers(dest="paper_command")
    paper_attach = paper_sub.add_parser("attach", help="Attach a paper to a workspace")
    paper_attach.add_argument("--workspace", required=True)
    paper_attach.add_argument("--paper", required=True)

    ask = subparsers.add_parser("ask", help="Ask a research question against a workspace")
    ask.add_argument("--workspace", required=True)
    ask.add_argument("--question", required=True)

    card = subparsers.add_parser("card", help="Build a reusable card from the latest workspace answer")
    card_sub = card.add_subparsers(dest="card_command")
    card_build = card_sub.add_parser("build", help="Build a card artifact")
    card_build.add_argument("--workspace", required=True)
    card_build.add_argument("--topic", required=True)

    export = subparsers.add_parser("export", help="Export a workspace note")
    export_sub = export.add_subparsers(dest="export_command")
    export_note = export_sub.add_parser("note", help="Export the workspace note")
    export_note.add_argument("--workspace", required=True)
    export_note.add_argument("--out", help="Optional output path")

    config = subparsers.add_parser("config", help="Show or update app config")
    config_sub = config.add_subparsers(dest="config_command")
    config_sub.add_parser("show", help="Show current config")
    set_model = config_sub.add_parser("set-model", help="Set the default Codex model")
    set_model.add_argument("model", choices=["gpt-5.4", "gpt-5.5"])

    codex = subparsers.add_parser("codex", help="Codex integration helpers")
    codex_sub = codex.add_subparsers(dest="codex_command")
    codex_test = codex_sub.add_parser("test", help="Check Codex CLI/auth by asking for OK")
    codex_test.add_argument("--model", choices=["gpt-5.4", "gpt-5.5"], help="Override model for this test")

    cleanup = subparsers.add_parser("cleanup", help="Remove temporary artifacts")
    cleanup.add_argument("--target", choices=["temp", "all"], default="temp")

    github = subparsers.add_parser("github", help="GitHub clone helpers")
    github_sub = github.add_subparsers(dest="github_command")
    github_test = github_sub.add_parser("test", help="Check whether git clone works with a shallow clone probe")
    github_test.add_argument("--repo-url", default=DEFAULT_REPO_URL)

    return parser


def run_analyze(args: argparse.Namespace) -> int:
    hints = [item.strip() for item in args.focus.split(",") if item.strip()]
    workspace_name = Path(args.out).stem or Path(args.repo).stem or "workspace"
    index_result = execute_workspace_index(args.repo, workspace_name)
    if args.paper:
        attachment = execute_paper_attach(index_result.manifest.workspace_id, args.paper)
        print(f"Attached paper: {attachment.title}")
    overview_question = "Explain the repository architecture."
    if hints:
        overview_question = f"Explain the repository architecture and implementation evidence for: {', '.join(hints)}."
    question_result = execute_workspace_question(index_result.manifest.workspace_id, overview_question)
    output_path = execute_export_note(index_result.manifest.workspace_id, Path(args.out))
    print("`analyze` is deprecated. Prefer `index`, `paper attach`, `ask`, and `export note`.")
    print(f"Workspace: {index_result.manifest.workspace_id}")
    print(f"Latest answer: {question_result.answer.confidence}")
    print(f"Wrote {output_path}")
    return 0


def run_index(args: argparse.Namespace) -> int:
    result = execute_workspace_index(args.repo, args.workspace)
    print(f"Indexed workspace: {result.manifest.workspace_id}")
    print(f"Repo path: {result.manifest.repo_path}")
    print(f"Graph nodes: {result.manifest.graph_node_count}")
    print(f"Graph edges: {result.manifest.graph_edge_count}")
    return 0


def run_paper(args: argparse.Namespace) -> int:
    if args.paper_command != "attach":
        raise ValueError("Missing paper command.")
    attachment = execute_paper_attach(args.workspace, args.paper)
    print(f"Attached paper `{attachment.title}` to workspace `{args.workspace}`")
    return 0


def run_ask(args: argparse.Namespace) -> int:
    result = execute_workspace_question(args.workspace, args.question)
    answer = result.answer
    print(f"Question: {answer.question}")
    print(f"Type: {answer.answer_type}")
    print(f"Confidence: {answer.confidence}")
    print("")
    print(answer.answer)
    if answer.uncertainty:
        print("")
        print("Uncertainty:")
        for item in answer.uncertainty:
            print(f"- {item}")
    if answer.follow_up_questions:
        print("")
        print("Follow-up:")
        for item in answer.follow_up_questions:
            print(f"- {item}")
    return 0


def run_card(args: argparse.Namespace) -> int:
    if args.card_command != "build":
        raise ValueError("Missing card command.")
    card = execute_card_build(args.workspace, args.topic)
    print(f"Built {card.card_type}: {card.card_id}")
    return 0


def run_export(args: argparse.Namespace) -> int:
    if args.export_command != "note":
        raise ValueError("Missing export command.")
    target = Path(args.out) if args.out else None
    result = execute_export_note(args.workspace, target)
    print(f"Wrote {result}")
    return 0


def run_config(args: argparse.Namespace) -> int:
    config = load_config()
    if args.config_command == "show":
        print(f"auth_path: {config.auth_path}")
        print(f"api_url: {config.api_url}")
        print(f"model: {config.model}")
        print(f"timeout_seconds: {config.timeout_seconds}")
        print(f"zotero_data_dir: {config.zotero_data_dir}")
        return 0
    if args.config_command == "set-model":
        updated = with_model(config, validate_model_name(args.model))
        save_config(updated)
        print(f"Updated default model: {updated.model}")
        return 0
    raise ValueError("Missing config command.")


def run_codex_command(args: argparse.Namespace) -> int:
    if args.codex_command != "test":
        raise ValueError("Missing codex command.")
    config = with_model(load_config(), getattr(args, "model", None))
    result = run_codex("Reply exactly: OK", config, Path.cwd(), Path(".study-agent") / "codex-test.md")
    print(result.strip())
    return 0


def run_cleanup(args: argparse.Namespace) -> int:
    removed = remove_all_caches() if args.target == "all" else remove_temp_artifacts()
    if not removed:
        print("Nothing to clean.")
        return 0
    print("Cleaned:")
    for path in removed:
        print(f"- {path}")
    return 0


def run_github_command(args: argparse.Namespace) -> int:
    if args.github_command != "test":
        raise ValueError("Missing github command.")
    result = check_github_clone(args.repo_url)
    print(result.summary)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
