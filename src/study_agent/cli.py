from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from .analyzer.code import build_code_map, build_open_questions, build_reading_path
from .analyzer.paper import analyze_paper
from .cleanup import remove_all_caches, remove_temp_artifacts
from .codex_client import CodexUnavailable, run_codex
from .config import load_config, save_config, validate_model_name, with_model
from .github_check import DEFAULT_REPO_URL, check_github_clone
from .models import StudyRequest
from .pipeline import execute_analysis
from .prompt_builder import build_reflection_prompt
from .profile import apply_feedback, apply_preset, load_profile, save_profile
from .runtime_env import configure_runtime_environment
from .taste_memory import append_taste_memory
from .tui import run_tui


def main(argv: list[str] | None = None) -> int:
    configure_runtime_environment()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            return run_analyze(args)
        if args.command == "profile":
            return run_profile(args)
        if args.command == "config":
            return run_config(args)
        if args.command == "feedback":
            return run_feedback(args)
        if args.command == "codex":
            return run_codex_command(args)
        if args.command == "cleanup":
            return run_cleanup(args)
        if args.command == "github":
            return run_github_command(args)
        if args.command == "tui":
            return run_tui()
    except Exception as exc:
        print(f"study-agent: error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="study-agent", description="VLA paper-to-code study agent")
    subparsers = parser.add_subparsers(dest="command")

    analyze = subparsers.add_parser("analyze", help="Analyze a paper and repository")
    analyze.add_argument("--paper", help="Paper URL, local PDF, or local text/markdown file")
    analyze.add_argument("--zotero-title", help="Find paper PDF by title in Zotero")
    analyze.add_argument("--repo", required=True, help="GitHub URL or local repository path")
    analyze.add_argument("--focus", default="", help="Comma-separated focus terms")
    analyze.add_argument("--out", required=True, help="Markdown output path")
    analyze.add_argument("--mode", default="paper-aligned")
    analyze.add_argument("--engine", choices=["codex", "offline"], default="codex")
    analyze.add_argument("--model", choices=["gpt-5.4", "gpt-5.5"], help="Override model for this run")
    analyze.add_argument(
        "--cleanup",
        choices=["none", "temp", "repo", "all"],
        default="none",
        help="Clean temporary artifacts after analysis: temp=PDF cache, repo=remote clone cache, all=both",
    )

    profile = subparsers.add_parser("profile", help="Show or update taste profile")
    profile_sub = profile.add_subparsers(dest="profile_command")
    profile_sub.add_parser("show", help="Show current profile")
    update = profile_sub.add_parser("update", help="Update profile")
    update.add_argument("--preset", default="default", help="Preset name")

    config = subparsers.add_parser("config", help="Show or update app config")
    config_sub = config.add_subparsers(dest="config_command")
    config_sub.add_parser("show", help="Show current config")
    set_model = config_sub.add_parser("set-model", help="Set the default Codex model")
    set_model.add_argument("model", choices=["gpt-5.4", "gpt-5.5"])

    feedback = subparsers.add_parser("feedback", help="Apply explicit taste feedback")
    feedback_sub = feedback.add_subparsers(dest="feedback_command")
    apply = feedback_sub.add_parser("apply", help="Apply feedback from a note")
    apply.add_argument("--from", dest="from_path", required=True, help="Study note path")
    apply.add_argument("--note", default="", help="Short feedback text")

    codex = subparsers.add_parser("codex", help="Codex integration helpers")
    codex_sub = codex.add_subparsers(dest="codex_command")
    codex_test = codex_sub.add_parser("test", help="Check Codex CLI/auth by asking for OK")
    codex_test.add_argument("--model", choices=["gpt-5.4", "gpt-5.5"], help="Override model for this test")

    cleanup = subparsers.add_parser("cleanup", help="Remove study-agent temporary artifacts")
    cleanup.add_argument("--target", choices=["temp", "all"], default="temp")

    github = subparsers.add_parser("github", help="GitHub clone helpers")
    github_sub = github.add_subparsers(dest="github_command")
    github_test = github_sub.add_parser("test", help="Check whether git clone works with a shallow clone probe")
    github_test.add_argument("--repo-url", default=DEFAULT_REPO_URL)

    subparsers.add_parser("tui", help="Launch the interactive PowerShell wizard")

    return parser


def run_analyze(args: argparse.Namespace) -> int:
    focus = [item.strip() for item in args.focus.split(",") if item.strip()]
    request = StudyRequest(
        paper_source=args.paper,
        repo_source=args.repo,
        focus=focus,
        output_path=Path(args.out),
        mode=args.mode,
        engine=args.engine,
        zotero_title=args.zotero_title,
        model=args.model,
    )
    config = with_model(load_config(), args.model)
    result = execute_analysis(request, cleanup_mode=args.cleanup, config=config)
    print(f"Wrote {result.output_path}")
    if result.cleaned:
        print("Cleaned:")
        for path in result.cleaned:
            print(f"- {path}")
    return 0


def run_config(args: argparse.Namespace) -> int:
    config = load_config()
    if args.config_command == "show":
        print(f"auth_path: {config.auth_path}")
        print(f"api_url: {config.api_url}")
        print(f"model: {config.model}")
        print(f"timeout_seconds: {config.timeout_seconds}")
        print(f"max_evidence_chars: {config.max_evidence_chars}")
        print(f"max_history_examples: {config.max_history_examples}")
        print(f"zotero_data_dir: {config.zotero_data_dir}")
        return 0
    if args.config_command == "set-model":
        updated = with_model(config, validate_model_name(args.model))
        save_config(updated)
        print(f"Updated default model: {updated.model}")
        return 0
    raise ValueError("Missing config command.")


def run_profile(args: argparse.Namespace) -> int:
    profile = load_profile()
    if args.profile_command == "show":
        for key, value in asdict(profile).items():
            print(f"{key}: {value}")
        return 0
    if args.profile_command == "update":
        profile = apply_preset(profile, args.preset)
        save_profile(profile)
        print(f"Updated profile with preset: {args.preset}")
        return 0
    raise ValueError("Missing profile command.")


def run_feedback(args: argparse.Namespace) -> int:
    if args.feedback_command != "apply":
        raise ValueError("Missing feedback command.")
    profile = load_profile()
    note_text = Path(args.from_path).read_text(encoding="utf-8", errors="replace") if args.from_path else ""
    feedback_text = "\n".join([note_text[-3000:], args.note])
    profile = apply_feedback(profile, feedback_text)
    save_profile(profile)
    config = load_config()
    memory_text = args.note.strip()
    try:
        prompt = build_reflection_prompt(note_text, args.note)
        memory_text = run_codex(prompt, config, Path.cwd(), Path(".study-agent") / "feedback-reflection.md")
    except CodexUnavailable:
        pass
    append_taste_memory(memory_text)
    print("Updated profile from explicit feedback.")
    return 0


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
