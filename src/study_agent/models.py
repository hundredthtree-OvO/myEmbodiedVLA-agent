from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class PaperSection:
    title: str
    text: str


@dataclass(frozen=True)
class PaperInfo:
    source: str
    title: str
    sections: list[PaperSection]
    raw_excerpt: str
    text: str = ""


@dataclass(frozen=True)
class PaperClaim:
    claim: str
    claim_type: str
    supporting_evidence: str = ""


@dataclass(frozen=True)
class PaperConcept:
    concept: str
    paper_status: str
    summary: str
    structure_roles: list[str] = field(default_factory=list)
    supporting_evidence: str = ""


@dataclass(frozen=True)
class PaperUnderstanding:
    summary: str
    claims: list[PaperClaim]
    concepts: list[PaperConcept]
    questions: list[str]
    named_modules_or_concepts: list[str] = field(default_factory=list)
    design_rationales: list[str] = field(default_factory=list)
    open_alignment_questions: list[str] = field(default_factory=list)
    key_figure_pages: list[int] = field(default_factory=list)
    figure_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CodeSymbol:
    name: str
    kind: str
    path: str
    line: int
    evidence: str


@dataclass(frozen=True)
class CodeHit:
    term: str
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class RepoInfo:
    source: str
    path: Path
    files_scanned: int
    file_groups: dict[str, list[str]]
    entry_candidates: list[CodeSymbol]
    architecture_entry_candidates: list[str]
    architecture_skeleton_candidates: list[str]
    architecture_component_candidates: list[str]
    config_entry_candidates: list[str]
    deployment_entry_candidates: list[str]
    docs_candidates: list[str]
    train_candidates: list[str]
    inference_candidates: list[str]
    config_candidates: list[str]
    core_model_candidates: list[str]
    deployment_policy_candidates: list[str]
    model_candidates: list[str]
    loss_candidates: list[str]
    data_candidates: list[str]
    env_candidates: list[str]
    utils_candidates: list[str]
    candidate_reasons: dict[str, list[str]]
    ast_candidate_reasons: dict[str, list[str]]
    ast_file_tags: dict[str, list[str]]
    symbols: list[CodeSymbol]
    hits: list[CodeHit]
    config_hits: list[CodeHit]
    train_path: list[CodeSymbol]
    infer_path: list[CodeSymbol]


@dataclass(frozen=True)
class ZoteroItem:
    title: str
    item_id: int
    attachment_item_id: int | None
    pdf_path: Path | None
    abstract: str = ""
    source_db: Path | None = None


@dataclass(frozen=True)
class AgentConfig:
    auth_path: Path
    api_url: str
    model: str
    timeout_seconds: int = 300
    zotero_data_dir: Path | None = None
