from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_SECTIONS = [
    "任务与输入",
    "论文核心概念解释",
    "仓库入口与主干候选",
    "论文模块 -> 代码模块映射",
    "训练/推理主路径",
    "关注点专项",
    "建议阅读顺序",
    "未确认点",
]


@dataclass(frozen=True)
class StudyRequest:
    paper_source: str | None
    repo_source: str
    focus: list[str]
    output_path: Path
    mode: str = "paper-aligned"
    engine: str = "codex"
    zotero_title: str | None = None
    model: str | None = None


@dataclass
class TasteProfile:
    analysis_template: str = "paper-aligned"
    preferred_sections: list[str] = field(default_factory=lambda: list(DEFAULT_SECTIONS))
    focus_bias: list[str] = field(default_factory=list)
    reading_order_style: str = "entrypoint-first"
    evidence_style: str = "CONFIRMED/INFERRED"
    terminology_preferences: dict[str, str] = field(default_factory=dict)
    depth_default: str = "module-function"
    verbosity: str = "medium"


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
    max_evidence_chars: int = 60000
    max_history_examples: int = 3
    zotero_data_dir: Path | None = None


@dataclass(frozen=True)
class EvidencePack:
    request: StudyRequest
    paper: PaperInfo
    repo: RepoInfo
    profile: TasteProfile
    zotero_item: ZoteroItem | None = None


@dataclass(frozen=True)
class ConceptCard:
    name: str
    summary: str
    evidence: str


@dataclass(frozen=True)
class CodeMapItem:
    concept: str
    code_refs: list[CodeSymbol | CodeHit]
    explanation: str
    evidence: str


@dataclass(frozen=True)
class StudyArtifact:
    request: StudyRequest
    paper: PaperInfo
    repo: RepoInfo
    profile: TasteProfile
    summary: str
    concept_cards: list[ConceptCard]
    code_map: list[CodeMapItem]
    reading_path: list[CodeSymbol]
    open_questions: list[str]
