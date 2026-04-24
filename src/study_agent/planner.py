from __future__ import annotations

from dataclasses import dataclass

from .models import StudyRequest, TasteProfile


@dataclass(frozen=True)
class AnalysisPlan:
    sections: list[str]
    focus_terms: list[str]
    depth: str
    reading_order_style: str
    evidence_labels: tuple[str, str]


def build_plan(request: StudyRequest, profile: TasteProfile) -> AnalysisPlan:
    focus_terms = []
    for item in request.focus + profile.focus_bias:
        normalized = item.strip()
        if normalized and normalized not in focus_terms:
            focus_terms.append(normalized)

    labels = ("CONFIRMED", "INFERRED")
    if "/" in profile.evidence_style:
        parts = [part.strip() for part in profile.evidence_style.split("/", 1)]
        if len(parts) == 2 and all(parts):
            labels = (parts[0], parts[1])

    return AnalysisPlan(
        sections=list(profile.preferred_sections),
        focus_terms=focus_terms,
        depth=profile.depth_default,
        reading_order_style=profile.reading_order_style,
        evidence_labels=labels,
    )
