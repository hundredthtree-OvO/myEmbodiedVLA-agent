from __future__ import annotations

from .models import CodeHit, CodeSymbol, StudyArtifact
from .prompt_builder import _repo_diagnostics


def compose_markdown(artifact: StudyArtifact) -> str:
    request = artifact.request
    title = artifact.paper.title
    if not title.endswith("架构学习笔记"):
        title = f"{title} 架构学习笔记"

    lines: list[str] = [
        f"# {title}",
        "",
        "## 1. 任务与输入",
        "",
        f"- Paper: `{request.paper_source}`",
        f"- Repository: `{request.repo_source}`",
        f"- Focus: `{', '.join(request.focus) or 'architecture'}`",
        f"- Analysis mode: `{request.mode}`",
        f"- Engine: `{request.engine}`",
        "",
        "## 2. 论文核心概念解释",
        "",
    ]

    for card in artifact.concept_cards:
        lines.extend(
            [
                f"### {card.name}",
                "",
                f"- Summary: {card.summary}",
                f"- Evidence: `{card.evidence}`",
                "",
            ]
        )

    lines.extend(
        [
            "## 3. 仓库入口与主干候选",
            "",
            f"- Scanned files: `{artifact.repo.files_scanned}`",
        ]
    )

    grouped = {name: paths for name, paths in artifact.repo.file_groups.items() if paths}
    if grouped:
        lines.append("- File groups:")
        for group_name, paths in grouped.items():
            lines.append(f"  - `{group_name}`: {', '.join(f'`{path}`' for path in paths[:5])}")
    else:
        lines.append("- File groups: none")

    _append_candidate_group(lines, "Model candidates", artifact.repo.model_candidates)
    _append_candidate_group(lines, "Train candidates", artifact.repo.train_candidates)
    _append_candidate_group(lines, "Inference candidates", artifact.repo.inference_candidates)
    _append_candidate_group(lines, "Config candidates", artifact.repo.config_candidates)
    _append_candidate_group(lines, "Data candidates", artifact.repo.data_candidates)

    if artifact.repo.entry_candidates:
        lines.append("- Entry candidates:")
        for idx, symbol in enumerate(artifact.repo.entry_candidates[:8], start=1):
            lines.append(f"  - Candidate {idx}: `{_symbol_ref(symbol)}`")
            lines.append(f"    - Evidence: `{symbol.evidence}`")
    else:
        lines.append("- No entry candidates found.")

    lines.extend(["", "## 4. 论文模块 -> 代码模块映射", ""])
    for item in artifact.code_map:
        lines.extend(
            [
                f"### {item.concept}",
                "",
                f"- Explanation: {item.explanation}",
                f"- Evidence: `{item.evidence}`",
            ]
        )
        if item.code_refs:
            for ref in item.code_refs[:8]:
                lines.append(f"- Code: `{_ref(ref)}`")
        lines.append("")

    lines.extend(["## 5. 训练/推理主路径", "", "### Training", ""])
    if artifact.repo.train_path:
        for symbol in artifact.repo.train_path[:8]:
            lines.append(f"- `{_symbol_ref(symbol)}`")
    else:
        lines.append("- `INFERRED`: no training symbol was confidently identified.")

    lines.extend(["", "### Inference", ""])
    if artifact.repo.infer_path:
        for symbol in artifact.repo.infer_path[:8]:
            lines.append(f"- `{_symbol_ref(symbol)}`")
    else:
        lines.append("- `INFERRED`: no inference symbol was confidently identified.")

    lines.extend(["", "## 6. 关注点专项", ""])
    for focus in artifact.request.focus:
        matching_hits = [hit for hit in artifact.repo.hits if hit.term.lower() == focus.lower()]
        lines.extend([f"### {focus}", ""])
        if matching_hits:
            for hit in matching_hits[:6]:
                lines.append(f"- `{hit.path}:{hit.line}` - {hit.text}")
            lines.append("- Evidence: `CONFIRMED`")
        else:
            lines.append("- No direct code hit yet; keep this as a manual reading target.")
            lines.append("- Evidence: `INFERRED`")
        lines.append("")

    lines.extend(["## 7. 建议阅读顺序", ""])
    if artifact.reading_path:
        for idx, symbol in enumerate(artifact.reading_path, start=1):
            lines.append(f"{idx}. `{_symbol_ref(symbol)}`")
    else:
        lines.append("1. Start from README and repository configs, then search focus terms manually.")

    lines.extend(["", "## 8. 未确认点", ""])
    questions = list(artifact.open_questions)
    repo_diagnostics = _repo_diagnostics(artifact.repo)
    for diagnostic in repo_diagnostics:
        tagged = diagnostic if diagnostic.startswith("[Missing Evidence]") else f"[Missing Evidence] {diagnostic}"
        if tagged not in questions:
            questions.append(tagged)
    if questions:
        for question in questions:
            lines.append(f"- {question}")
    else:
        lines.append("- No major unresolved point was detected by the current analyzer.")

    lines.append("")
    return "\n".join(lines)


def _append_candidate_group(lines: list[str], title: str, values: list[str]) -> None:
    if not values:
        return
    lines.append(f"- {title}:")
    for value in values[:8]:
        lines.append(f"  - `{value}`")


def _symbol_ref(symbol: CodeSymbol) -> str:
    return f"{symbol.path}:{symbol.line} - {symbol.kind} {symbol.name}"


def _ref(ref: CodeSymbol | CodeHit) -> str:
    if isinstance(ref, CodeSymbol):
        return _symbol_ref(ref)
    return f"{ref.path}:{ref.line} - {ref.text}"
