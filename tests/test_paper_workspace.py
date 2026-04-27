from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from study_agent.models import PaperInfo, PaperSection
from study_agent.paper_understanding import build_paper_understanding
from study_agent.paper_workspace import (
    build_paper_slug,
    prepare_paper_workspace,
    write_paper_text,
    write_paper_understanding,
)
from study_agent.pdf import render_pdf_pages


class PaperWorkspaceTests(unittest.TestCase):
    def test_build_paper_slug_prefers_source_stem(self) -> None:
        slug = build_paper_slug("E:/papers/VLA-Adapter.pdf", "Ignored Title")
        self.assertEqual(slug, "vla-adapter")

    def test_prepare_workspace_and_write_outputs(self) -> None:
        tmp_root = Path.cwd() / ".tmp" / "test_paper_workspace"
        source = tmp_root / "paper.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# Demo Paper\n\nBridge attention matters.", encoding="utf-8")
        paper = PaperInfo(
            source=str(source),
            title="Demo Paper",
            sections=[PaperSection("Overview", "Bridge attention matters.")],
            raw_excerpt="Bridge attention matters.",
            text="Bridge attention matters.",
        )

        workspace = prepare_paper_workspace(str(source), paper, root=tmp_root / "result")
        write_paper_text(workspace, paper.text)
        understanding = build_paper_understanding(paper, ["bridge_attention"])
        write_paper_understanding(workspace, understanding)

        self.assertTrue((workspace.source_dir / "paper.md").exists())
        self.assertTrue((workspace.extracted_dir / "paper_text.md").exists())
        self.assertTrue((workspace.notes_dir / "paper-understanding.md").exists())
        self.assertTrue((workspace.notes_dir / "paper-concepts.json").exists())

    def test_render_pdf_pages_reuses_existing_png(self) -> None:
        tmp_root = Path.cwd() / ".tmp" / "test_render_pdf_pages"
        pdf_path = tmp_root / "paper.pdf"
        output_dir = tmp_root / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n")
        existing = output_dir / "page-03.png"
        existing.write_bytes(b"png")

        with patch("study_agent.pdf.subprocess.run") as mock_run:
            rendered = render_pdf_pages(pdf_path, [3], output_dir)

        self.assertEqual(rendered, [existing])
        self.assertEqual(mock_run.call_count, 0)

    def test_render_pdf_pages_calls_pdftoppm_for_missing_page(self) -> None:
        tmp_root = Path.cwd() / ".tmp" / "test_render_pdf_pages_missing"
        pdf_path = tmp_root / "paper.pdf"
        output_dir = tmp_root / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n")
        target = output_dir / "page-02.png"
        if target.exists():
            target.unlink()

        def _fake_run(cmd, **kwargs):
            target = Path(cmd[-1]).with_suffix(".png")
            target.write_bytes(b"png")
            return None

        with patch("study_agent.pdf.shutil.which", return_value="pdftoppm"):
            with patch("study_agent.pdf.subprocess.run", side_effect=_fake_run) as mock_run:
                rendered = render_pdf_pages(pdf_path, [2], output_dir)

        self.assertEqual(mock_run.call_count, 1)
        self.assertEqual(rendered, [output_dir / "page-02.png"])


if __name__ == "__main__":
    unittest.main()
