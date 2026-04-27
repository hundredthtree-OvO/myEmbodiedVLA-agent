from __future__ import annotations

import re
from pathlib import Path

from .analyzer.shared import sentence_with_term
from .models import PaperConcept, PaperInfo, PaperUnderstanding


ROLE_HINTS = {
    "attention": ("cross-attention-like", "self-attention-like"),
    "bridge": ("query-like", "condition-kv-like", "fusion-like"),
    "head": ("output-head-like",),
    "token": ("token-like", "mask-like", "sequence-like"),
    "policy": ("policy-like", "output-path-like"),
    "project": ("projection-like", "embedding-space-like"),
    "query": ("query-like",),
    "action": ("action-output-like",),
}

ROLE_QUESTIONS = {
    "query-like": "代码里 action/query-like 表示是在哪里定义和更新的？",
    "condition-kv-like": "代码里来自视觉/条件分支的 KV-like 信号是在哪里形成的？",
    "cross-attention-like": "代码里跨分支的信息读取是在哪里实现的？",
    "self-attention-like": "代码里 policy/self-attention 路径是在哪里实现的？",
    "fusion-like": "代码里 concat、ratio、gate 或其他融合逻辑在哪里实现？",
    "output-head-like": "代码里输出头或输出投影的定义与使用分别在哪里？",
    "token-like": "代码里 token 路径、token field 和 token 相关输入输出在哪里？",
    "mask-like": "代码里 attention mask / loss mask / autoregressive mask 在哪里？",
    "sequence-like": "代码里序列拼接、prefix/suffix 或 token sequence 组织逻辑在哪里？",
    "policy-like": "代码里的 policy 入口和 action inference 路径在哪里？",
    "output-path-like": "代码里的最终 action output path 是怎样形成的？",
    "projection-like": "代码里 projector / projection 到共享表征空间的实现在哪里？",
    "embedding-space-like": "代码里输入被映射到 hidden/embedding space 的位置在哪里？",
    "action-output-like": "代码里的 action generation / action decoding / action prediction 路径在哪里？",
}


def build_paper_understanding(
    paper: PaperInfo,
    focus_terms: list[str],
    figure_paths: list[Path] | None = None,
    key_figure_pages: list[int] | None = None,
) -> PaperUnderstanding:
    concepts: list[PaperConcept] = []
    questions: list[str] = []
    figure_paths = figure_paths or []
    key_figure_pages = key_figure_pages or []
    lowered_text = paper.text.lower()

    for raw_term in focus_terms:
        concept = raw_term.strip()
        if not concept:
            continue
        paper_status = _paper_status(concept, lowered_text)
        evidence = sentence_with_term(paper.text or paper.raw_excerpt, concept) or ""
        roles = _structure_roles_for_concept(concept)
        summary = _concept_summary(concept, paper_status, evidence)
        concepts.append(
            PaperConcept(
                concept=concept,
                paper_status=paper_status,
                summary=summary,
                structure_roles=roles,
                supporting_evidence=evidence[:280],
            )
        )
        questions.append(f"论文里的 `{concept}` 在代码里对应哪些实现位置？")
        for role in roles:
            question = ROLE_QUESTIONS.get(role)
            if question and question not in questions:
                questions.append(question)

    summary = _paper_summary(paper, concepts)
    return PaperUnderstanding(
        summary=summary,
        concepts=concepts,
        questions=questions[:12],
        key_figure_pages=list(key_figure_pages),
        figure_paths=[str(path.as_posix()) for path in figure_paths],
    )


def understanding_focus_terms(understanding: PaperUnderstanding | None) -> list[str]:
    if not understanding:
        return []
    terms: list[str] = []
    for concept in understanding.concepts:
        if concept.concept not in terms:
            terms.append(concept.concept)
        for role in concept.structure_roles:
            role_term = role.replace("-like", "").replace("-", "_")
            if role_term not in terms:
                terms.append(role_term)
    return terms


def _paper_status(concept: str, lowered_text: str) -> str:
    lowered_concept = concept.lower()
    if lowered_concept and lowered_concept in lowered_text:
        return "paper_explicit"
    pieces = [piece for piece in re.split(r"[^a-z0-9]+", lowered_concept) if piece]
    if pieces and all(piece in lowered_text for piece in pieces):
        return "paper_implicit"
    return "user_defined"


def _structure_roles_for_concept(concept: str) -> list[str]:
    roles: list[str] = []
    lowered = concept.lower()
    for token, token_roles in ROLE_HINTS.items():
        if token in lowered:
            for role in token_roles:
                if role not in roles:
                    roles.append(role)
    return roles


def _concept_summary(concept: str, paper_status: str, evidence: str) -> str:
    if paper_status == "paper_explicit" and evidence:
        return f"`{concept}` 在当前论文材料中有直接文本证据，后续应优先寻找代码中的实现或结构对应。"
    if paper_status == "paper_implicit":
        return f"`{concept}` 没有完整同名短语直击，但其组成词或相关描述已出现在论文材料中，后续应按结构角色做代码核验。"
    return f"`{concept}` 目前更像用户定义或外部引入的分析视角，后续需要通过论文上下文与代码结构共同判断。"


def _paper_summary(paper: PaperInfo, concepts: list[PaperConcept]) -> str:
    explicit = [concept.concept for concept in concepts if concept.paper_status == "paper_explicit"]
    implicit = [concept.concept for concept in concepts if concept.paper_status == "paper_implicit"]
    if explicit or implicit:
        details: list[str] = []
        if explicit:
            details.append(f"论文中显式出现的关注概念：{', '.join(explicit)}")
        if implicit:
            details.append(f"论文中需要按结构理解的概念：{', '.join(implicit)}")
        return "；".join(details)
    return f"当前论文理解基于《{paper.title}》的文本材料，尚未形成强显式概念命中。"
