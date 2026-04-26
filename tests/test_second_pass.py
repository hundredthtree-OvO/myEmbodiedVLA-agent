from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from study_agent.config import load_config
from study_agent.ingest import ingest_repo
from study_agent.models import (
    AgentConfig,
    MissingFileSuggestion,
    SecondPassFileEvidence,
    SecondPassRoundResult,
    StudyRequest,
    UncertainLink,
)
from study_agent.pipeline import execute_analysis
from study_agent.planner import build_plan
from study_agent.profile import load_profile
from study_agent.second_pass import validate_round2_candidates


class SecondPassTests(unittest.TestCase):
    def test_validate_round2_candidates_filters_noise_and_missing_files(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_second_pass_validate"
        repo = tmp_path / "repo"
        (repo / "models").mkdir(parents=True, exist_ok=True)
        (repo / "utils").mkdir(parents=True, exist_ok=True)
        (repo / "scripts").mkdir(parents=True, exist_ok=True)
        (repo / "models" / "policy.py").write_text(
            "class Policy:\n"
            "    def forward(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        (repo / "models" / "bridge.py").write_text(
            "class Bridge:\n"
            "    pass\n",
            encoding="utf-8",
        )
        (repo / "utils" / "helpers.py").write_text("VALUE = 1\n", encoding="utf-8")
        (repo / "scripts" / "compute_norm_stats.py").write_text("print('x')\n", encoding="utf-8")
        (repo / "train.py").write_text(
            "from models.policy import Policy\n"
            "from models.bridge import Bridge\n"
            "policy = Policy()\n"
            "bridge = Bridge()\n",
            encoding="utf-8",
        )

        request = StudyRequest(
            paper_source=str(tmp_path / "paper.md"),
            repo_source=str(repo),
            focus=["architecture"],
            output_path=tmp_path / "out.md",
            engine="offline",
        )
        (tmp_path / "paper.md").write_text("# Demo\n\nArchitecture focus.\n", encoding="utf-8")
        plan = build_plan(request, load_profile())
        repo_info = ingest_repo(request.repo_source, plan.focus_terms)

        round1_result = SecondPassRoundResult(
            round_id=1,
            summary="demo",
            files=[
                SecondPassFileEvidence(
                    path="models/policy.py",
                    selected_reason="entry",
                    excerpt="class Policy",
                    top_symbols=["Policy.forward"],
                    local_evidence=[],
                )
            ],
            concept_links=[],
            uncertain_links=[UncertainLink(concept="bridge", reason="check bridge", candidate_files=["models/bridge.py"])],
            missing_files=[
                MissingFileSuggestion(path="utils/helpers.py", reason="helper noise"),
                MissingFileSuggestion(path="scripts/compute_norm_stats.py", reason="script noise"),
                MissingFileSuggestion(path="missing.py", reason="not found"),
            ],
        )

        validated = validate_round2_candidates(repo_info, round1_result, ["models/policy.py"], max_files=4)

        self.assertEqual(validated, ["models/bridge.py"])

    def test_execute_analysis_runs_two_round_second_pass_and_persists_structured_evidence(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_second_pass_pipeline"
        if tmp_path.exists():
            shutil.rmtree(tmp_path)
        repo = tmp_path / "repo"
        session_dir = tmp_path / "session"
        session_dir.mkdir(parents=True, exist_ok=True)
        (repo / "models").mkdir(parents=True, exist_ok=True)
        paper = tmp_path / "paper.md"
        paper.write_text("# Demo\n\nAction head and bridge matter.\n", encoding="utf-8")
        (repo / "models" / "policy.py").write_text(
            "class Policy:\n"
            "    def forward(self):\n"
            "        return self.predict_action()\n"
            "    def predict_action(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        (repo / "models" / "bridge.py").write_text(
            "class Bridge:\n"
            "    def forward(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        (repo / "train.py").write_text(
            "from models.policy import Policy\n"
            "from models.bridge import Bridge\n"
            "policy = Policy()\n"
            "bridge = Bridge()\n",
            encoding="utf-8",
        )

        request = StudyRequest(
            paper_source=str(paper),
            repo_source=str(repo),
            focus=["architecture"],
            output_path=tmp_path / "out.md",
            engine="codex",
        )
        config = AgentConfig(
            auth_path=tmp_path / "auth.json",
            api_url="https://example.invalid",
            model="gpt-5.5",
            zotero_data_dir=tmp_path / "zotero",
            second_pass_enabled=True,
            second_pass_round1_max_files=5,
            second_pass_round2_max_files=3,
        )

        round1_raw = json.dumps(
            {
                "summary": "Round 1 found the policy entry but still needs the bridge.",
                "concept_links": [
                    {
                        "concept": "policy",
                        "status": "CONFIRMED",
                        "files": ["models/policy.py"],
                        "symbols": ["Policy.forward"],
                        "evidence_span": "class Policy",
                        "confidence": "high",
                        "reason": "forward calls predict_action",
                        "round": 1,
                    }
                ],
                "uncertain_links": [
                    {
                        "concept": "bridge",
                        "reason": "bridge path needs extra file grounding",
                        "candidate_files": ["models/bridge.py"],
                    }
                ],
                "missing_files": [
                    {"path": "models/bridge.py", "reason": "bridge file is needed"},
                    {"path": "utils/helpers.py", "reason": "should be filtered out"},
                ],
            },
            ensure_ascii=False,
        )
        round2_raw = json.dumps(
            {
                "summary": "Round 2 confirms the bridge link.",
                "concept_links": [
                    {
                        "concept": "bridge",
                        "status": "CONFIRMED",
                        "files": ["models/bridge.py"],
                        "symbols": ["Bridge.forward"],
                        "evidence_span": "class Bridge",
                        "confidence": "medium",
                        "reason": "bridge forward is defined directly",
                        "round": 2,
                    }
                ],
                "uncertain_links": [],
                "missing_files": [],
            },
            ensure_ascii=False,
        )

        with patch("study_agent.pipeline.assert_codex_ready") as mock_ready:
            with patch("study_agent.pipeline.create_session_dir", return_value=session_dir):
                with patch("study_agent.pipeline.select_second_pass_files", return_value=["models/policy.py"]):
                    with patch(
                        "study_agent.pipeline.run_codex",
                        side_effect=[round1_raw, round2_raw, "# Final Markdown\n\nDone.\n"],
                    ) as mock_codex:
                        result = execute_analysis(request, config=config)

        self.assertEqual(result.output_path, tmp_path / "out.md")
        self.assertEqual(mock_ready.call_count, 1)
        self.assertEqual(mock_codex.call_count, 3)
        self.assertTrue((session_dir / "second-pass-round-1.json").exists())
        self.assertTrue((session_dir / "second-pass-round-2.json").exists())
        self.assertTrue((session_dir / "concept2code.json").exists())

        concept_links = json.loads((session_dir / "concept2code.json").read_text(encoding="utf-8"))
        concepts = {item["concept"] for item in concept_links}
        self.assertEqual(concepts, {"policy", "bridge"})
        bridge_link = next(item for item in concept_links if item["concept"] == "bridge")
        self.assertEqual(bridge_link["round"], 2)
        round2_json = json.loads((session_dir / "second-pass-round-2.json").read_text(encoding="utf-8"))
        self.assertEqual(round2_json["files"][0]["path"], "models/bridge.py")

    def test_execute_analysis_skips_round2_when_no_missing_files(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_second_pass_pipeline_skip_round2"
        if tmp_path.exists():
            shutil.rmtree(tmp_path)
        repo = tmp_path / "repo"
        session_dir = tmp_path / "session"
        session_dir.mkdir(parents=True, exist_ok=True)
        (repo / "models").mkdir(parents=True, exist_ok=True)
        paper = tmp_path / "paper.md"
        paper.write_text("# Demo\n\nSingle-file architecture.\n", encoding="utf-8")
        (repo / "models" / "policy.py").write_text(
            "class Policy:\n"
            "    def forward(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        (repo / "train.py").write_text(
            "from models.policy import Policy\n"
            "policy = Policy()\n",
            encoding="utf-8",
        )

        request = StudyRequest(
            paper_source=str(paper),
            repo_source=str(repo),
            focus=["architecture"],
            output_path=tmp_path / "out.md",
            engine="codex",
        )
        config = AgentConfig(
            auth_path=tmp_path / "auth.json",
            api_url="https://example.invalid",
            model="gpt-5.5",
            zotero_data_dir=tmp_path / "zotero",
            second_pass_enabled=True,
            second_pass_round1_max_files=4,
            second_pass_round2_max_files=2,
        )
        round1_raw = json.dumps(
            {
                "summary": "Policy is already confirmed.",
                "concept_links": [
                    {
                        "concept": "policy",
                        "status": "CONFIRMED",
                        "files": ["models/policy.py"],
                        "symbols": ["Policy.forward"],
                        "evidence_span": "class Policy",
                        "confidence": "high",
                        "reason": "policy forward is local",
                        "round": 1,
                    }
                ],
                "uncertain_links": [],
                "missing_files": [],
            },
            ensure_ascii=False,
        )

        with patch("study_agent.pipeline.assert_codex_ready"):
            with patch("study_agent.pipeline.create_session_dir", return_value=session_dir):
                with patch(
                    "study_agent.pipeline.run_codex",
                    side_effect=[round1_raw, "# Final Markdown\n\nDone.\n"],
                ) as mock_codex:
                    execute_analysis(request, config=config)

        self.assertEqual(mock_codex.call_count, 2)
        self.assertTrue((session_dir / "second-pass-round-1.json").exists())
        self.assertFalse((session_dir / "second-pass-round-2.json").exists())

    def test_execute_analysis_respects_second_pass_disabled(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_second_pass_disabled"
        if tmp_path.exists():
            shutil.rmtree(tmp_path)
        repo = tmp_path / "repo"
        session_dir = tmp_path / "session"
        session_dir.mkdir(parents=True, exist_ok=True)
        (repo / "models").mkdir(parents=True, exist_ok=True)
        paper = tmp_path / "paper.md"
        paper.write_text("# Demo\n\nNo second pass.\n", encoding="utf-8")
        (repo / "models" / "policy.py").write_text("class Policy:\n    pass\n", encoding="utf-8")

        request = StudyRequest(
            paper_source=str(paper),
            repo_source=str(repo),
            focus=["architecture"],
            output_path=tmp_path / "out.md",
            engine="codex",
        )
        config = AgentConfig(
            auth_path=tmp_path / "auth.json",
            api_url="https://example.invalid",
            model="gpt-5.5",
            zotero_data_dir=tmp_path / "zotero",
            second_pass_enabled=False,
        )

        with patch("study_agent.pipeline.assert_codex_ready"):
            with patch("study_agent.pipeline.create_session_dir", return_value=session_dir):
                with patch("study_agent.pipeline.run_codex", return_value="# Final Markdown\n") as mock_codex:
                    execute_analysis(request, config=config)

        self.assertEqual(mock_codex.call_count, 1)
        self.assertFalse((session_dir / "second-pass-round-1.json").exists())
        self.assertFalse((session_dir / "concept2code.json").exists())

    def test_load_config_reads_second_pass_defaults(self) -> None:
        config_path = Path.cwd() / ".tmp" / "test_second_pass_config" / "config.json"
        if config_path.parent.exists():
            shutil.rmtree(config_path.parent)

        config = load_config(config_path)

        self.assertTrue(config.second_pass_enabled)
        self.assertEqual(config.second_pass_round1_max_files, 8)
        self.assertEqual(config.second_pass_round2_max_files, 4)


if __name__ == "__main__":
    unittest.main()
