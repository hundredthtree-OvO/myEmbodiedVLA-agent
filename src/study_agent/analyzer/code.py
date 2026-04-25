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

    focus_terms = {term.lower() for term in plan.focus_terms}
    architecture_focus = any(term in focus_terms for term in {"architecture", "model", "module"})
    training_focus = any(term in focus_terms for term in {"training", "loss", "objective"})
    inference_focus = any(term in focus_terms for term in {"inference", "deploy", "eval"})
    config_focus = any(term in focus_terms for term in {"config", "hyperparameter"})

    ordered_paths: list[str] = []
    if architecture_focus or not (training_focus or inference_focus or config_focus):
        ordered_paths.extend(repo.architecture_entry_candidates[:4])
        ordered_paths.extend(repo.architecture_skeleton_candidates[:3])
        ordered_paths.extend(repo.architecture_component_candidates[:2])
        ordered_paths.extend(repo.core_model_candidates[:2])
        ordered_paths.extend(repo.config_entry_candidates[:2])
        ordered_paths.extend(repo.deployment_entry_candidates[:1])
    elif training_focus:
        ordered_paths.extend(repo.train_candidates[:4])
        ordered_paths.extend(repo.loss_candidates[:2])
        ordered_paths.extend(repo.architecture_entry_candidates[:3])
        ordered_paths.extend(repo.architecture_skeleton_candidates[:2])
        ordered_paths.extend(repo.config_entry_candidates[:2])
    elif inference_focus:
        ordered_paths.extend(repo.inference_candidates[:4])
        ordered_paths.extend(repo.deployment_entry_candidates[:3])
        ordered_paths.extend(repo.architecture_entry_candidates[:3])
        ordered_paths.extend(repo.architecture_skeleton_candidates[:2])
    elif config_focus:
        ordered_paths.extend(repo.config_entry_candidates[:4])
        ordered_paths.extend(repo.train_candidates[:2])
        ordered_paths.extend(repo.architecture_entry_candidates[:3])
        ordered_paths.extend(repo.architecture_skeleton_candidates[:2])

    ordered: list[CodeSymbol] = []
    seen_paths: set[str] = set()
    for symbol in _symbols_for_paths(repo, ordered_paths):
        if symbol.path in seen_paths:
            continue
        seen_paths.add(symbol.path)
        ordered.append(symbol)

    if not ordered:
        for group in (repo.entry_candidates, repo.train_path, repo.infer_path):
            for symbol in group:
                if symbol.path not in seen_paths:
                    seen_paths.add(symbol.path)
                    ordered.append(symbol)
    return ordered[:12]


def build_open_questions(repo: RepoInfo, code_map: list[CodeMapItem], plan: AnalysisPlan) -> list[str]:
    questions: list[str] = []
    if not repo.entry_candidates:
        questions.append("[Missing Evidence] No clear model/policy entrypoint was found; inspect repository layout manually.")
    if not repo.architecture_entry_candidates:
        questions.append("[Missing Evidence] No architecture-oriented entry candidates were found for the current repository.")
    if repo.architecture_entry_candidates and not repo.architecture_skeleton_candidates:
        questions.append("[Missing Evidence] Architecture entry files were found, but no architecture skeleton files were confidently separated yet.")
    if not repo.model_candidates:
        questions.append("[Missing Evidence] No obvious model/policy files were found in the current scan.")
    if not repo.train_candidates:
        questions.append("[Missing Evidence] No obvious train scripts were found in the current scan.")
    if not repo.inference_candidates:
        questions.append("[Missing Evidence] No obvious inference scripts were found in the current scan.")
    if not repo.config_candidates:
        questions.append("[Missing Evidence] No obvious config files were found in the current scan.")
    if not repo.data_candidates:
        questions.append("[Missing Evidence] No obvious data/dataset files were found in the current scan.")
    if not repo.train_path:
        questions.append("[Missing Evidence] Training path is not confirmed by symbol names; search scripts/configs next.")
    if not repo.infer_path:
        questions.append("[Missing Evidence] Inference path is not confirmed by symbol names; inspect eval or policy wrappers next.")
    if len(repo.hits) < 5:
        questions.append(
            f"[Missing Evidence] Only {len(repo.hits)} repository keyword hits were found; code alignment confidence is low."
        )
    if code_map and all(item.evidence == plan.evidence_labels[1] for item in code_map):
        questions.append(
            "[Missing Evidence] All requested concepts are currently inferred rather than directly confirmed in code."
        )
    for item in code_map:
        if item.evidence == plan.evidence_labels[1]:
            questions.append(
                f"[Missing Evidence] `{item.concept}` needs manual confirmation because no direct code hit was found."
            )
    return questions[:8]


def _symbols_for_paths(repo: RepoInfo, paths: list[str]) -> list[CodeSymbol]:
    symbols: list[CodeSymbol] = []
    for path in paths:
        matching_symbols = [symbol for symbol in repo.symbols if symbol.path == path]
        if matching_symbols:
            chosen = sorted(
                matching_symbols,
                key=lambda item: (item.kind != "class", item.line, item.name.lower()),
            )[0]
            symbols.append(chosen)
            continue

        matching_hits = [hit for hit in repo.hits if hit.path == path]
        if matching_hits:
            chosen_hit = sorted(matching_hits, key=lambda item: (item.line, item.term.lower()))[0]
            symbols.append(
                CodeSymbol(
                    name=path.rsplit("/", 1)[-1].rsplit(".", 1)[0],
                    kind="file",
                    path=path,
                    line=chosen_hit.line,
                    evidence=chosen_hit.text or "role-aware reading path candidate",
                )
            )
            continue

        symbols.append(
            CodeSymbol(
                name=path.rsplit("/", 1)[-1].rsplit(".", 1)[0],
                kind="file",
                path=path,
                line=1,
                evidence="role-aware reading path candidate",
            )
        )
    return symbols
