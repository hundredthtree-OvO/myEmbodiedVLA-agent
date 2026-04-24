from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from .analyzer.code import build_code_map, build_open_questions, build_reading_path
from .analyzer.paper import analyze_paper
from .cleanup import cleanup_after_analyze, remove_all_caches, remove_pdf_cache
from .codex_client import CodexUnavailable, assert_codex_ready, run_codex
from .composer import compose_markdown
from .config import load_config
from .ingest import ingest_paper, ingest_repo
from .models import EvidencePack, StudyArtifact, StudyRequest
from .planner import build_plan
from .prompt_builder import build_reflection_prompt, build_study_prompt
from .profile import apply_feedback, apply_preset, load_profile, save_profile
from .session_store import create_session_dir, save_session
from .taste_memory import append_taste_memory
from .zotero import find_zotero_item


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            return run_analyze(args)
        if args.command == "profile":
            return run_profile(args)
        if args.command == "feedback":
            return run_feedback(args)
        if args.command == "codex":
            return run_codex_command(args)
        if args.command == "cleanup":
            return run_cleanup(args)
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

    feedback = subparsers.add_parser("feedback", help="Apply explicit taste feedback")
    feedback_sub = feedback.add_subparsers(dest="feedback_command")
    apply = feedback_sub.add_parser("apply", help="Apply feedback from a note")
    apply.add_argument("--from", dest="from_path", required=True, help="Study note path")
    apply.add_argument("--note", default="", help="Short feedback text")

    codex = subparsers.add_parser("codex", help="Codex integration helpers")
    codex_sub = codex.add_subparsers(dest="codex_command")
    codex_sub.add_parser("test", help="Check Codex CLI/auth by asking for OK")

    cleanup = subparsers.add_parser("cleanup", help="Remove study-agent temporary artifacts")
    cleanup.add_argument("--target", choices=["temp", "all"], default="temp")

    return parser


def run_analyze(args: argparse.Namespace) -> int:
    if not args.paper and not args.zotero_title:
        raise ValueError("Either --paper or --zotero-title is required.")

    config = load_config()
    zotero_item = None
    paper_source = args.paper
    if args.zotero_title:
        zotero_item = find_zotero_item(args.zotero_title, config.zotero_data_dir or Path("E:/zoteroData"))
        if not paper_source and zotero_item.pdf_path:
            paper_source = str(zotero_item.pdf_path)
    if not paper_source:
        raise ValueError("Zotero item was found, but no PDF attachment path was available.")

    focus = [item.strip() for item in args.focus.split(",") if item.strip()]
    request = StudyRequest(
        paper_source=paper_source,
        repo_source=args.repo,
        focus=focus,
        output_path=Path(args.out),
        mode=args.mode,
        engine=args.engine,
        zotero_title=args.zotero_title,
    )
    profile = load_profile()
    plan = build_plan(request, profile)
    paper = ingest_paper(request.paper_source)
    repo = ingest_repo(request.repo_source, plan.focus_terms)
    concept_cards = analyze_paper(paper, plan)
    code_map = build_code_map(repo, concept_cards, plan)
    reading_path = build_reading_path(repo, plan)
    open_questions = build_open_questions(repo, code_map, plan)
    artifact = StudyArtifact(
        request=request,
        paper=paper,
        repo=repo,
        profile=profile,
        summary=f"{paper.title} aligned against {repo.path.name}",
        concept_cards=concept_cards,
        code_map=code_map,
        reading_path=reading_path,
        open_questions=open_questions,
    )

    evidence = EvidencePack(request=request, paper=paper, repo=repo, profile=profile, zotero_item=zotero_item)
    markdown = _render(artifact, evidence, args.engine, config)
    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    request.output_path.write_text(markdown, encoding="utf-8")
    removed = cleanup_after_analyze(args.cleanup, request.repo_source)
    print(f"Wrote {request.output_path}")
    if removed:
        print("Cleaned:")
        for path in removed:
            print(f"- {path}")
    return 0


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
    config = load_config()
    result = run_codex("Reply exactly: OK", config, Path.cwd(), Path(".study-agent") / "codex-test.md")
    print(result.strip())
    return 0


def run_cleanup(args: argparse.Namespace) -> int:
    removed = remove_all_caches() if args.target == "all" else remove_pdf_cache()
    if not removed:
        print("Nothing to clean.")
        return 0
    print("Cleaned:")
    for path in removed:
        print(f"- {path}")
    return 0


def _render(artifact: StudyArtifact, evidence: EvidencePack, engine: str, config) -> str:
    if engine == "codex":
        assert_codex_ready(config)
        session_dir = create_session_dir()
        prompt = build_study_prompt(evidence, config.max_evidence_chars)
        output = run_codex(prompt, config, Path.cwd(), session_dir / "codex-output.md")
        save_session(session_dir, evidence, prompt, output)
        return output
    return compose_markdown(artifact)


if __name__ == "__main__":
    raise SystemExit(main())
