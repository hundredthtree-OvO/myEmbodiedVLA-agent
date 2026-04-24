from __future__ import annotations

from .models import CodeHit, CodeSymbol, StudyArtifact


def compose_markdown(artifact: StudyArtifact) -> str:
    request = artifact.request
    title = artifact.paper.title
    if not title.endswith("架构学习笔记"):
        title = f"{title} 架构学习笔记"
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## 1. 任务与输入")
    lines.append("")
    lines.append(f"- Paper: `{request.paper_source}`")
    lines.append(f"- Repository: `{request.repo_source}`")
    lines.append(f"- Focus: `{', '.join(request.focus) or 'architecture'}`")
    lines.append(f"- Analysis mode: `{request.mode}`")
    lines.append(f"- Engine: `{request.engine}`")
    lines.append("")
    lines.append("## 2. 论文核心概念解释")
    lines.append("")
    for card in artifact.concept_cards:
        lines.append(f"### {card.name}")
        lines.append("")
        lines.append(f"- Summary: {card.summary}")
        lines.append(f"- Evidence: `{card.evidence}`")
        lines.append("")
    lines.append("## 3. 仓库入口与主干候选")
    lines.append("")
    lines.append(f"- Scanned files: `{artifact.repo.files_scanned}`")
    if artifact.repo.entry_candidates:
        for idx, symbol in enumerate(artifact.repo.entry_candidates[:8], start=1):
            lines.append(f"- Candidate {idx}: `{_symbol_ref(symbol)}`")
            lines.append(f"  - Evidence: `{symbol.evidence}`")
    else:
        lines.append("- No entry candidates found.")
    lines.append("")
    lines.append("## 4. 论文模块 -> 代码模块映射")
    lines.append("")
    for item in artifact.code_map:
        lines.append(f"### {item.concept}")
        lines.append("")
        lines.append(f"- Explanation: {item.explanation}")
        lines.append(f"- Evidence: `{item.evidence}`")
        if item.code_refs:
            for ref in item.code_refs[:8]:
                lines.append(f"- Code: `{_ref(ref)}`")
        lines.append("")
    lines.append("## 5. 训练/推理主路径")
    lines.append("")
    lines.append("### Training")
    lines.append("")
    if artifact.repo.train_path:
        for symbol in artifact.repo.train_path[:8]:
            lines.append(f"- `{_symbol_ref(symbol)}`")
    else:
        lines.append("- `INFERRED`: no training symbol was confidently identified.")
    lines.append("")
    lines.append("### Inference")
    lines.append("")
    if artifact.repo.infer_path:
        for symbol in artifact.repo.infer_path[:8]:
            lines.append(f"- `{_symbol_ref(symbol)}`")
    else:
        lines.append("- `INFERRED`: no inference symbol was confidently identified.")
    lines.append("")
    lines.append("## 6. 关注点专项")
    lines.append("")
    for focus in artifact.request.focus:
        matching_hits = [hit for hit in artifact.repo.hits if hit.term.lower() == focus.lower()]
        lines.append(f"### {focus}")
        lines.append("")
        if matching_hits:
            for hit in matching_hits[:6]:
                lines.append(f"- `{hit.path}:{hit.line}` - {hit.text}")
            lines.append("- Evidence: `CONFIRMED`")
        else:
            lines.append("- No direct code hit yet; keep this as a manual reading target.")
            lines.append("- Evidence: `INFERRED`")
        lines.append("")
    lines.append("## 7. 建议阅读顺序")
    lines.append("")
    if artifact.reading_path:
        for idx, symbol in enumerate(artifact.reading_path, start=1):
            lines.append(f"{idx}. `{_symbol_ref(symbol)}`")
    else:
        lines.append("1. Start from README and repository configs, then search focus terms manually.")
    lines.append("")
    lines.append("## 8. 未确认点")
    lines.append("")
    if artifact.open_questions:
        for question in artifact.open_questions:
            lines.append(f"- {question}")
    else:
        lines.append("- No major unresolved point was detected by the MVP analyzer.")
    lines.append("")
    return "\n".join(lines)


def _symbol_ref(symbol: CodeSymbol) -> str:
    return f"{symbol.path}:{symbol.line} - {symbol.kind} {symbol.name}"


def _ref(ref: CodeSymbol | CodeHit) -> str:
    if isinstance(ref, CodeSymbol):
        return _symbol_ref(ref)
    return f"{ref.path}:{ref.line} - {ref.text}"
