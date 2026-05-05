from __future__ import annotations

import json
import unittest
from pathlib import Path

from study_agent.cli import main
from study_agent.copilot import ask_workspace, attach_paper_to_workspace, build_card, index_workspace
from study_agent.workspace_store import workspace_root


class CopilotWorkflowTests(unittest.TestCase):
    def test_index_workspace_creates_manifest_and_graph_artifacts(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_copilot_index"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "policy.py").write_text(
            "class ImplicitActionReasoner:\n"
            "    pass\n\n"
            "def predict_action():\n"
            "    return None\n",
            encoding="utf-8",
        )

        result = index_workspace(str(repo), "Copilot Index Demo")

        workspace = workspace_root(result.manifest.workspace_id)
        self.assertTrue((workspace / "manifest.json").exists())
        self.assertTrue((workspace / "graph_nodes.jsonl").exists())
        self.assertTrue((workspace / "graph_edges.jsonl").exists())
        self.assertGreater(result.manifest.graph_node_count, 0)
        self.assertGreater(result.manifest.graph_edge_count, 0)

    def test_ask_implementation_returns_symbol_and_file_evidence(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_copilot_implementation"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "policy.py").write_text(
            "class ImplicitActionReasoner:\n"
            "    def forward(self):\n"
            "        return None\n",
            encoding="utf-8",
        )

        result = index_workspace(str(repo), "Implementation Workspace")
        answer = ask_workspace(result.manifest.workspace_id, "Explain the implementation of ImplicitActionReasoner.")

        self.assertEqual(answer.answer_type, "implementation")
        self.assertTrue(answer.code_evidence)
        self.assertEqual(answer.code_evidence[0].path, "policy.py")
        self.assertIn("ImplicitActionReasoner", answer.code_evidence[0].symbol)

    def test_ask_rationale_with_attached_paper_returns_paper_evidence(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_copilot_rationale_with_paper"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "policy.py").write_text(
            "class ImplicitActionReasoner:\n"
            "    def forward(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        paper = tmp_path / "paper.md"
        paper.write_text(
            "# Demo Paper\n\n"
            "We propose an Implicit Action Reasoner to stabilize action prediction.\n",
            encoding="utf-8",
        )

        result = index_workspace(str(repo), "Rationale With Paper")
        attach_paper_to_workspace(result.manifest.workspace_id, str(paper))
        answer = ask_workspace(result.manifest.workspace_id, "Why is the Implicit Action Reasoner designed this way?")

        self.assertEqual(answer.answer_type, "rationale")
        self.assertTrue(answer.paper_evidence)
        self.assertTrue(any("Implicit Action Reasoner" in item.excerpt for item in answer.paper_evidence))

    def test_ask_rationale_without_paper_marks_code_only_inference(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_copilot_rationale_without_paper"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "policy.py").write_text(
            "class ImplicitActionReasoner:\n"
            "    def forward(self):\n"
            "        return None\n",
            encoding="utf-8",
        )

        result = index_workspace(str(repo), "Rationale Without Paper")
        answer = ask_workspace(result.manifest.workspace_id, "Why is the Implicit Action Reasoner designed this way?")

        self.assertEqual(answer.answer_type, "rationale")
        self.assertFalse(answer.paper_evidence)
        self.assertTrue(any("No attached paper evidence matched" in item for item in answer.uncertainty))

    def test_index_workspace_survives_non_python_files(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_copilot_non_python"
        repo = tmp_path / "repo"
        (repo / "src").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "policy.ts").write_text("export class Policy {}\n", encoding="utf-8")
        (repo / "config.yaml").write_text("model: demo\n", encoding="utf-8")

        result = index_workspace(str(repo), "Non Python Workspace")

        workspace = workspace_root(result.manifest.workspace_id)
        node_lines = (workspace / "graph_nodes.jsonl").read_text(encoding="utf-8").splitlines()
        nodes = [json.loads(line) for line in node_lines if line.strip()]
        self.assertTrue(any(node["attributes"].get("language") == "typescript" for node in nodes if node["node_type"] == "File"))
        self.assertTrue(any(node["node_type"] == "Config" for node in nodes))

    def test_build_card_creates_module_or_question_card(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_copilot_card"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "policy.py").write_text(
            "class ImplicitActionReasoner:\n"
            "    def forward(self):\n"
            "        return None\n",
            encoding="utf-8",
        )

        result = index_workspace(str(repo), "Card Workspace")
        ask_workspace(result.manifest.workspace_id, "Explain the implementation of ImplicitActionReasoner.")
        card = build_card(result.manifest.workspace_id, "ImplicitActionReasoner")

        self.assertEqual(card.card_type, "ModuleCard")
        workspace = workspace_root(result.manifest.workspace_id)
        self.assertTrue((workspace / "cards" / f"{card.card_id}.md").exists())

    def test_deprecated_analyze_wrapper_exports_note(self) -> None:
        tmp_path = Path.cwd() / ".tmp" / "test_copilot_analyze_wrapper"
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        paper = tmp_path / "paper.md"
        paper.write_text("# Demo Paper\n\nWe propose an action reasoner.\n", encoding="utf-8")
        (repo / "policy.py").write_text(
            "class ActionReasoner:\n"
            "    def forward(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        out = tmp_path / "note.md"

        exit_code = main(
            [
                "analyze",
                "--paper",
                str(paper),
                "--repo",
                str(repo),
                "--focus",
                "action_reasoner",
                "--out",
                str(out),
                "--engine",
                "offline",
            ]
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(out.exists())
        markdown = out.read_text(encoding="utf-8")
        self.assertIn("Research Workspace", markdown)


if __name__ == "__main__":
    unittest.main()
