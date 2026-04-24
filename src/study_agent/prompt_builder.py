from __future__ import annotations

from .models import CodeHit, CodeSymbol, EvidencePack
from .pdf import focus_excerpt
from .taste_memory import read_taste_memory


def build_study_prompt(evidence: EvidencePack, max_chars: int) -> str:
    request = evidence.request
    focus = ", ".join(request.focus) or "architecture"
    paper_excerpt = focus_excerpt(evidence.paper.text or evidence.paper.raw_excerpt, request.focus, max_chars=18000)
    sections = "\n".join(f"- {section.title}" for section in evidence.paper.sections[:20])
    memory = read_taste_memory()

    body = f"""
你是一个 VLA 论文-代码对齐研究副驾。请基于下面的证据生成中文 Markdown 学习笔记。

硬性要求：
- 聚焦用户指定的 focus，不要泛泛总结整篇论文。
- 论文概念解释和代码证据要分开讲。
- 代码位置只能来自 Evidence Pack，不要编造文件、类名或行号。
- 有直接论文/代码证据时标 `CONFIRMED`，由上下文推断时标 `INFERRED`。
- 如果代码没有直接命名为 focus 中的术语，要解释论文概念如何折叠进实现。
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

Repository evidence:
{_repo_block(evidence)}
"""
    return body[:max_chars]


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


def _repo_block(evidence: EvidencePack) -> str:
    repo = evidence.repo
    lines = [f"Scanned files: {repo.files_scanned}", "Entry candidates:"]
    lines.extend(f"- {_symbol(symbol)}" for symbol in repo.entry_candidates[:12])
    lines.append("Training candidates:")
    lines.extend(f"- {_symbol(symbol)}" for symbol in repo.train_path[:12])
    lines.append("Inference candidates:")
    lines.extend(f"- {_symbol(symbol)}" for symbol in repo.infer_path[:12])
    lines.append("Focus/default hits:")
    lines.extend(f"- {_hit(hit)}" for hit in repo.hits[:120])
    return "\n".join(lines)


def _symbol(symbol: CodeSymbol) -> str:
    return f"{symbol.path}:{symbol.line} {symbol.kind} {symbol.name} | {symbol.evidence}"


def _hit(hit: CodeHit) -> str:
    return f"{hit.path}:{hit.line} term={hit.term} | {hit.text}"
