from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analyzer.code import build_code_map, build_open_questions, build_reading_path
from .analyzer.paper import analyze_paper
from .cleanup import cleanup_after_analyze
from .codex_client import CodexUnavailable, assert_codex_ready, run_codex
from .composer import compose_markdown
from .config import default_zotero_data_dir, load_config, with_model
from .ingest import RepositoryPrepareError, ingest_paper, ingest_repo
from .models import EvidencePack, StudyArtifact, StudyRequest
from .paper_understanding import build_paper_understanding, understanding_focus_terms
from .paper_workspace import prepare_paper_workspace, save_workspace_outputs, write_paper_text, write_paper_understanding
from .planner import build_plan
from .profile import load_profile
from .progress import NullProgress, ProgressSink
from .prompt_builder import (
    build_second_pass_round1_prompt,
    build_second_pass_round2_prompt,
    build_study_prompt,
)
from .pdf import extract_pdf_page_texts, render_pdf_pages, select_key_figure_pages
from .quality_gate import evaluate_evidence_quality, prepend_quality_gate_note
from .second_pass import (
    extract_second_pass_evidence,
    merge_second_pass_results,
    parse_second_pass_round_result,
    select_second_pass_files,
    validate_round2_candidates,
)
from .session_store import create_session_dir, save_session
from .zotero import ZoteroLookupError, find_zotero_item


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
        try:
            zotero_item = find_zotero_item(request.zotero_title, config.zotero_data_dir or default_zotero_data_dir())
        except ZoteroLookupError as exc:
            raise RuntimeError(f"Zotero lookup failed: {exc}") from exc
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
    try:
        paper = ingest_paper(final_request.paper_source)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Paper input failed: {exc}") from exc
    except RuntimeError as exc:
        raise RuntimeError(f"PDF extraction failed: {exc}") from exc

    progress.stage("Preparing paper workspace")
    paper_workspace = prepare_paper_workspace(final_request.paper_source, paper)
    write_paper_text(paper_workspace, paper.text or paper.raw_excerpt)
    figure_paths = []
    key_figure_pages: list[int] = []
    paper_source_path = Path(final_request.paper_source) if final_request.paper_source else None
    if paper_source_path and paper_source_path.exists() and paper_source_path.suffix.lower() == ".pdf":
        try:
            page_texts = extract_pdf_page_texts(paper_source_path)
            key_figure_pages = select_key_figure_pages(page_texts, plan.focus_terms)
            figure_paths = render_pdf_pages(paper_source_path, key_figure_pages, paper_workspace.figures_dir)
        except Exception as exc:  # pragma: no cover - defensive fallback for local rendering issues
            progress.info(f"Paper figure rendering skipped: {exc}")
    paper_understanding = build_paper_understanding(
        paper,
        plan.focus_terms,
        figure_paths=figure_paths,
        key_figure_pages=key_figure_pages,
    )
    write_paper_understanding(paper_workspace, paper_understanding)

    progress.stage("Preparing repo", final_request.repo_source)
    try:
        repo = ingest_repo(final_request.repo_source, plan.focus_terms)
    except RepositoryPrepareError as exc:
        raise RuntimeError(f"Repository preparation failed: {exc}") from exc

    progress.stage("Building evidence pack")
    concept_cards = analyze_paper(paper, plan, paper_understanding)
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
        paper_understanding=paper_understanding,
    )
    evidence = EvidencePack(
        request=final_request,
        paper=paper,
        repo=repo,
        profile=profile,
        zotero_item=zotero_item,
        paper_understanding=paper_understanding,
    )
    quality_report = evaluate_evidence_quality(artifact)

    session_dir: Path | None = None
    second_pass = None
    second_pass_round1_raw = ""
    second_pass_round2_raw = ""
    if final_request.engine == "codex":
        if not quality_report.should_call_codex:
            progress.stage("Evidence quality gate", "degraded to offline")
            progress.info(f"Evidence quality gate blocked Codex call: {', '.join(quality_report.reasons)}")
            markdown = prepend_quality_gate_note(compose_markdown(artifact), quality_report)
        else:
            if quality_report.reasons:
                progress.stage("Evidence quality gate", quality_report.status)
                progress.info(f"Evidence quality warnings: {', '.join(quality_report.reasons)}")
            progress.stage("Calling Codex", config.model)
            try:
                assert_codex_ready(config)
            except CodexUnavailable as exc:
                raise RuntimeError(f"Codex auth failed: {exc}") from exc
            session_dir = create_session_dir()
            if config.second_pass_enabled:
                progress.stage("Second-pass round 1")
                round1_paths = select_second_pass_files(repo, reading_path, code_map, config.second_pass_round1_max_files)
                second_pass_focus = _merge_second_pass_focus_terms(final_request.focus, paper_understanding)
                round1_files = extract_second_pass_evidence(repo, round1_paths, second_pass_focus)
                if round1_files:
                    round1_prompt = build_second_pass_round1_prompt(evidence, round1_files, code_map)
                    try:
                        second_pass_round1_raw = run_codex(
                            round1_prompt,
                            config,
                            Path.cwd(),
                            session_dir / "codex-second-pass-round-1.md",
                        )
                        round1_result = parse_second_pass_round_result(second_pass_round1_raw, 1, round1_files)
                        round2_paths = validate_round2_candidates(
                            repo,
                            round1_result,
                            [item.path for item in round1_files],
                            config.second_pass_round2_max_files,
                        )
                        round2_result = None
                        if round2_paths:
                            progress.stage("Second-pass round 2")
                            round2_files = extract_second_pass_evidence(repo, round2_paths, second_pass_focus)
                            if round2_files:
                                round1_links_json = second_pass_round1_raw.strip() or "{}"
                                round2_prompt = build_second_pass_round2_prompt(
                                    evidence,
                                    round1_result.summary,
                                    round1_links_json,
                                    round2_files,
                                )
                                second_pass_round2_raw = run_codex(
                                    round2_prompt,
                                    config,
                                    Path.cwd(),
                                    session_dir / "codex-second-pass-round-2.md",
                                )
                                round2_result = parse_second_pass_round_result(second_pass_round2_raw, 2, round2_files)
                        second_pass = merge_second_pass_results(round1_result, round2_result)
                    except CodexUnavailable as exc:
                        raise RuntimeError(f"Codex request failed: {exc}") from exc
            prompt = build_study_prompt(evidence, config.max_evidence_chars, second_pass=second_pass)
            try:
                markdown = run_codex(
                    prompt,
                    config,
                    Path.cwd(),
                    session_dir / "codex-output.md",
                    on_text=progress.output,
                )
            except CodexUnavailable as exc:
                raise RuntimeError(f"Codex request failed: {exc}") from exc
            progress.stage("Saving session", session_dir.name)
            save_session(
                session_dir,
                evidence,
                prompt,
                markdown,
                second_pass=second_pass,
                second_pass_round1_raw=second_pass_round1_raw,
                second_pass_round2_raw=second_pass_round2_raw,
            )
    else:
        markdown = compose_markdown(artifact)

    final_request.output_path.parent.mkdir(parents=True, exist_ok=True)
    final_request.output_path.write_text(markdown, encoding="utf-8")
    save_workspace_outputs(paper_workspace, markdown, second_pass=second_pass)
    cleaned = cleanup_after_analyze(cleanup_mode, final_request.repo_source)
    progress.stage("Done", final_request.output_path.name)
    return AnalysisResult(
        request=final_request,
        output_path=final_request.output_path,
        markdown=markdown,
        cleaned=cleaned,
        session_dir=session_dir,
    )


def _merge_second_pass_focus_terms(focus: list[str], paper_understanding) -> list[str]:
    merged: list[str] = []
    for item in focus + understanding_focus_terms(paper_understanding):
        normalized = item.strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged
