from __future__ import annotations

import unittest
from pathlib import Path

from study_agent.ingest import ingest_repo
from study_agent.prompt_builder import _repo_block


class RepoEvidenceTests(unittest.TestCase):
    def test_ingest_repo_builds_structured_file_groups_and_candidates(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence"
        repo = root / "repo"
        (repo / "configs").mkdir(parents=True, exist_ok=True)
        (repo / "models").mkdir(parents=True, exist_ok=True)
        (repo / "losses").mkdir(parents=True, exist_ok=True)
        (repo / "data").mkdir(parents=True, exist_ok=True)
        (repo / "utils").mkdir(parents=True, exist_ok=True)
        (repo / "env").mkdir(parents=True, exist_ok=True)

        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "train.py").write_text("def train():\n    pass\n", encoding="utf-8")
        (repo / "eval.py").write_text("def eval_step():\n    pass\n", encoding="utf-8")
        (repo / "configs" / "model.yaml").write_text("model: demo\n", encoding="utf-8")
        (repo / "models" / "policy.py").write_text("class Policy:\n    pass\n", encoding="utf-8")
        (repo / "losses" / "objective.py").write_text("def compute_loss():\n    pass\n", encoding="utf-8")
        (repo / "data" / "dataset.py").write_text("class Dataset:\n    pass\n", encoding="utf-8")
        (repo / "utils" / "helpers.py").write_text("VALUE = 1\n", encoding="utf-8")
        (repo / "env" / "robot_env.py").write_text("class RobotEnv:\n    pass\n", encoding="utf-8")

        repo_info = ingest_repo(str(repo), ["policy", "loss"])

        self.assertIn("README.md", repo_info.file_groups["docs"])
        self.assertIn("train.py", repo_info.file_groups["train_scripts"])
        self.assertIn("eval.py", repo_info.file_groups["inference_scripts"])
        self.assertIn("configs/model.yaml", repo_info.file_groups["configs"])
        self.assertIn("models/policy.py", repo_info.file_groups["model_policy"])
        self.assertIn("losses/objective.py", repo_info.file_groups["loss_objective"])
        self.assertIn("data/dataset.py", repo_info.file_groups["data"])
        self.assertIn("utils/helpers.py", repo_info.file_groups["utils"])
        self.assertIn("env/robot_env.py", repo_info.file_groups["env_robot_interface"])

        self.assertIn("train.py", repo_info.train_candidates)
        self.assertIn("eval.py", repo_info.inference_candidates)
        self.assertIn("configs/model.yaml", repo_info.config_candidates)
        self.assertIn("models/policy.py", repo_info.model_candidates)
        self.assertIn("data/dataset.py", repo_info.data_candidates)

    def test_ingest_repo_allows_multi_role_files(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_overlap"
        repo = root / "repo"
        (repo / "models").mkdir(parents=True, exist_ok=True)
        (repo / "models" / "train_policy.py").write_text("class TrainPolicy:\n    pass\n", encoding="utf-8")

        repo_info = ingest_repo(str(repo), ["policy"])

        self.assertIn("models/train_policy.py", repo_info.file_groups["model_policy"])
        self.assertIn("models/train_policy.py", repo_info.file_groups["train_scripts"])

    def test_repo_block_exposes_structured_sections(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_prompt"
        repo = root / "repo"
        (repo / "configs").mkdir(parents=True, exist_ok=True)
        (repo / "models").mkdir(parents=True, exist_ok=True)
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "train.py").write_text("def train():\n    pass\n", encoding="utf-8")
        (repo / "configs" / "model.yaml").write_text("model: demo\n", encoding="utf-8")
        (repo / "models" / "policy.py").write_text("class Policy:\n    pass\n", encoding="utf-8")

        repo_info = ingest_repo(str(repo), ["policy"])
        block = _repo_block(repo_info)

        self.assertIn("File groups:", block)
        self.assertIn("Model candidates:", block)
        self.assertIn("Train candidates:", block)
        self.assertIn("Config candidates:", block)
        self.assertIn("Repository diagnostics:", block)


if __name__ == "__main__":
    unittest.main()
