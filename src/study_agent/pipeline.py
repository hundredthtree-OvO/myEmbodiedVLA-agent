from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .card_models import CardArtifact
from .copilot import (
    WorkspaceIndexResult,
    ask_workspace,
    attach_paper_to_workspace,
    build_card,
    export_note,
    index_workspace,
)
from .qa_models import AnswerBundle
from .workspace_models import PaperAttachment


@dataclass(frozen=True)
class WorkspaceQuestionResult:
    workspace_id: str
    answer_path: Path
    answer: AnswerBundle


def execute_workspace_index(repo_source: str, workspace_name: str) -> WorkspaceIndexResult:
    return index_workspace(repo_source, workspace_name)


def execute_paper_attach(workspace_id: str, paper_source: str) -> PaperAttachment:
    return attach_paper_to_workspace(workspace_id, paper_source)


def execute_workspace_question(workspace_id: str, question: str) -> WorkspaceQuestionResult:
    answer = ask_workspace(workspace_id, question)
    answer_path = Path(".study-agent") / "workspaces" / workspace_id / "sessions"
    latest = sorted((item for item in answer_path.iterdir() if item.is_dir()), key=lambda item: item.name, reverse=True)[0]
    return WorkspaceQuestionResult(
        workspace_id=workspace_id,
        answer_path=latest / "answer.json",
        answer=answer,
    )


def execute_card_build(workspace_id: str, topic: str) -> CardArtifact:
    return build_card(workspace_id, topic)


def execute_export_note(workspace_id: str, output_path: Path | None = None) -> Path:
    return export_note(workspace_id, output_path)
