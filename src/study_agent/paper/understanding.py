from __future__ import annotations

from collections.abc import Iterable
import re
from pathlib import Path

from ..analyzer.shared import sentence_with_term
from ..models import PaperClaim, PaperConcept, PaperInfo, PaperUnderstanding


CLAIM_CUES: tuple[tuple[str, str], ...] = (
    ("we propose", "proposal"),
    ("we present", "proposal"),
    ("we introduce", "proposal"),
    ("our method", "method"),
    ("our approach", "method"),
    ("our model", "architecture"),
    ("we design", "architecture"),
    ("we build", "architecture"),
    ("we use", "method"),
    ("we show", "finding"),
    ("results show", "finding"),
    ("we find", "finding"),
)

ROLE_HINTS = {
    "attention": ("cross-attention-like", "self-attention-like"),
    "bridge": ("query-like", "condition-kv-like", "fusion-like"),
    "fusion": ("fusion-like",),
    "head": ("output-head-like",),
    "token": ("token-like", "mask-like", "sequence-like"),
    "policy": ("policy-like", "output-path-like"),
    "project": ("projection-like", "embedding-space-like"),
    "query": ("query-like",),
    "action": ("action-output-like",),
    "reason": ("reasoning-like",),
    "latent": ("latent-state-like",),
}

ROLE_QUESTIONS = {
    "query-like": "代码里的 action/query-like 表示是在什么位置定义、更新并送入模型块的？",
    "condition-kv-like": "代码里来自视觉或条件分支的 KV-like 信号是在什么位置形成并被读取的？",
    "cross-attention-like": "代码里跨分支读取条件信息的 cross-attention-like 逻辑在哪里？",
    "self-attention-like": "代码里 policy/self-attention 路径在哪里实现？",
    "fusion-like": "代码里 concat、ratio、gate 或其它融合逻辑在哪里？",
    "output-head-like": "代码里的输出头或输出投影在哪里定义、在哪里被调用？",
    "token-like": "代码里的 token 字段、token 组织或 token 序列拼接在哪里？",
    "mask-like": "代码里的 attention mask、loss mask 或 autoregressive mask 在哪里？",
    "sequence-like": "代码里的 prefix/suffix 或序列组织逻辑在哪里？",
    "policy-like": "代码里的 policy 入口和 action inference 路径在哪里？",
    "output-path-like": "代码里的最终 action output path 是如何形成的？",
    "projection-like": "代码里的 projector/projection 到共享表示空间的位置在哪里？",
    "embedding-space-like": "代码里的输入映射到 hidden/embedding space 的逻辑在哪里？",
    "action-output-like": "代码里的 action generation / action decoding / action prediction 路径在哪里？",
    "reasoning-like": "代码里的 reasoning latent、reasoner block 或 reasoning state 由哪些模块实现？",
    "latent-state-like": "代码里的 latent state 是在哪里初始化、更新并参与推理的？",
}

GENERIC_CONCEPTS = {
    "Figure",
    "Table",
    "Introduction",
    "Method",
    "Results",
    "Experiments",
    "Ablation",
    "Appendix",
}


def build_paper_understanding(
    paper: PaperInfo,
    focus_terms: list[str],
    figure_paths: list[Path] | None = None,
    key_figure_pages: list[int] | None = None,
) -> PaperUnderstanding:
    figure_paths = figure_paths or []
    key_figure_pages = key_figure_pages or []
    source_text = _paper_text(paper)
    sentences = _split_sentences(source_text)
    claims = _extract_claims(sentences)
    concepts = _extract_concepts(paper, source_text, sentences, focus_terms)
    questions = _build_questions(claims, concepts)
    summary = _paper_summary(paper, claims, concepts)
    return PaperUnderstanding(
        summary=summary,
        claims=claims,
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
        _append_unique(terms, concept.concept)
        for role in concept.structure_roles:
            _append_unique(terms, role.replace("-like", "").replace("-", "_"))
    for claim in understanding.claims:
        for token in _claim_tokens(claim.claim):
            _append_unique(terms, token)
    return terms


def _paper_text(paper: PaperInfo) -> str:
    text = paper.text.strip() if paper.text else ""
    if text:
        return text
    sections = "\n\n".join(section.text for section in paper.sections if section.text)
    return sections or paper.raw_excerpt


def _split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?;:])\s+|(?<=[。！？；：])", normalized)
    return [part.strip() for part in parts if len(part.strip()) >= 24]


def _extract_claims(sentences: list[str]) -> list[PaperClaim]:
    claims: list[PaperClaim] = []
    seen: set[str] = set()
    for sentence in sentences:
        lowered = sentence.lower()
        claim_type = next((claim_type for cue, claim_type in CLAIM_CUES if cue in lowered), None)
        if not claim_type:
            continue
        claim = sentence[:320]
        key = claim.lower()
        if key in seen:
            continue
        seen.add(key)
        claims.append(PaperClaim(claim=claim, claim_type=claim_type, supporting_evidence=claim))
        if len(claims) >= 6:
            break

    if claims:
        return claims

    fallback = [sentence[:320] for sentence in sentences[:3]]
    return [
        PaperClaim(claim=claim, claim_type="context", supporting_evidence=claim)
        for claim in fallback
    ]


def _extract_concepts(
    paper: PaperInfo,
    text: str,
    sentences: list[str],
    focus_terms: list[str],
) -> list[PaperConcept]:
    candidates: list[str] = []
    for term in focus_terms:
        normalized = _humanize_term(term)
        if normalized:
            _append_unique(candidates, normalized)

    for match in re.finditer(r"([A-Z][A-Za-z0-9-]+(?:\s+[A-Z][A-Za-z0-9-]+){1,5})\s*\(([A-Z][A-Za-z0-9-]{2,12})\)", text):
        phrase = match.group(1).strip()
        acronym = match.group(2).strip()
        if _valid_concept_phrase(phrase):
            _append_unique(candidates, phrase)
        if _valid_concept_phrase(acronym):
            _append_unique(candidates, acronym)

    for source in [paper.title, *sentences[:24]]:
        for phrase in _title_case_phrases(source):
            _append_unique(candidates, phrase)

    concepts: list[PaperConcept] = []
    lowered_text = text.lower()
    for candidate in candidates:
        status = _paper_status(candidate, lowered_text)
        evidence = sentence_with_term(text, candidate) or ""
        roles = _structure_roles_for_concept(candidate)
        summary = _concept_summary(candidate, status, evidence, roles)
        concepts.append(
            PaperConcept(
                concept=candidate,
                paper_status=status,
                summary=summary,
                structure_roles=roles,
                supporting_evidence=evidence[:280],
            )
        )
        if len(concepts) >= 12:
            break
    return concepts


def _build_questions(claims: list[PaperClaim], concepts: list[PaperConcept]) -> list[str]:
    questions: list[str] = []
    for claim in claims[:4]:
        question = _claim_question(claim)
        if question:
            _append_unique(questions, question)
    for concept in concepts[:8]:
        _append_unique(questions, f"论文中的 `{concept.concept}` 在代码里由哪些文件、符号或局部路径实现？")
        for role in concept.structure_roles:
            question = ROLE_QUESTIONS.get(role)
            if question:
                _append_unique(questions, question)
    return questions


def _claim_question(claim: PaperClaim) -> str:
    if claim.claim_type == "proposal":
        return f"代码里哪些模块真正实现了论文声称提出的核心方法：{claim.claim[:120]}？"
    if claim.claim_type == "architecture":
        return f"代码里哪些模块承担了论文描述的核心结构角色：{claim.claim[:120]}？"
    if claim.claim_type == "finding":
        return f"代码里有哪些训练或推理路径支持论文的结论：{claim.claim[:120]}？"
    if claim.claim_type == "method":
        return f"代码里哪些实现路径对应论文的方法描述：{claim.claim[:120]}？"
    return f"代码里哪些实现能够支撑论文中的这段描述：{claim.claim[:120]}？"


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


def _concept_summary(concept: str, paper_status: str, evidence: str, roles: list[str]) -> str:
    if paper_status == "paper_explicit" and evidence:
        if roles:
            return f"`{concept}` 在论文文本中被直接提到，并带有可继续追踪的结构角色：{', '.join(roles)}。"
        return f"`{concept}` 在论文文本中被直接提到，后续应优先寻找代码中的实现位置。"
    if paper_status == "paper_implicit":
        if roles:
            return f"`{concept}` 没有稳定的同名显式模块，但其组成词和结构角色在论文中可见，适合按结构角色继续追代码。"
        return f"`{concept}` 更像论文里的隐式结构概念，后续应按上下文和结构角色核验代码。"
    return f"`{concept}` 当前更像用户关注点或分析标签，后续需要结合论文上下文与代码结构共同判断。"


def _paper_summary(paper: PaperInfo, claims: list[PaperClaim], concepts: list[PaperConcept]) -> str:
    explicit = [concept.concept for concept in concepts if concept.paper_status == "paper_explicit"]
    implicit = [concept.concept for concept in concepts if concept.paper_status == "paper_implicit"]
    claim_types = ", ".join(sorted({claim.claim_type for claim in claims})) if claims else "context"
    parts = [f"当前论文理解基于《{paper.title}》的文本材料，抽取到的 claim 类型包括：{claim_types}。"]
    if explicit:
        parts.append(f"论文中显式命中的关键概念：{', '.join(explicit[:6])}。")
    if implicit:
        parts.append(f"需要按结构角色继续追踪的隐式概念：{', '.join(implicit[:6])}。")
    return " ".join(parts)


def _title_case_phrases(source: str) -> list[str]:
    phrases: list[str] = []
    for match in re.finditer(r"\b([A-Z][A-Za-z0-9-]+(?:\s+[A-Z][A-Za-z0-9-]+){1,4})\b", source or ""):
        phrase = match.group(1).strip()
        if _valid_concept_phrase(phrase):
            phrases.append(phrase)
    return phrases


def _valid_concept_phrase(value: str) -> bool:
    stripped = value.strip(" -:_")
    if len(stripped) < 3:
        return False
    if stripped in GENERIC_CONCEPTS:
        return False
    if stripped.lower().startswith(("the ", "this ", "our ")):
        return False
    return True


def _humanize_term(term: str) -> str:
    pieces = [piece for piece in re.split(r"[_\-]+", term.strip()) if piece]
    if not pieces:
        return ""
    return " ".join(piece if piece.isupper() else piece.capitalize() for piece in pieces)


def _claim_tokens(claim: str) -> Iterable[str]:
    for token in re.split(r"[^a-z0-9]+", claim.lower()):
        if len(token) >= 6 and token not in {"paper", "method", "results", "attention"}:
            yield token


def _append_unique(values: list[str], item: str) -> None:
    normalized = item.strip()
    if normalized and normalized not in values:
        values.append(normalized)
