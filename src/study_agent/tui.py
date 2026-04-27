from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .cleanup import remove_all_caches, remove_temp_artifacts
from .codex_client import CodexUnavailable, assert_codex_ready, run_codex
from .config import SUPPORTED_MODELS, load_config, with_model
from .github_check import DEFAULT_REPO_URL, check_github_clone
from .models import StudyRequest
from .paper_workspace import build_paper_slug
from .pipeline import execute_analysis
from .profile import load_profile
from .progress import STAGES, TerminalProgress
from .runtime_env import RuntimeEnvironment, configure_runtime_environment
from .session_store import latest_session_dir


@dataclass(frozen=True)
class TuiDefaults:
    paper: str
    zotero_title: str
    repo: str
    focus: str
    model: str
    cleanup: str
    mode: str
    engine: str


def run_tui() -> int:
    env = configure_runtime_environment()
    while True:
        _print_header(env)
        print("1. New Analysis")
        print("2. Codex Test")
        print("3. GitHub Clone Test")
        print("4. Profile Show")
        print("5. Cleanup Temp")
        print("6. Cleanup All")
        print("7. Open Last Session")
        print("Q. Quit")
        choice = input("\nSelect an action: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            print("Bye.")
            return 0
        if choice == "1":
            _run_analysis_wizard(env)
        elif choice == "2":
            _run_codex_test()
        elif choice == "3":
            _run_github_test()
        elif choice == "4":
            _show_profile()
        elif choice == "5":
            _run_cleanup("temp")
        elif choice == "6":
            _run_cleanup("all")
        elif choice == "7":
            _open_last_session()
        else:
            print("Unknown action.\n")


def default_form_values() -> TuiDefaults:
    config = load_config()
    return TuiDefaults(
        paper="",
        zotero_title="",
        repo=".",
        focus="",
        model=config.model,
        cleanup="none",
        mode="paper-aligned",
        engine="codex",
    )


def cleanup_choices() -> list[str]:
    return ["none", "temp", "repo", "all"]


def next_step(current_step: str) -> str | None:
    steps = ["input", "repo", "focus", "cleanup", "run"]
    try:
        index = steps.index(current_step)
    except ValueError:
        return None
    return steps[index + 1] if index + 1 < len(steps) else None


def _print_header(env: RuntimeEnvironment) -> None:
    config = load_config()
    codex_status = "ready"
    try:
        assert_codex_ready(config)
    except CodexUnavailable as exc:
        codex_status = f"unavailable ({exc})"

    print("\n" + "=" * 72)
    print("VLA Study Agent TUI")
    print("=" * 72)
    print(f"Workspace : {env.workspace_root}")
    print(f"UV cache  : {env.uv_cache_dir}")
    print(f"Codex     : {codex_status}")
    print(f"Model     : {config.model}")
    print(f"Zotero    : {config.zotero_data_dir}")
    print(f"Stages    : {', '.join(STAGES)}")
    print("=" * 72)


def _run_analysis_wizard(env: RuntimeEnvironment) -> None:
    defaults = default_form_values()

    print("\nStep 1/5 - Input source")
    source_mode = _prompt_with_default("Source mode [zotero/paper]", "paper").lower()

    zotero_title = ""
    paper = ""
    if source_mode == "zotero":
        zotero_title = _prompt_with_default("Zotero title", defaults.zotero_title)
        paper = _prompt_with_default("Paper path override (optional)", "")
    else:
        paper = _prompt_with_default("Paper path", defaults.paper)

    print("\nStep 2/5 - Repository")
    repo = _prompt_with_default("Repo path or GitHub URL", defaults.repo or ".")

    print("\nStep 3/5 - Focus")
    focus_text = _prompt_with_default("Focus (comma-separated)", defaults.focus)
    focus = [item.strip() for item in focus_text.split(",") if item.strip()]

    out = _fixed_output_path(paper, zotero_title)

    print("\nStep 4/5 - Cleanup")
    model = _prompt_with_default(f"Model [{'/'.join(SUPPORTED_MODELS)}]", defaults.model)
    while model not in SUPPORTED_MODELS:
        model = _prompt_with_default(f"Model [{'/'.join(SUPPORTED_MODELS)}]", defaults.model)
    cleanup = _prompt_with_default("Cleanup [none/temp/repo/all]", defaults.cleanup)
    while cleanup not in cleanup_choices():
        cleanup = _prompt_with_default("Cleanup [none/temp/repo/all]", "none")

    print("\nStep 5/5 - Run")
    print(f"- paper: {paper or '(resolved from Zotero)'}")
    print(f"- zotero_title: {zotero_title or '(none)'}")
    print(f"- repo: {repo}")
    print(f"- focus: {', '.join(focus) or '(none)'}")
    print(f"- output: {out} (fixed)")
    print(f"- model: {model}")
    print(f"- cleanup: {cleanup}")
    confirm = _prompt_with_default("Run analysis now? [y/n]", "y").lower()
    if confirm != "y":
        print("Canceled.\n")
        return

    request = StudyRequest(
        paper_source=paper or None,
        repo_source=repo,
        focus=focus,
        output_path=Path(out),
        mode="paper-aligned",
        engine="codex",
        zotero_title=zotero_title or None,
        model=model,
    )
    progress = TerminalProgress()
    result = execute_analysis(request, cleanup_mode=cleanup, progress=progress)
    print(f"\nSaved note: {result.output_path}")
    if result.session_dir:
        print(f"Session: {result.session_dir}")
    if result.cleaned:
        print("Cleaned:")
        for path in result.cleaned:
            print(f"- {path}")
    print("")


def _run_codex_test() -> None:
    base_config = load_config()
    model = _prompt_with_default(f"Model [{'/'.join(SUPPORTED_MODELS)}]", base_config.model)
    while model not in SUPPORTED_MODELS:
        model = _prompt_with_default(f"Model [{'/'.join(SUPPORTED_MODELS)}]", base_config.model)
    config = with_model(base_config, model)
    result = run_codex("Reply exactly: OK", config, Path.cwd(), Path(".study-agent") / "codex-test.md")
    print(f"\nCodex test result ({config.model}): {result.strip()}\n")


def _run_github_test() -> None:
    repo_url = _prompt_with_default("GitHub repo URL", DEFAULT_REPO_URL)
    result = check_github_clone(repo_url)
    print("")
    print(result.summary)
    print("")


def _show_profile() -> None:
    profile = load_profile()
    print("")
    for key, value in profile.__dict__.items():
        print(f"{key}: {value}")
    print("")


def _run_cleanup(target: str) -> None:
    removed = remove_all_caches() if target == "all" else remove_temp_artifacts()
    if not removed:
        print("\nNothing to clean.\n")
        return
    print("\nCleaned:")
    for path in removed:
        print(f"- {path}")
    print("")


def _open_last_session() -> None:
    session = latest_session_dir()
    if not session:
        print("\nNo sessions yet.\n")
        return
    print(f"\nLast session: {session}")
    request_path = session / "request.json"
    output_path = session / "output.md"
    if request_path.exists():
        print("\nRequest:")
        print(request_path.read_text(encoding="utf-8", errors="replace")[:2000])
    if output_path.exists():
        print("\nOutput preview:")
        print(output_path.read_text(encoding="utf-8", errors="replace")[:3000])
    print("")


def _fixed_output_path(paper: str, zotero_title: str) -> str:
    title_hint = zotero_title or (Path(paper).stem if paper else "study-paper")
    slug = build_paper_slug(paper or None, title_hint)
    return f"result/{slug}/outputs/study-note.md"


def _prompt_with_default(label: str, default: str) -> str:
    prompt = f"{label}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    value = input(prompt).strip()
    return value or default
