from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from study_agent.models import PaperInfo, PaperSection
from study_agent.paper import (
    build_paper_slug,
    build_paper_understanding,
    prepare_paper_workspace,
    render_pdf_pages,
    write_paper_text,
    write_paper_understanding,
)


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

    def test_build_paper_understanding_extracts_claims_and_explicit_concepts(self) -> None:
        paper = PaperInfo(
            source="demo",
            title="Bridge Attention for VLA",
            sections=[PaperSection("Method", "We propose Bridge Attention (BA) for action prediction.")],
            raw_excerpt="We propose Bridge Attention (BA) for action prediction. Our method uses action queries and condition KV.",
            text="We propose Bridge Attention (BA) for action prediction. Our method uses action queries and condition KV.",
        )

        understanding = build_paper_understanding(paper, [])

        self.assertGreaterEqual(len(understanding.claims), 1)
        self.assertIn("Bridge Attention", [concept.concept for concept in understanding.concepts])
        bridge = next(concept for concept in understanding.concepts if concept.concept == "Bridge Attention")
        self.assertEqual(bridge.paper_status, "paper_explicit")
        self.assertGreaterEqual(len(understanding.questions), 1)

    def test_render_pdf_pages_reuses_existing_png(self) -> None:
        tmp_root = Path.cwd() / ".tmp" / "test_render_pdf_pages"
        pdf_path = tmp_root / "paper.pdf"
        output_dir = tmp_root / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n")
        existing = output_dir / "page-03.png"
        existing.write_bytes(b"png")

        with patch("study_agent.paper.pdf._open_pdf_document") as mock_document:
            rendered = render_pdf_pages(pdf_path, [3], output_dir)

        self.assertEqual(rendered, [existing])
        self.assertEqual(mock_document.call_count, 1)

    def test_render_pdf_pages_calls_pdftoppm_for_missing_page(self) -> None:
        tmp_root = Path.cwd() / ".tmp" / "test_render_pdf_pages_missing"
        pdf_path = tmp_root / "paper.pdf"
        output_dir = tmp_root / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n")
        target = output_dir / "page-02.png"
        if target.exists():
            target.unlink()

        class _FakePixmap:
            def save(self, destination):
                Path(destination).write_bytes(b"png")

        class _FakePage:
            def get_pixmap(self, matrix, alpha):  # noqa: ARG002
                return _FakePixmap()

        class _FakeDocument:
            page_count = 2

            def load_page(self, index):
                self.loaded_index = index
                return _FakePage()

            def close(self):
                return None

        class _FakeFitz:
            @staticmethod
            def Matrix(x, y):  # noqa: ARG004
                return object()

        with patch("study_agent.paper.pdf._import_fitz", return_value=_FakeFitz()):
            with patch("study_agent.paper.pdf._open_pdf_document", return_value=_FakeDocument()) as mock_open:
                rendered = render_pdf_pages(pdf_path, [2], output_dir)

        self.assertEqual(mock_open.call_count, 1)
        self.assertEqual(rendered, [output_dir / "page-02.png"])


if __name__ == "__main__":
    unittest.main()
