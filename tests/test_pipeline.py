from __future__ import annotations

import unittest
from pathlib import Path

from study_agent.analyzer.code import build_code_map, build_open_questions, build_reading_path
from study_agent.analyzer.paper import analyze_paper
from study_agent.composer import compose_markdown
from study_agent.ingest import ingest_paper, ingest_repo
from study_agent.models import StudyArtifact, StudyRequest, TasteProfile
from study_agent.planner import build_plan


class PipelineTests(unittest.TestCase):
    def test_offline_pipeline(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_pipeline"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        paper = tmp_path / "paper.md"
        paper.write_text("# Demo VLA\n\nEAR uses kv_cache for action reasoning.", encoding="utf-8")
        model = repo / "model.py"
        model.write_text(
            "class DemoVLA:\n"
            "    def compute_loss(self):\n"
            "        kv_cache = None\n"
            "    def sample_actions(self):\n"
            "        return None\n",
            encoding="utf-8",
        )

        request = StudyRequest(
            paper_source=str(paper),
            repo_source=str(repo),
            focus=["EAR", "kv_cache"],
            output_path=tmp_path / "out.md",
            engine="offline",
        )
        profile = TasteProfile()
        plan = build_plan(request, profile)
        paper_info = ingest_paper(request.paper_source)
        repo_info = ingest_repo(request.repo_source, plan.focus_terms)
        cards = analyze_paper(paper_info, plan)
        code_map = build_code_map(repo_info, cards, plan)
        artifact = StudyArtifact(
            request=request,
            paper=paper_info,
            repo=repo_info,
            profile=profile,
            summary="demo",
            concept_cards=cards,
            code_map=code_map,
            reading_path=build_reading_path(repo_info, plan),
            open_questions=build_open_questions(repo_info, code_map, plan),
        )
        markdown = compose_markdown(artifact)

        self.assertIn("Demo VLA 架构学习笔记", markdown)
        self.assertIn("kv_cache", markdown)
        self.assertIn("model.py", markdown)
        self.assertIn("File groups", markdown)
        self.assertIn("Model candidates", markdown)

    def test_offline_pipeline_surfaces_missing_evidence_diagnostics(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_pipeline_missing_evidence"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        paper = tmp_path / "paper.md"
        paper.write_text("# Sparse Repo\n\nBridge attention is important here.", encoding="utf-8")
        (repo / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")

        request = StudyRequest(
            paper_source=str(paper),
            repo_source=str(repo),
            focus=["bridge_attention"],
            output_path=tmp_path / "out.md",
            engine="offline",
        )
        profile = TasteProfile()
        plan = build_plan(request, profile)
        paper_info = ingest_paper(request.paper_source)
        repo_info = ingest_repo(request.repo_source, plan.focus_terms)
        cards = analyze_paper(paper_info, plan)
        code_map = build_code_map(repo_info, cards, plan)
        artifact = StudyArtifact(
            request=request,
            paper=paper_info,
            repo=repo_info,
            profile=profile,
            summary="demo",
            concept_cards=cards,
            code_map=code_map,
            reading_path=build_reading_path(repo_info, plan),
            open_questions=build_open_questions(repo_info, code_map, plan),
        )
        markdown = compose_markdown(artifact)

        self.assertIn("[Missing Evidence]", markdown)
        self.assertIn("code alignment confidence is low", markdown)


if __name__ == "__main__":
    unittest.main()
