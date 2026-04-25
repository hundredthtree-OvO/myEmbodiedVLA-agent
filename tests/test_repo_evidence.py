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
        (repo / "models" / "transformer_impl.py").write_text("class TransformerImpl:\n    pass\n", encoding="utf-8")
        (repo / "web_infer_utils" / "client").mkdir(parents=True, exist_ok=True)
        (repo / "web_infer_utils" / "client" / "base_policy.py").write_text("class BasePolicy:\n    pass\n", encoding="utf-8")
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
        self.assertIn("models/transformer_impl.py", repo_info.file_groups["core_model"])
        self.assertIn("web_infer_utils/client/base_policy.py", repo_info.file_groups["deployment_policy"])
        self.assertIn("losses/objective.py", repo_info.file_groups["loss_objective"])
        self.assertIn("data/dataset.py", repo_info.file_groups["data"])
        self.assertIn("utils/helpers.py", repo_info.file_groups["utils"])
        self.assertIn("env/robot_env.py", repo_info.file_groups["env_robot_interface"])

        self.assertIn("train.py", repo_info.train_candidates)
        self.assertIn("eval.py", repo_info.inference_candidates)
        self.assertIn("configs/model.yaml", repo_info.config_candidates)
        self.assertIn("models/transformer_impl.py", repo_info.core_model_candidates)
        self.assertIn("web_infer_utils/client/base_policy.py", repo_info.deployment_policy_candidates)
        self.assertIn("models/policy.py", repo_info.architecture_entry_candidates)
        self.assertIn("configs/model.yaml", repo_info.config_entry_candidates)
        self.assertIn("web_infer_utils/client/base_policy.py", repo_info.deployment_entry_candidates)
        self.assertEqual(repo_info.model_candidates[0], "models/transformer_impl.py")
        self.assertIn("losses/objective.py", repo_info.loss_candidates)
        self.assertIn("data/dataset.py", repo_info.data_candidates)
        self.assertIn("env/robot_env.py", repo_info.env_candidates)
        self.assertIn("utils/helpers.py", repo_info.utils_candidates)
        self.assertIn("README.md", repo_info.docs_candidates)
        self.assertIn("models/policy.py", repo_info.candidate_reasons)
        self.assertTrue(
            any(reason.startswith("architecture_entry:") for reason in repo_info.candidate_reasons["models/policy.py"])
        )

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
        (repo / "web_infer_utils").mkdir(parents=True, exist_ok=True)
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "train.py").write_text("def train():\n    pass\n", encoding="utf-8")
        (repo / "configs" / "model.yaml").write_text("model: demo\n", encoding="utf-8")
        (repo / "models" / "policy.py").write_text("class Policy:\n    pass\n", encoding="utf-8")
        (repo / "web_infer_utils" / "base_policy.py").write_text("class BasePolicy:\n    pass\n", encoding="utf-8")
        (repo / "loss.py").write_text("def compute_loss():\n    pass\n", encoding="utf-8")

        repo_info = ingest_repo(str(repo), ["policy"])
        block = _repo_block(repo_info)

        self.assertIn("File groups:", block)
        self.assertIn("Architecture entry candidates:", block)
        self.assertIn("Config entry candidates:", block)
        self.assertIn("Deployment entry candidates:", block)
        self.assertIn("Core model candidates:", block)
        self.assertIn("Deployment/client policy candidates:", block)
        self.assertIn("Model candidates:", block)
        self.assertIn("Train candidates:", block)
        self.assertIn("Config candidates:", block)
        self.assertIn("Loss candidates:", block)
        self.assertIn("Docs candidates:", block)
        self.assertIn("Candidate reason debug:", block)
        self.assertIn("Repository diagnostics:", block)

    def test_repo_diagnostics_use_standalone_loss_wording(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_diagnostics"
        repo = root / "repo"
        (repo / "models").mkdir(parents=True, exist_ok=True)
        (repo / "runner").mkdir(parents=True, exist_ok=True)
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "models" / "policy.py").write_text(
            "class Policy:\n"
            "    def compute_loss(self):\n"
            "        return 0\n",
            encoding="utf-8",
        )
        (repo / "runner" / "trainer.py").write_text("def train():\n    loss = 1\n", encoding="utf-8")

        repo_info = ingest_repo(str(repo), ["loss", "policy"])
        block = _repo_block(repo_info)

        self.assertIn("No obvious standalone loss/objective file found.", block)
        self.assertIn("Loss/objective may be implemented inline in model/trainer/algorithm files.", block)

    def test_model_candidates_prioritize_core_model_over_deployment_wrappers(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_core_model_priority"
        repo = root / "repo"
        (repo / "models" / "ltx_models").mkdir(parents=True, exist_ok=True)
        (repo / "web_infer_utils" / "openpi_client" / "runtime" / "agents").mkdir(parents=True, exist_ok=True)
        (repo / "models" / "ltx_models" / "transformer_ltx_multiview.py").write_text(
            "class TransformerLTX:\n    pass\n",
            encoding="utf-8",
        )
        (repo / "web_infer_utils" / "openpi_client" / "runtime" / "agents" / "policy_agent.py").write_text(
            "class PolicyAgent:\n    pass\n",
            encoding="utf-8",
        )

        repo_info = ingest_repo(str(repo), ["policy", "latent"])

        self.assertIn("models/ltx_models/transformer_ltx_multiview.py", repo_info.core_model_candidates)
        self.assertIn(
            "web_infer_utils/openpi_client/runtime/agents/policy_agent.py",
            repo_info.deployment_policy_candidates,
        )
        self.assertEqual(repo_info.model_candidates[0], "models/ltx_models/transformer_ltx_multiview.py")

    def test_architecture_candidates_stay_ahead_of_deployment_and_config_noise(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_architecture_priority"
        repo = root / "repo"
        (repo / "src" / "demo" / "models").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "demo" / "training").mkdir(parents=True, exist_ok=True)
        (repo / "web_infer_utils" / "client").mkdir(parents=True, exist_ok=True)
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

        repo_info = ingest_repo(str(repo), ["architecture", "module"])

        self.assertEqual(repo_info.architecture_entry_candidates[0], "src/demo/models/demo_vla.py")
        self.assertIn("src/demo/training/config.py", repo_info.config_entry_candidates)
        self.assertIn(
            "web_infer_utils/client/websocket_client_policy.py",
            repo_info.deployment_entry_candidates,
        )
        self.assertNotEqual(
            repo_info.architecture_entry_candidates[0],
            "web_infer_utils/client/websocket_client_policy.py",
        )


if __name__ == "__main__":
    unittest.main()
