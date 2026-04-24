from __future__ import annotations

from ..models import CodeHit, CodeMapItem, CodeSymbol, ConceptCard, RepoInfo
from ..planner import AnalysisPlan


def build_code_map(repo: RepoInfo, cards: list[ConceptCard], plan: AnalysisPlan) -> list[CodeMapItem]:
    items: list[CodeMapItem] = []
    for card in cards:
        refs: list[CodeSymbol | CodeHit] = []
        term = card.name.lower()
        refs.extend([hit for hit in repo.hits if hit.term.lower() == term][:8])
        if not refs:
            refs.extend([symbol for symbol in repo.entry_candidates if term in symbol.name.lower()][:4])

        if refs:
            explanation = f"`{card.name}` has direct repository evidence in the files listed below."
            evidence = plan.evidence_labels[0]
        else:
            refs = repo.entry_candidates[:3]
            explanation = f"`{card.name}` has no direct symbol hit yet; start from the strongest architecture entry candidates."
            evidence = plan.evidence_labels[1]

        items.append(CodeMapItem(concept=card.name, code_refs=refs, explanation=explanation, evidence=evidence))
    return items


def build_reading_path(repo: RepoInfo, plan: AnalysisPlan) -> list[CodeSymbol]:
    if plan.reading_order_style == "concept-first":
        return repo.entry_candidates[:8]

    ordered: list[CodeSymbol] = []
    for group in (repo.entry_candidates, repo.train_path, repo.infer_path):
        for symbol in group:
            if symbol not in ordered:
                ordered.append(symbol)
    return ordered[:12]


def build_open_questions(repo: RepoInfo, code_map: list[CodeMapItem], plan: AnalysisPlan) -> list[str]:
    questions: list[str] = []
    if not repo.entry_candidates:
        questions.append("No clear model/policy entrypoint was found; inspect repository layout manually.")
    if not repo.train_path:
        questions.append("Training path is not confirmed by symbol names; search scripts/configs next.")
    if not repo.infer_path:
        questions.append("Inference path is not confirmed by symbol names; inspect eval or policy wrappers next.")
    for item in code_map:
        if item.evidence == plan.evidence_labels[1]:
            questions.append(f"`{item.concept}` needs manual confirmation because no direct code hit was found.")
    return questions[:8]
