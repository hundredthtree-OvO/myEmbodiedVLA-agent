from __future__ import annotations

import json
import re
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

from .card_models import CardArtifact
from .qa_models import AnswerBundle, QuestionPlan
from .workspace_models import PaperAttachment, WorkspaceManifest


WORKSPACES_ROOT = Path(".study-agent") / "workspaces"


def workspace_id_from_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug[:80] or "workspace"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def workspace_root(workspace_id: str, root: Path = WORKSPACES_ROOT) -> Path:
    return root / workspace_id


def ensure_workspace_dirs(workspace_id: str, root: Path = WORKSPACES_ROOT) -> Path:
    base = workspace_root(workspace_id, root)
    for path in (
        base,
        base / "papers",
        base / "sessions",
        base / "cards",
    ):
        path.mkdir(parents=True, exist_ok=True)
    return base


def manifest_path(workspace_id: str, root: Path = WORKSPACES_ROOT) -> Path:
    return workspace_root(workspace_id, root) / "manifest.json"


def save_manifest(manifest: WorkspaceManifest, root: Path = WORKSPACES_ROOT) -> None:
    ensure_workspace_dirs(manifest.workspace_id, root)
    path = manifest_path(manifest.workspace_id, root)
    path.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_manifest(workspace_id: str, root: Path = WORKSPACES_ROOT) -> WorkspaceManifest:
    path = manifest_path(workspace_id, root)
    data = json.loads(path.read_text(encoding="utf-8"))
    return WorkspaceManifest(**data)


def create_or_update_workspace(
    name: str,
    repo_source: str,
    repo_path: str,
    graph_node_count: int = 0,
    graph_edge_count: int = 0,
    root: Path = WORKSPACES_ROOT,
) -> WorkspaceManifest:
    workspace_id = workspace_id_from_name(name)
    ensure_workspace_dirs(workspace_id, root)
    now = utc_now_iso()
    path = manifest_path(workspace_id, root)
    if path.exists():
        current = load_manifest(workspace_id, root)
        updated = replace(
            current,
            name=name,
            repo_source=repo_source,
            repo_path=repo_path,
            graph_node_count=graph_node_count,
            graph_edge_count=graph_edge_count,
            updated_at=now,
        )
        save_manifest(updated, root)
        return updated
    manifest = WorkspaceManifest(
        workspace_id=workspace_id,
        name=name,
        repo_source=repo_source,
        repo_path=repo_path,
        created_at=now,
        updated_at=now,
        graph_node_count=graph_node_count,
        graph_edge_count=graph_edge_count,
    )
    save_manifest(manifest, root)
    return manifest


def record_paper_attachment(
    workspace_id: str,
    attachment: PaperAttachment,
    root: Path = WORKSPACES_ROOT,
) -> WorkspaceManifest:
    manifest = load_manifest(workspace_id, root)
    papers = list(manifest.papers)
    if attachment.paper_id not in papers:
        papers.append(attachment.paper_id)
    updated = replace(manifest, papers=papers, updated_at=utc_now_iso())
    save_manifest(updated, root)
    paper_dir = workspace_root(workspace_id, root) / "papers" / attachment.paper_id
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "attachment.json").write_text(
        json.dumps(asdict(attachment), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return updated


def load_paper_attachments(workspace_id: str, root: Path = WORKSPACES_ROOT) -> list[PaperAttachment]:
    paper_root = workspace_root(workspace_id, root) / "papers"
    if not paper_root.exists():
        return []
    items: list[PaperAttachment] = []
    for path in sorted(paper_root.glob("*/attachment.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items.append(PaperAttachment(**data))
    return items


def create_session_dir(workspace_id: str, root: Path = WORKSPACES_ROOT) -> tuple[str, Path]:
    base = workspace_root(workspace_id, root) / "sessions"
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = base / stamp
    counter = 1
    while path.exists():
        path = base / f"{stamp}-{counter}"
        counter += 1
    path.mkdir()
    return path.name, path


def save_question_answer(
    workspace_id: str,
    plan: QuestionPlan,
    answer: AnswerBundle,
    root: Path = WORKSPACES_ROOT,
) -> tuple[str, Path]:
    session_id, session_dir = create_session_dir(workspace_id, root)
    (session_dir / "question.json").write_text(
        json.dumps(asdict(plan), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (session_dir / "answer.json").write_text(
        json.dumps(asdict(answer), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = load_manifest(workspace_id, root)
    sessions = list(manifest.sessions)
    sessions.append(session_id)
    save_manifest(replace(manifest, sessions=sessions, updated_at=utc_now_iso()), root)
    return session_id, session_dir


def latest_session(workspace_id: str, root: Path = WORKSPACES_ROOT) -> tuple[str, Path] | None:
    session_root = workspace_root(workspace_id, root) / "sessions"
    if not session_root.exists():
        return None
    candidates = sorted((item for item in session_root.iterdir() if item.is_dir()), key=lambda item: item.name, reverse=True)
    if not candidates:
        return None
    return candidates[0].name, candidates[0]


def save_card(workspace_id: str, card: CardArtifact, root: Path = WORKSPACES_ROOT) -> Path:
    cards_dir = workspace_root(workspace_id, root) / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    path = cards_dir / f"{card.card_id}.md"
    path.write_text(card.markdown, encoding="utf-8")
    manifest = load_manifest(workspace_id, root)
    cards = list(manifest.cards)
    if card.card_id not in cards:
        cards.append(card.card_id)
    save_manifest(replace(manifest, cards=cards, updated_at=utc_now_iso()), root)
    return path
