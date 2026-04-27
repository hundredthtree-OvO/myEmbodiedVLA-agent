from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import PaperInfo, PaperUnderstanding, SecondPassEvidence


RESULT_ROOT = Path("result")


@dataclass(frozen=True)
class PaperWorkspace:
    slug: str
    root: Path
    source_dir: Path
    extracted_dir: Path
    figures_dir: Path
    notes_dir: Path
    outputs_dir: Path


def prepare_paper_workspace(
    paper_source: str | None,
    paper: PaperInfo,
    root: Path = RESULT_ROOT,
) -> PaperWorkspace:
    slug = build_paper_slug(paper_source, paper.title)
    workspace = PaperWorkspace(
        slug=slug,
        root=root / slug,
        source_dir=root / slug / "source",
        extracted_dir=root / slug / "extracted",
        figures_dir=root / slug / "extracted" / "figures",
        notes_dir=root / slug / "notes",
        outputs_dir=root / slug / "outputs",
    )
    for path in (
        workspace.root,
        workspace.source_dir,
        workspace.extracted_dir,
        workspace.figures_dir,
        workspace.notes_dir,
        workspace.outputs_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)

    if paper_source:
        source_path = Path(paper_source)
        if source_path.exists():
            target = workspace.source_dir / source_path.name
            if not target.exists():
                shutil.copy2(source_path, target)
        else:
            (workspace.source_dir / "paper-source.txt").write_text(paper_source, encoding="utf-8")

    return workspace


def build_paper_slug(paper_source: str | None, title: str) -> str:
    source_path = Path(paper_source) if paper_source else None
    generic_stems = {"paper", "note", "notes", "study", "analysis"}
    if source_path and source_path.suffix and source_path.stem.lower() not in generic_stems:
        base = source_path.stem
    else:
        base = title
    slug = _slugify(base)
    if slug:
        return slug
    fallback = title or paper_source or "paper"
    digest = hashlib.sha1(fallback.encode("utf-8")).hexdigest()[:8]
    return f"paper-{digest}"


def write_paper_text(workspace: PaperWorkspace, text: str) -> Path:
    target = workspace.extracted_dir / "paper_text.md"
    target.write_text(text, encoding="utf-8")
    return target


def write_paper_understanding(workspace: PaperWorkspace, understanding: PaperUnderstanding) -> None:
    markdown = render_paper_understanding_markdown(understanding)
    (workspace.notes_dir / "paper-understanding.md").write_text(markdown, encoding="utf-8")
    (workspace.notes_dir / "paper-concepts.json").write_text(
        json.dumps(_safe_asdict(understanding), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def save_workspace_outputs(
    workspace: PaperWorkspace,
    markdown: str,
    second_pass: SecondPassEvidence | None = None,
) -> None:
    (workspace.outputs_dir / "study-note.md").write_text(markdown, encoding="utf-8")
    if second_pass:
        (workspace.outputs_dir / "concept2code.json").write_text(
            json.dumps(_safe_asdict(second_pass.final_concept2code_links), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def render_paper_understanding_markdown(understanding: PaperUnderstanding) -> str:
    lines = ["# Paper Understanding", "", understanding.summary or "No summary.", ""]
    if understanding.key_figure_pages:
        pages = ", ".join(str(page) for page in understanding.key_figure_pages)
        lines.extend(["## Key Figure Pages", f"- {pages}", ""])
    if understanding.figure_paths:
        lines.append("## Figure Assets")
        lines.extend(f"- {path}" for path in understanding.figure_paths)
        lines.append("")
    lines.append("## Concepts")
    if understanding.concepts:
        for concept in understanding.concepts:
            lines.append(f"- `{concept.concept}` [{concept.paper_status}]")
            lines.append(f"  - 摘要: {concept.summary}")
            if concept.structure_roles:
                lines.append(f"  - 结构角色: {', '.join(concept.structure_roles)}")
            if concept.supporting_evidence:
                lines.append(f"  - 证据: {concept.supporting_evidence}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Questions")
    if understanding.questions:
        lines.extend(f"- {question}" for question in understanding.questions)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug[:80]


def _safe_asdict(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, list):
        return [_safe_asdict(item) for item in obj]
    if isinstance(obj, tuple):
        return [_safe_asdict(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _safe_asdict(value) for key, value in obj.items()}
    try:
        data = asdict(obj)
    except TypeError:
        return obj
    return {key: _safe_asdict(value) for key, value in data.items()}
