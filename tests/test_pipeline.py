from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from study_agent.analyzer.code import build_code_map, build_open_questions, build_reading_path
from study_agent.analyzer.paper import analyze_paper
from study_agent.composer import compose_markdown
from study_agent.models import AgentConfig, StudyArtifact, StudyRequest, TasteProfile
from study_agent.paper import build_paper_slug, build_paper_understanding
from study_agent.pipeline import execute_analysis
from study_agent.planner import build_plan
from study_agent.repo import ingest_paper, ingest_repo


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
        paper_understanding = build_paper_understanding(paper_info, plan.focus_terms)
        cards = analyze_paper(paper_info, plan, paper_understanding)
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
            paper_understanding=paper_understanding,
        )
        markdown = compose_markdown(artifact)

        self.assertIn("Demo VLA 架构学习笔记", markdown)
        self.assertIn("kv_cache", markdown)
        self.assertIn("model.py", markdown)
        self.assertIn("File groups", markdown)
        self.assertIn("Architecture entry candidates", markdown)
        self.assertIn("Model candidates", markdown)
        self.assertIn("Candidate reason debug", markdown)
        self.assertIn("AST ranking debug", markdown)
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
        paper_understanding = build_paper_understanding(paper_info, plan.focus_terms)
        cards = analyze_paper(paper_info, plan, paper_understanding)
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
            paper_understanding=paper_understanding,
        )
        markdown = compose_markdown(artifact)

        self.assertIn("[Missing Evidence]", markdown)
        self.assertIn("code alignment confidence is low", markdown)
        self.assertIn("No obvious standalone loss/objective file found", markdown)

    def test_architecture_focus_reading_path_prefers_architecture_entries(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_pipeline_architecture_focus"
        repo = tmp_path / "repo"
        (repo / "src" / "demo" / "models").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "demo" / "models" / "layers").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "demo" / "training").mkdir(parents=True, exist_ok=True)
        (repo / "web_infer_utils" / "client").mkdir(parents=True, exist_ok=True)

        paper = tmp_path / "paper.md"
        paper.write_text("# Demo Repo\n\nArchitecture matters here.", encoding="utf-8")
        (repo / "src" / "demo" / "models" / "demo_vla.py").write_text(
            "class DemoVLA:\n    pass\n",
            encoding="utf-8",
        )
        (repo / "src" / "demo" / "models" / "vision_backbone.py").write_text(
            "class VisionBackbone:\n    pass\n",
            encoding="utf-8",
        )
        (repo / "src" / "demo" / "models" / "layers" / "attention.py").write_text(
            "class Attention:\n    pass\n",
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
        self.assertEqual(reading_path[1].path, "src/demo/models/vision_backbone.py")
        self.assertEqual(reading_path[2].path, "src/demo/models/layers/attention.py")

    def test_codex_engine_degrades_to_offline_when_evidence_quality_gate_fails(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_pipeline_quality_gate"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        paper = tmp_path / "paper.md"
        paper.write_text("", encoding="utf-8")
        (repo / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")

        request = StudyRequest(
            paper_source=str(paper),
            repo_source=str(repo),
            focus=["bridge_attention"],
            output_path=tmp_path / "out.md",
            engine="codex",
        )
        config = AgentConfig(
            auth_path=tmp_path / "auth.json",
            api_url="https://example.invalid",
            model="gpt-5.5",
            zotero_data_dir=tmp_path / "zotero",
        )

        with patch("study_agent.pipeline.assert_codex_ready") as mock_ready:
            with patch("study_agent.pipeline.run_codex") as mock_codex:
                result = execute_analysis(request, config=config)

        self.assertIsNone(result.session_dir)
        self.assertEqual(mock_ready.call_count, 0)
        self.assertEqual(mock_codex.call_count, 0)
        self.assertTrue(result.output_path.exists())
        markdown = result.output_path.read_text(encoding="utf-8")
        self.assertIn("Evidence quality gate status", markdown)
        self.assertIn("downgraded to an offline-style result", markdown)

    def test_execute_analysis_creates_paper_workspace_outputs(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_pipeline_paper_workspace"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        paper = tmp_path / "paper.md"
        paper.write_text("# Demo Paper\n\nBridge attention is explicit in the paper.", encoding="utf-8")
        (repo / "model.py").write_text(
            "class DemoVLA:\n"
            "    def sample_actions(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        request = StudyRequest(
            paper_source=str(paper),
            repo_source=str(repo),
            focus=["bridge_attention"],
            output_path=tmp_path / "out.md",
            engine="offline",
        )

        execute_analysis(request)

        slug = build_paper_slug(str(paper), "Demo Paper")
        workspace = Path.cwd() / "result" / slug
        self.assertTrue((workspace / "extracted" / "paper_text.md").exists())
        self.assertTrue((workspace / "notes" / "paper-understanding.md").exists())
        self.assertTrue((workspace / "outputs" / "study-note.md").exists())


if __name__ == "__main__":
    unittest.main()
