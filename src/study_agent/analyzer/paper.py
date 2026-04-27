from __future__ import annotations

from .shared import sentence_with_term
from ..models import ConceptCard, PaperInfo, PaperUnderstanding
from ..planner import AnalysisPlan


def analyze_paper(
    paper: PaperInfo,
    plan: AnalysisPlan,
    paper_understanding: PaperUnderstanding | None = None,
) -> list[ConceptCard]:
    cards: list[ConceptCard] = []
    excerpt = paper.raw_excerpt
    for term in plan.focus_terms:
        evidence = sentence_with_term(excerpt, term)
        if evidence:
            summary = f"`{term}` appears in the paper material and should be treated as a primary reading target."
            cards.append(ConceptCard(name=term, summary=summary, evidence=plan.evidence_labels[0]))
        else:
            summary = f"`{term}` is user-specified or profile-prioritized; explain it by aligning paper claims with repository evidence."
            cards.append(ConceptCard(name=term, summary=summary, evidence=plan.evidence_labels[1]))

    if paper_understanding:
        existing = {card.name for card in cards}
        for concept in paper_understanding.concepts:
            if concept.concept in existing:
                continue
            evidence = plan.evidence_labels[0] if concept.paper_status == "paper_explicit" else plan.evidence_labels[1]
            cards.append(ConceptCard(name=concept.concept, summary=concept.summary, evidence=evidence))

    if not cards:
        cards.append(
            ConceptCard(
                name="architecture",
                summary="No explicit focus terms were provided, so the analysis should start from the repository architecture.",
                evidence=plan.evidence_labels[1],
            )
        )
    return cards
