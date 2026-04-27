from __future__ import annotations

from .models import CodeHit, CodeMapItem, CodeSymbol, EvidencePack, RepoInfo, SecondPassCodeSpan, SecondPassEvidence, SecondPassFileEvidence
from .pdf import focus_excerpt
from .taste_memory import read_taste_memory


def build_study_prompt(evidence: EvidencePack, max_chars: int, second_pass: SecondPassEvidence | None = None) -> str:
    request = evidence.request
    focus = ", ".join(request.focus) or "architecture"
    paper_excerpt = focus_excerpt(evidence.paper.text or evidence.paper.raw_excerpt, request.focus, max_chars=18000)
    sections = "\n".join(f"- {section.title}" for section in evidence.paper.sections[:20])
    memory = read_taste_memory()

    body = f"""
你是一个 VLA 论文-代码对齐研究副驾。请基于下面的证据生成中文 Markdown 学习笔记。

硬性要求：
- 聚焦用户指定的 focus，不要泛泛总结整篇论文。
- 论文概念解释和代码证据要分开写。
- 代码位置只能来自 Evidence Pack，不要编造文件、类名或行号。
- 有直接论文/代码证据时标 `CONFIRMED`，由上下文推断时标 `INFERRED`。
- 如果当前 evidence 不足，必须明确写出 `Missing Evidence` 或“需要人工确认”。
- 必须包含章节：任务与输入、论文核心概念解释、仓库入口与主干候选、论文模块 -> 代码模块映射、训练/推理主路径、关注点专项、建议阅读顺序、未确认点。

用户任务：
- Paper: {request.paper_source or request.zotero_title}
- Zotero title: {request.zotero_title or ""}
- Repository: {request.repo_source}
- Focus: {focus}
- Mode: {request.mode}

Taste profile:
{evidence.profile}

Taste memory:
{memory}

Zotero metadata:
{_zotero_block(evidence)}

Paper sections:
{sections}

Paper focus excerpt:
{paper_excerpt}

Paper understanding:
{_paper_understanding_block(evidence)}

Repository evidence:
{_repo_block(evidence.repo)}

Second-pass evidence:
{_second_pass_block(second_pass)}
"""
    return body[:max_chars]


def build_second_pass_round1_prompt(
    evidence: EvidencePack,
    selected_files: list[SecondPassFileEvidence],
    code_map: list[CodeMapItem],
) -> str:
    focus = ", ".join(evidence.request.focus) or "architecture"
    return f"""
You are doing round-1 deep reading for Concept2Code tracing.
Work only from the local evidence below. Do not invent files or symbols.

Output JSON only with this shape:
{{
  "summary": "short summary",
  "concept_links": [
    {{
      "concept": "action head",
      "status": "CONFIRMED|INFERRED|MISSING",
      "files": ["relative/path.py"],
      "symbols": ["ClassName.method"],
      "evidence_span": "short evidence excerpt",
      "confidence": "high|medium|low",
      "reason": "why this link is valid",
      "round": 1
    }}
  ],
  "uncertain_links": [
    {{
      "concept": "bridge",
      "reason": "what is uncertain",
      "candidate_files": ["relative/path.py"]
    }}
  ],
  "missing_files": [
    {{
      "path": "relative/path.py",
      "reason": "why this file may resolve uncertainty"
    }}
  ]
}}

Rules:
- Prefer CONFIRMED only when the local evidence directly supports the link.
- Use INFERRED when the evidence is suggestive but incomplete.
- Use MISSING only when a concept clearly matters but no file/symbol is currently grounded.
- Keep evidence_span short.
- Suggest at most 4 missing files.

Focus: {focus}
Repository: {evidence.request.repo_source}

High-level concept cards:
{_concept_map_block(code_map)}

Paper understanding:
{_paper_understanding_block(evidence)}

Selected files:
{_second_pass_files_block(selected_files)}
""".strip()


def build_second_pass_round2_prompt(
    evidence: EvidencePack,
    round1_summary: str,
    round1_links_json: str,
    selected_files: list[SecondPassFileEvidence],
) -> str:
    focus = ", ".join(evidence.request.focus) or "architecture"
    return f"""
You are doing round-2 deep reading for Concept2Code tracing.
Round 1 is already done. Your job is to revise or confirm the links using the additional files below.
Work only from the local evidence below. Do not invent files or symbols.

Output JSON only with the same shape as round 1.

Focus: {focus}
Repository: {evidence.request.repo_source}

Round 1 summary:
{round1_summary}

Round 1 concept links:
{round1_links_json}

Paper understanding:
{_paper_understanding_block(evidence)}

Round 2 additional files:
{_second_pass_files_block(selected_files)}
""".strip()


def build_reflection_prompt(note: str, feedback: str = "") -> str:
    return f"""
请从下面的学习笔记和用户反馈中总结 taste 变化。只输出简洁 Markdown，包含：
- 新增偏好
- 保持不变的偏好
- 下次生成笔记应注意什么

用户反馈：
{feedback}

学习笔记：
{note[-12000:]}
"""


def _zotero_block(evidence: EvidencePack) -> str:
    item = evidence.zotero_item
    if not item:
        return "No Zotero item."
    return (
        f"- Title: {item.title}\n"
        f"- Item ID: {item.item_id}\n"
        f"- Attachment ID: {item.attachment_item_id}\n"
        f"- PDF path: {item.pdf_path}\n"
        f"- Source DB: {item.source_db}\n"
        f"- Abstract: {item.abstract[:2500]}"
    )


def _repo_block(repo: RepoInfo) -> str:
    lines = [f"Scanned files: {repo.files_scanned}"]
    grouped = {name: paths for name, paths in repo.file_groups.items() if paths}
    if grouped:
        lines.append("File groups:")
        for group_name, paths in grouped.items():
            preview = ", ".join(paths[:5])
            lines.append(f"- {group_name}: {preview}")

    _append_path_list(lines, "Architecture entry candidates", repo.architecture_entry_candidates)
    _append_path_list(lines, "Architecture skeleton candidates", repo.architecture_skeleton_candidates)
    _append_path_list(lines, "Architecture component candidates", repo.architecture_component_candidates)
    _append_path_list(lines, "Config entry candidates", repo.config_entry_candidates)
    _append_path_list(lines, "Deployment entry candidates", repo.deployment_entry_candidates)
    _append_path_list(lines, "Core model candidates", repo.core_model_candidates)
    _append_path_list(lines, "Deployment/client policy candidates", repo.deployment_policy_candidates)
    _append_path_list(lines, "Model candidates", repo.model_candidates)
    _append_path_list(lines, "Train candidates", repo.train_candidates)
    _append_path_list(lines, "Inference candidates", repo.inference_candidates)
    _append_path_list(lines, "Config candidates", repo.config_candidates)
    _append_path_list(lines, "Loss candidates", repo.loss_candidates)
    _append_path_list(lines, "Data candidates", repo.data_candidates)
    _append_path_list(lines, "Env candidates", repo.env_candidates)
    _append_path_list(lines, "Utils candidates", repo.utils_candidates)
    _append_path_list(lines, "Docs candidates", repo.docs_candidates)

    lines.append("Entry candidates:")
    lines.extend(f"- {_symbol(symbol)}" for symbol in repo.entry_candidates[:12])
    lines.append("Training symbol candidates:")
    lines.extend(f"- {_symbol(symbol)}" for symbol in repo.train_path[:12])
    lines.append("Inference symbol candidates:")
    lines.extend(f"- {_symbol(symbol)}" for symbol in repo.infer_path[:12])
    lines.append("Focus/default hits:")
    lines.extend(f"- {_hit(hit)}" for hit in repo.hits[:120])

    diagnostics = _repo_diagnostics(repo)
    if diagnostics:
        lines.append("Repository diagnostics:")
        lines.extend(f"- {item}" for item in diagnostics)
    debug_lines = _candidate_reason_lines(repo)
    if debug_lines:
        lines.append("Candidate reason debug:")
        lines.extend(debug_lines)
    ast_debug_lines = _ast_reason_lines(repo)
    if ast_debug_lines:
        lines.append("AST ranking debug:")
        lines.extend(ast_debug_lines)
    return "\n".join(lines)


def _paper_understanding_block(evidence: EvidencePack) -> str:
    understanding = evidence.paper_understanding
    if not understanding:
        return "Not available."
    lines = [understanding.summary or "No summary."]
    if understanding.key_figure_pages:
        pages = ", ".join(str(page) for page in understanding.key_figure_pages)
        lines.append(f"key_figure_pages: {pages}")
    if understanding.figure_paths:
        lines.append("figure_assets:")
        lines.extend(f"- {path}" for path in understanding.figure_paths[:6])
    if understanding.concepts:
        lines.append("paper_concepts:")
        for concept in understanding.concepts[:8]:
            role_text = ", ".join(concept.structure_roles) or "-"
            lines.append(
                f"- {concept.concept} [{concept.paper_status}] roles={role_text} summary={concept.summary}"
            )
    if understanding.questions:
        lines.append("paper_questions:")
        lines.extend(f"- {question}" for question in understanding.questions[:8])
    return "\n".join(lines)


def _append_path_list(lines: list[str], title: str, values: list[str]) -> None:
    if not values:
        return
    lines.append(f"{title}:")
    lines.extend(f"- {value}" for value in values[:8])


def _repo_diagnostics(repo: RepoInfo) -> list[str]:
    diagnostics: list[str] = []
    if not repo.entry_candidates:
        diagnostics.append("No clear model/policy entrypoint was found in the repository evidence.")
    if not repo.architecture_entry_candidates:
        diagnostics.append("No architecture-oriented entry candidates were found; fall back to core model and training evidence.")
    elif not repo.architecture_skeleton_candidates:
        diagnostics.append("Architecture entry files were found, but no architecture skeleton files were confidently separated yet.")
    if not repo.config_entry_candidates:
        diagnostics.append("No research-oriented config entry candidates were found in the current scan.")
    if not repo.core_model_candidates:
        diagnostics.append("No obvious core model files were found in the current scan.")
        diagnostics.append("Inspect train/config candidates for inline architecture definition.")
    if repo.deployment_policy_candidates:
        diagnostics.append("Deployment/client policy files found; treat them as inference wrappers unless paper evidence suggests otherwise.")
        if repo.core_model_candidates:
            diagnostics.append("Core model files found, but deployment/client wrappers are also prominent. Prioritize core_model candidates for architecture analysis.")
    if not repo.model_candidates:
        diagnostics.append("No obvious model/policy files were found in the current scan.")
    if not repo.train_candidates:
        diagnostics.append("No obvious train scripts were found in the current scan.")
    if not repo.inference_candidates:
        diagnostics.append("No obvious inference scripts were found in the current scan.")
    if not repo.config_candidates:
        diagnostics.append("No obvious config files were found in the current scan.")
    if not repo.loss_candidates:
        diagnostics.append("No obvious standalone loss/objective file found.")
        diagnostics.append("Loss/objective may be implemented inline in model/trainer/algorithm files.")
    if not repo.data_candidates:
        diagnostics.append("No obvious data/dataset files were found in the current scan.")
    if not repo.env_candidates:
        diagnostics.append("No obvious standalone env/robot interface file found.")
        diagnostics.append("Environment integration may be implemented inline in deploy/wrapper/controller files.")
    if not repo.utils_candidates:
        diagnostics.append("No obvious utils/helper files were found in the current scan.")
    elif not any(hit.path in repo.utils_candidates for hit in repo.hits):
        diagnostics.append("Utils/helper files exist, but no focused hits were found in them yet.")
    if not repo.docs_candidates:
        diagnostics.append("No obvious docs/readme files were found in the current scan.")
    elif len(repo.docs_candidates) < 2:
        diagnostics.append("Docs are sparse; rely more on code/config evidence for alignment.")
    if not repo.train_path:
        diagnostics.append("Training path is not directly confirmed by symbol names.")
    if not repo.infer_path:
        diagnostics.append("Inference path is not directly confirmed by symbol names.")
    if len(repo.hits) < 5:
        diagnostics.append(f"Only {len(repo.hits)} repository hits were found; concept-to-code alignment confidence is low.")
    if not repo.config_hits:
        diagnostics.append("No config-related keyword hits were found in the current scan.")
    return diagnostics


def _candidate_reason_lines(repo: RepoInfo) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for title, values in (
        ("architecture_entry", repo.architecture_entry_candidates),
        ("architecture_skeleton", repo.architecture_skeleton_candidates),
        ("architecture_component", repo.architecture_component_candidates),
        ("config_entry", repo.config_entry_candidates),
        ("deployment_entry", repo.deployment_entry_candidates),
    ):
        for path in values[:3]:
            if path in seen:
                continue
            seen.add(path)
            reasons = repo.candidate_reasons.get(path, [])
            if reasons:
                lines.append(f"- {title} :: {path} => {', '.join(reasons[:6])}")
    return lines


def _ast_reason_lines(repo: RepoInfo) -> list[str]:
    lines: list[str] = []
    for title, values in (
        ("architecture_entry", repo.architecture_entry_candidates[:4]),
        ("architecture_skeleton", repo.architecture_skeleton_candidates[:3]),
        ("architecture_component", repo.architecture_component_candidates[:3]),
    ):
        for path in values:
            tags = repo.ast_file_tags.get(path, [])
            reasons = repo.ast_candidate_reasons.get(path, [])
            detail: list[str] = []
            if tags:
                detail.append(f"tags={', '.join(tags[:6])}")
            if reasons:
                detail.append(f"reasons={', '.join(reasons[:6])}")
            if detail:
                lines.append(f"- {title} :: {path} => {' | '.join(detail)}")
    return lines


def _second_pass_block(second_pass: SecondPassEvidence | None) -> str:
    if not second_pass:
        return "Not run."
    lines = ["Round 1 summary:", second_pass.round_1.summary or "No round-1 summary."]
    lines.append("Round 1 concept links:")
    for link in second_pass.round_1.concept_links[:8]:
        lines.append(
            f"- [{link.status}/{link.confidence}] {link.concept} -> files={', '.join(link.files) or '-'}; symbols={', '.join(link.symbols) or '-'}; reason={link.reason}"
        )
    if second_pass.round_2:
        lines.append("Round 2 summary:")
        lines.append(second_pass.round_2.summary or "No round-2 summary.")
        lines.append("Round 2 concept links:")
        for link in second_pass.round_2.concept_links[:8]:
            lines.append(
                f"- [{link.status}/{link.confidence}] {link.concept} -> files={', '.join(link.files) or '-'}; symbols={', '.join(link.symbols) or '-'}; reason={link.reason}"
            )
    lines.append("Final concept2code links:")
    for link in second_pass.final_concept2code_links[:12]:
        lines.append(
            f"- round={link.round} [{link.status}/{link.confidence}] {link.concept} -> files={', '.join(link.files) or '-'}; symbols={', '.join(link.symbols) or '-'}; reason={link.reason}"
        )
    return "\n".join(lines)


def _concept_map_block(code_map: list[CodeMapItem]) -> str:
    lines: list[str] = []
    for item in code_map[:10]:
        refs: list[str] = []
        for ref in item.code_refs[:4]:
            if isinstance(ref, CodeSymbol):
                refs.append(f"{ref.path}:{ref.line} {ref.name}")
            elif isinstance(ref, CodeHit):
                refs.append(f"{ref.path}:{ref.line} hit={ref.term}")
        lines.append(f"- {item.concept}: {item.explanation} | refs={'; '.join(refs) or '-'}")
    return "\n".join(lines) if lines else "- none"


def _second_pass_files_block(selected_files: list[SecondPassFileEvidence]) -> str:
    lines: list[str] = []
    for item in selected_files:
        lines.append(f"FILE: {item.path}")
        lines.append(f"selected_reason: {item.selected_reason}")
        if item.top_symbols:
            lines.append(f"top_symbols: {', '.join(item.top_symbols[:8])}")
        if item.local_evidence:
            lines.append("local_evidence:")
            lines.extend(f"- {value}" for value in item.local_evidence[:8])
        if item.spans:
            lines.append("spans:")
            for span in item.spans[:4]:
                lines.extend(_span_block(span))
        else:
            lines.append("excerpt:")
            lines.append(item.excerpt or "<empty>")
        lines.append("")
    return "\n".join(lines).strip() or "No files selected."


def _span_block(span: SecondPassCodeSpan) -> list[str]:
    return [
        f"- symbol: {span.symbol}",
        f"  lines: {span.line_start}-{span.line_end}",
        f"  score: {span.score}",
        f"  reason: {span.reason}",
        "  excerpt:",
        *[f"    {line}" for line in (span.excerpt or "<empty>").splitlines()],
    ]


def _symbol(symbol: CodeSymbol) -> str:
    return f"{symbol.path}:{symbol.line} {symbol.kind} {symbol.name} | {symbol.evidence}"


def _hit(hit: CodeHit) -> str:
    return f"{hit.path}:{hit.line} term={hit.term} | {hit.text}"
