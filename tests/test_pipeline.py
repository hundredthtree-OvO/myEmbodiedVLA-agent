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
        self.assertIn("Architecture entry candidates", markdown)
        self.assertIn("Model candidates", markdown)
        self.assertIn("Candidate reason debug", markdown)
        self.assertIn("No obvious core model files were found", markdown)
        self.assertIn("No obvious docs/readme files were found", markdown)

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
        self.assertIn("No obvious standalone loss/objective file found", markdown)

    def test_architecture_focus_reading_path_prefers_architecture_entries(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_pipeline_architecture_focus"
        repo = tmp_path / "repo"
        (repo / "src" / "demo" / "models").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "demo" / "training").mkdir(parents=True, exist_ok=True)
        (repo / "web_infer_utils" / "client").mkdir(parents=True, exist_ok=True)

        paper = tmp_path / "paper.md"
        paper.write_text("# Demo Repo\n\nArchitecture matters here.", encoding="utf-8")
        (repo / "src" / "demo" / "models" / "demo_vla.py").write_text(
            "class DemoVLA:\n    pass\n",
            encoding="utf-8",
        )
        (repo / "src" / "demo" / "training" / "config.py").write_text(
            "class TrainConfig:\n    pass\n",
            encoding="utf-8",
        )
        (repo / "web_infer_utils" / "client" / "websocket_client_policy.py").write_text(
            "class WebsocketClientPolicy:\n    pass\n",
            encoding="utf-8",
        )

        request = StudyRequest(
            paper_source=str(paper),
            repo_source=str(repo),
            focus=["architecture"],
            output_path=tmp_path / "out.md",
            engine="offline",
        )
        profile = TasteProfile()
        plan = build_plan(request, profile)
        repo_info = ingest_repo(request.repo_source, plan.focus_terms)
        reading_path = build_reading_path(repo_info, plan)

        self.assertGreater(len(reading_path), 0)
        self.assertEqual(reading_path[0].path, "src/demo/models/demo_vla.py")


if __name__ == "__main__":
    unittest.main()
