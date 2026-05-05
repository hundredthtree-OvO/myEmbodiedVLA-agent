from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorkspaceManifest:
    workspace_id: str
    name: str
    repo_source: str
    repo_path: str
    created_at: str
    updated_at: str
    parser_backend: str = "python-ast+text-fallback"
    graph_node_count: int = 0
    graph_edge_count: int = 0
    papers: list[str] = field(default_factory=list)
    sessions: list[str] = field(default_factory=list)
    cards: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepoIndex:
    workspace_id: str
    repo_source: str
    repo_path: str
    files_scanned: int
    languages: list[str]
    graph_nodes_path: str
    graph_edges_path: str
    top_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PaperAttachment:
    paper_id: str
    title: str
    source: str
    attached_at: str
    claims: list[str] = field(default_factory=list)
    named_modules_or_concepts: list[str] = field(default_factory=list)
    design_rationales: list[str] = field(default_factory=list)
    open_alignment_questions: list[str] = field(default_factory=list)
