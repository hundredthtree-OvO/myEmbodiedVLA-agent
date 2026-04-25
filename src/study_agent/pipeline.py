from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analyzer.code import build_code_map, build_open_questions, build_reading_path
from .analyzer.paper import analyze_paper
from .cleanup import cleanup_after_analyze
from .codex_client import assert_codex_ready, run_codex
from .composer import compose_markdown
from .config import load_config, with_model
from .ingest import ingest_paper, ingest_repo
from .models import EvidencePack, StudyArtifact, StudyRequest
from .planner import build_plan
from .profile import load_profile
from .progress import NullProgress, ProgressSink
from .prompt_builder import build_study_prompt
from .session_store import create_session_dir, save_session
from .zotero import find_zotero_item


@dataclass(frozen=True)
class AnalysisResult:
    request: StudyRequest
    output_path: Path
    markdown: str
    cleaned: list[Path]
    session_dir: Path | None


def execute_analysis(
    request: StudyRequest,
    cleanup_mode: str = "none",
    progress: ProgressSink | None = None,
    config=None,
) -> AnalysisResult:
    progress = progress or NullProgress()
    config = config or load_config()
    config = with_model(config, request.model)

    progress.stage("Resolving inputs")
    paper_source = request.paper_source
    zotero_item = None
    if request.zotero_title:
        progress.stage("Querying Zotero", request.zotero_title)
        zotero_item = find_zotero_item(request.zotero_title, config.zotero_data_dir or Path("E:/zoteroData"))
        if not paper_source and zotero_item.pdf_path:
            paper_source = str(zotero_item.pdf_path)
    if not paper_source:
        raise ValueError("Zotero item was found, but no PDF attachment path was available.")

    progress.stage("Extracting PDF text", Path(paper_source).name)
    profile = load_profile()
    final_request = StudyRequest(
        paper_source=paper_source,
        repo_source=request.repo_source,
        focus=request.focus,
        output_path=request.output_path,
        mode=request.mode,
        engine=request.engine,
        zotero_title=request.zotero_title,
        model=request.model or config.model,
    )
    plan = build_plan(final_request, profile)
    paper = ingest_paper(final_request.paper_source)

    progress.stage("Preparing repo", final_request.repo_source)
    repo = ingest_repo(final_request.repo_source, plan.focus_terms)

    progress.stage("Building evidence pack")
    concept_cards = analyze_paper(paper, plan)
    code_map = build_code_map(repo, concept_cards, plan)
    reading_path = build_reading_path(repo, plan)
    open_questions = build_open_questions(repo, code_map, plan)
    artifact = StudyArtifact(
        request=final_request,
        paper=paper,
        repo=repo,
        profile=profile,
        summary=f"{paper.title} aligned against {repo.path.name}",
        concept_cards=concept_cards,
        code_map=code_map,
        reading_path=reading_path,
        open_questions=open_questions,
    )
    evidence = EvidencePack(
        request=final_request,
        paper=paper,
        repo=repo,
        profile=profile,
        zotero_item=zotero_item,
    )

    session_dir: Path | None = None
    if final_request.engine == "codex":
        progress.stage("Calling Codex", config.model)
        assert_codex_ready(config)
        session_dir = create_session_dir()
        prompt = build_study_prompt(evidence, config.max_evidence_chars)
        markdown = run_codex(
            prompt,
            config,
            Path.cwd(),
            session_dir / "codex-output.md",
            on_text=progress.output,
        )
        progress.stage("Saving session", session_dir.name)
        save_session(session_dir, evidence, prompt, markdown)
    else:
        markdown = compose_markdown(artifact)

    final_request.output_path.parent.mkdir(parents=True, exist_ok=True)
    final_request.output_path.write_text(markdown, encoding="utf-8")
    cleaned = cleanup_after_analyze(cleanup_mode, final_request.repo_source)
    progress.stage("Done", final_request.output_path.name)
    return AnalysisResult(
        request=final_request,
        output_path=final_request.output_path,
        markdown=markdown,
        cleaned=cleaned,
        session_dir=session_dir,
    )
