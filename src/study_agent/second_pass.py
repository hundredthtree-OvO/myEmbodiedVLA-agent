from __future__ import annotations

import json
import re
from pathlib import Path

from .models import (
    CodeHit,
    CodeMapItem,
    CodeSymbol,
    Concept2CodeLink,
    EvidencePack,
    MissingFileSuggestion,
    RepoInfo,
    SecondPassEvidence,
    SecondPassFileEvidence,
    SecondPassRoundResult,
    UncertainLink,
)


ROUND1_MIN_FILES = 3
FILE_EXCERPT_CHARS = 2800
MAX_LOCAL_EVIDENCE = 8
CONFIDENCE_LEVELS = {"high", "medium", "low"}
STATUS_LEVELS = {"CONFIRMED": 3, "INFERRED": 2, "MISSING": 1}
SCRIPT_NAME_PATTERNS = (
    "compute_",
    "_stats",
    "prepare_",
    "convert_",
    "benchmark",
    "demo",
)
HELPER_PATH_PARTS = {"utils", "common", "helpers", "ops", "io", "logging", "transforms"}


def select_second_pass_files(
    repo: RepoInfo,
    reading_path: list[CodeSymbol],
    code_map: list[CodeMapItem],
    max_files: int,
) -> list[str]:
    ordered: list[str] = []

    def add(path: str) -> None:
        normalized = _normalize_repo_path(path)
        if not normalized or normalized in ordered:
            return
        ordered.append(normalized)

    for symbol in reading_path:
        add(symbol.path)
    for path in repo.architecture_entry_candidates:
        add(path)
    for path in repo.architecture_skeleton_candidates:
        add(path)
    for path in repo.architecture_component_candidates[:2]:
        add(path)
    for item in code_map:
        for ref in item.code_refs:
            if isinstance(ref, (CodeSymbol, CodeHit)):
                add(ref.path)
    for path in repo.train_candidates[:2]:
        add(path)
    for path in repo.config_entry_candidates[:2]:
        add(path)
    for path in repo.inference_candidates[:1]:
        add(path)

    selected = ordered[: max(max_files, 0)]
    if len(selected) >= ROUND1_MIN_FILES:
        return selected
    for path in repo.core_model_candidates:
        add(path)
        if len(ordered) >= max(ROUND1_MIN_FILES, max_files):
            break
    return ordered[: max(max_files, ROUND1_MIN_FILES)]


def extract_second_pass_evidence(
    repo: RepoInfo,
    selected_paths: list[str],
) -> list[SecondPassFileEvidence]:
    files: list[SecondPassFileEvidence] = []
    for path in selected_paths:
        repo_path = repo.path / path
        if not repo_path.exists() or not repo_path.is_file():
            continue
        try:
            text = repo_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        top_symbols = [symbol.name for symbol in repo.symbols if symbol.path == path][:8]
        local_evidence = _collect_local_evidence(repo, path)
        files.append(
            SecondPassFileEvidence(
                path=path,
                selected_reason=_selected_reason(repo, path),
                excerpt=_trim_excerpt(text),
                top_symbols=top_symbols,
                local_evidence=local_evidence[:MAX_LOCAL_EVIDENCE],
            )
        )
    return files


def parse_second_pass_round_result(
    raw_text: str,
    round_id: int,
    files: list[SecondPassFileEvidence],
) -> SecondPassRoundResult:
    data = _extract_json_object(raw_text)
    summary = str(data.get("summary") or "").strip()
    concept_links = [_parse_concept_link(item, round_id) for item in data.get("concept_links", []) or []]
    uncertain_links = [_parse_uncertain_link(item) for item in data.get("uncertain_links", []) or []]
    missing_files = [_parse_missing_file(item) for item in data.get("missing_files", []) or []]
    return SecondPassRoundResult(
        round_id=round_id,
        summary=summary,
        files=files,
        concept_links=[item for item in concept_links if item],
        uncertain_links=[item for item in uncertain_links if item],
        missing_files=[item for item in missing_files if item],
    )


def validate_round2_candidates(
    repo: RepoInfo,
    round1_result: SecondPassRoundResult,
    round1_paths: list[str],
    max_files: int,
) -> list[str]:
    validated: list[str] = []
    seen: set[str] = set(round1_paths)
    candidate_pool: list[tuple[str, str]] = []

    for item in round1_result.missing_files:
        candidate_pool.append((item.path, item.reason))
    for link in round1_result.uncertain_links:
        for path in link.candidate_files:
            candidate_pool.append((path, link.reason))

    for raw_path, reason in candidate_pool:
        path = _normalize_repo_path(raw_path)
        if not path or path in seen:
            continue
        if not _is_existing_repo_file(repo, path):
            continue
        if _is_noise_candidate(path):
            continue
        if not _is_related_candidate(repo, path, round1_paths, reason):
            continue
        seen.add(path)
        validated.append(path)
        if len(validated) >= max_files:
            break
    return validated


def merge_second_pass_results(
    round1: SecondPassRoundResult,
    round2: SecondPassRoundResult | None,
) -> SecondPassEvidence:
    merged: dict[str, Concept2CodeLink] = {}
    for link in round1.concept_links:
        merged[link.concept] = link
    if round2:
        for link in round2.concept_links:
            existing = merged.get(link.concept)
            if existing is None or _link_rank(link) >= _link_rank(existing):
                merged[link.concept] = link
    final_links = sorted(merged.values(), key=lambda item: (item.concept.lower(), item.round))
    return SecondPassEvidence(round_1=round1, round_2=round2, final_concept2code_links=final_links)


def render_second_pass_markdown(result: SecondPassRoundResult) -> str:
    lines = [f"# Second-Pass Round {result.round_id}", "", result.summary or "No summary.", ""]
    lines.append("## Files")
    for item in result.files:
        lines.append(f"- `{item.path}`")
        lines.append(f"  reason: {item.selected_reason}")
        if item.top_symbols:
            lines.append(f"  symbols: {', '.join(item.top_symbols[:6])}")
    lines.append("")
    lines.append("## Concept Links")
    if result.concept_links:
        for link in result.concept_links:
            files = ", ".join(link.files) or "-"
            symbols = ", ".join(link.symbols) or "-"
            lines.append(
                f"- [{link.status}/{link.confidence}] {link.concept} -> files={files}; symbols={symbols}; reason={link.reason}"
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Uncertain Links")
    if result.uncertain_links:
        for item in result.uncertain_links:
            candidates = ", ".join(item.candidate_files) or "-"
            lines.append(f"- {item.concept}: {item.reason} | candidates={candidates}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Missing Files")
    if result.missing_files:
        for item in result.missing_files:
            lines.append(f"- {item.path}: {item.reason}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_concept2code_markdown(second_pass: SecondPassEvidence) -> str:
    lines = ["# Concept2Code", ""]
    for link in second_pass.final_concept2code_links:
        files = ", ".join(link.files) or "-"
        symbols = ", ".join(link.symbols) or "-"
        lines.append(
            f"- [{link.status}/{link.confidence}] {link.concept} (round {link.round}) -> files={files}; symbols={symbols}; reason={link.reason}"
        )
    if len(lines) == 2:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _selected_reason(repo: RepoInfo, path: str) -> str:
    reasons = repo.ast_candidate_reasons.get(path) or repo.candidate_reasons.get(path) or []
    if reasons:
        return ", ".join(reasons[:4])
    if path in repo.architecture_entry_candidates:
        return "selected_from_architecture_entry"
    if path in repo.architecture_skeleton_candidates:
        return "selected_from_architecture_skeleton"
    if path in repo.architecture_component_candidates:
        return "selected_from_architecture_component"
    if path in repo.train_candidates:
        return "selected_from_train_candidates"
    if path in repo.config_entry_candidates:
        return "selected_from_config_entry"
    return "selected_from_reading_path"


def _collect_local_evidence(repo: RepoInfo, path: str) -> list[str]:
    items: list[str] = []
    tags = repo.ast_file_tags.get(path, [])
    if tags:
        items.append(f"ast_tags={', '.join(tags[:8])}")
    reasons = repo.ast_candidate_reasons.get(path, [])
    if reasons:
        items.extend(f"ast_reason={reason}" for reason in reasons[:4])
    reasons = repo.candidate_reasons.get(path, [])
    if reasons:
        items.extend(f"candidate_reason={reason}" for reason in reasons[:4])
    hits = [hit for hit in repo.hits if hit.path == path][:4]
    items.extend(f"hit={hit.term}@{hit.line}: {hit.text}" for hit in hits)
    return items


def _trim_excerpt(text: str) -> str:
    compact = text.strip()
    if len(compact) <= FILE_EXCERPT_CHARS:
        return compact
    return compact[:FILE_EXCERPT_CHARS].rstrip() + "\n..."


def _extract_json_object(raw_text: str) -> dict:
    stripped = raw_text.strip()
    if not stripped:
        return {}
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(stripped[start : end + 1])
            except json.JSONDecodeError:
                return {}
    return {}


def _parse_concept_link(item: object, round_id: int) -> Concept2CodeLink | None:
    if not isinstance(item, dict):
        return None
    concept = str(item.get("concept") or "").strip()
    if not concept:
        return None
    status = str(item.get("status") or "INFERRED").upper()
    if status not in STATUS_LEVELS:
        status = "INFERRED"
    confidence = str(item.get("confidence") or "medium").lower()
    if confidence not in CONFIDENCE_LEVELS:
        confidence = "medium"
    files = [_normalize_repo_path(value) for value in item.get("files", []) or []]
    symbols = [str(value).strip() for value in item.get("symbols", []) or [] if str(value).strip()]
    evidence_span = str(item.get("evidence_span") or "").strip()
    reason = str(item.get("reason") or "").strip()
    round_value = int(item.get("round") or round_id)
    if not files and not symbols:
        return None
    return Concept2CodeLink(
        concept=concept,
        status=status,
        files=[value for value in files if value],
        symbols=symbols,
        evidence_span=evidence_span,
        confidence=confidence,
        reason=reason,
        round=round_value,
    )


def _parse_uncertain_link(item: object) -> UncertainLink | None:
    if not isinstance(item, dict):
        return None
    concept = str(item.get("concept") or "").strip()
    if not concept:
        return None
    return UncertainLink(
        concept=concept,
        reason=str(item.get("reason") or "").strip(),
        candidate_files=[
            value
            for value in (_normalize_repo_path(path) for path in item.get("candidate_files", []) or [])
            if value
        ],
    )


def _parse_missing_file(item: object) -> MissingFileSuggestion | None:
    if not isinstance(item, dict):
        return None
    path = _normalize_repo_path(item.get("path"))
    if not path:
        return None
    return MissingFileSuggestion(path=path, reason=str(item.get("reason") or "").strip())


def _normalize_repo_path(value: object) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.strip().replace("\\", "/").lstrip("./")
    if not normalized or normalized.startswith("/"):
        return ""
    return normalized


def _is_existing_repo_file(repo: RepoInfo, path: str) -> bool:
    candidate = repo.path / path
    try:
        resolved = candidate.resolve(strict=True)
        root = repo.path.resolve()
    except OSError:
        return False
    return resolved.is_file() and (resolved == root or root in resolved.parents)


def _is_noise_candidate(path: str) -> bool:
    lowered = path.lower()
    name = Path(path).name.lower()
    parts = {part.lower() for part in Path(path).parts}
    if any(part in HELPER_PATH_PARTS for part in parts):
        return True
    if "scripts" in parts and any(token in name for token in SCRIPT_NAME_PATTERNS):
        return True
    if "tests" in parts:
        return True
    return False


def _is_related_candidate(repo: RepoInfo, path: str, round1_paths: list[str], reason: str) -> bool:
    if path in repo.architecture_entry_candidates:
        return True
    if path in repo.architecture_skeleton_candidates:
        return True
    if path in repo.architecture_component_candidates:
        return True
    if path in repo.config_entry_candidates or path in repo.deployment_entry_candidates:
        return True
    if path in repo.train_candidates or path in repo.inference_candidates:
        return True
    path_obj = Path(path)
    for base in round1_paths:
        base_obj = Path(base)
        if path_obj.parent == base_obj.parent:
            return True
        if path_obj.stem == base_obj.stem:
            return True
        if base_obj.parent in path_obj.parents:
            return True
    if reason:
        lowered = reason.lower()
        if any(token and token in lowered for token in path_obj.parts):
            return True
        if path_obj.stem.lower() in lowered:
            return True
    return False


def _link_rank(link: Concept2CodeLink) -> tuple[int, int, int]:
    confidence_score = {"high": 3, "medium": 2, "low": 1}.get(link.confidence, 0)
    return (STATUS_LEVELS.get(link.status, 0), confidence_score, link.round)
