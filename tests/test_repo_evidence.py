from __future__ import annotations

import unittest
from pathlib import Path

from study_agent.repo import ingest_repo
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
        (repo / "models" / "vision_backbone.py").write_text("class VisionBackbone:\n    pass\n", encoding="utf-8")
        (repo / "models" / "layers").mkdir(parents=True, exist_ok=True)
        (repo / "models" / "layers" / "attention.py").write_text("class Attention:\n    pass\n", encoding="utf-8")
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
        self.assertIn("models/vision_backbone.py", repo_info.architecture_skeleton_candidates)
        self.assertIn("models/layers/attention.py", repo_info.architecture_component_candidates)
        self.assertIn("configs/model.yaml", repo_info.config_entry_candidates)
        self.assertIn("web_infer_utils/client/base_policy.py", repo_info.deployment_entry_candidates)
        self.assertIn(repo_info.model_candidates[0], repo_info.core_model_candidates)
        self.assertIn("losses/objective.py", repo_info.loss_candidates)
        self.assertIn("data/dataset.py", repo_info.data_candidates)
        self.assertIn("env/robot_env.py", repo_info.env_candidates)
        self.assertIn("utils/helpers.py", repo_info.utils_candidates)
        self.assertIn("README.md", repo_info.docs_candidates)
        self.assertIn("models/policy.py", repo_info.candidate_reasons)
        self.assertIn("models/policy.py", repo_info.ast_candidate_reasons)
        self.assertIn("models/policy.py", repo_info.ast_file_tags)
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
        (repo / "models" / "vision_backbone.py").write_text("class VisionBackbone:\n    pass\n", encoding="utf-8")
        (repo / "models" / "layers").mkdir(parents=True, exist_ok=True)
        (repo / "models" / "layers" / "attention.py").write_text("class Attention:\n    pass\n", encoding="utf-8")
        (repo / "web_infer_utils" / "base_policy.py").write_text("class BasePolicy:\n    pass\n", encoding="utf-8")
        (repo / "loss.py").write_text("def compute_loss():\n    pass\n", encoding="utf-8")

        repo_info = ingest_repo(str(repo), ["policy"])
        block = _repo_block(repo_info)

        self.assertIn("File groups:", block)
        self.assertIn("Architecture entry candidates:", block)
        self.assertIn("Architecture skeleton candidates:", block)
        self.assertIn("Architecture component candidates:", block)
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
        self.assertIn("AST ranking debug:", block)
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

    def test_architecture_subcategories_follow_entry_to_skeleton_to_component(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_architecture_subcategories"
        repo = root / "repo"
        (repo / "models" / "layers").mkdir(parents=True, exist_ok=True)
        (repo / "models" / "modules").mkdir(parents=True, exist_ok=True)

        (repo / "models" / "policy.py").write_text("class Policy:\n    pass\n", encoding="utf-8")
        (repo / "models" / "vision_backbone.py").write_text("class VisionBackbone:\n    pass\n", encoding="utf-8")
        (repo / "models" / "action_head.py").write_text("class ActionHead:\n    pass\n", encoding="utf-8")
        (repo / "models" / "layers" / "attention.py").write_text("class Attention:\n    pass\n", encoding="utf-8")
        (repo / "models" / "modules" / "projector.py").write_text("class Projector:\n    pass\n", encoding="utf-8")
        (repo / "configs").mkdir(parents=True, exist_ok=True)
        (repo / "configs" / "model.yaml").write_text("model: demo\n", encoding="utf-8")

        repo_info = ingest_repo(str(repo), ["architecture", "model"])

        self.assertEqual(repo_info.architecture_entry_candidates[0], "models/policy.py")
        self.assertIn("models/vision_backbone.py", repo_info.architecture_skeleton_candidates[:3])
        self.assertIn("models/action_head.py", repo_info.architecture_skeleton_candidates[:3])
        self.assertIn("models/modules/projector.py", repo_info.architecture_component_candidates[:3])
        self.assertIn("models/layers/attention.py", repo_info.architecture_component_candidates[:3])
        self.assertNotIn("models/layers/attention.py", repo_info.architecture_skeleton_candidates[:3])

    def test_ast_rerank_prefers_concrete_model_over_abstract_base(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_ast_concrete"
        repo = root / "repo"
        (repo / "models" / "vlms").mkdir(parents=True, exist_ok=True)
        (repo / "models" / "vlas").mkdir(parents=True, exist_ok=True)

        (repo / "models" / "vlms" / "base_vlm.py").write_text(
            "from abc import ABC, abstractmethod\n"
            "class VLM(ABC):\n"
            "    @abstractmethod\n"
            "    def forward(self):\n"
            "        raise NotImplementedError\n",
            encoding="utf-8",
        )
        (repo / "models" / "vlas" / "openvla.py").write_text(
            "from models.vlms.base_vlm import VLM\n"
            "class OpenVLA(VLM):\n"
            "    def predict_action(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        (repo / "train.py").write_text(
            "from models.vlas.openvla import OpenVLA\n"
            "model = OpenVLA()\n",
            encoding="utf-8",
        )

        repo_info = ingest_repo(str(repo), ["architecture", "model"])

        self.assertEqual(repo_info.architecture_entry_candidates[0], "models/vlas/openvla.py")
        self.assertIn("abstract_base", repo_info.ast_file_tags["models/vlms/base_vlm.py"])
        self.assertTrue(
            any("abstract_base_penalty" in reason for reason in repo_info.ast_candidate_reasons["models/vlms/base_vlm.py"])
        )

    def test_ast_rerank_prefers_top_level_arch_over_submodule_builder(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_ast_builder"
        repo = root / "repo"
        (repo / "recon" / "model" / "pixel_decoder").mkdir(parents=True, exist_ok=True)
        (repo / "recon" / "model" / "multimodal_encoder").mkdir(parents=True, exist_ok=True)

        (repo / "recon" / "model" / "recon_arch.py").write_text(
            "from recon.model.pixel_decoder.builder import build_pixel_decoder\n"
            "from recon.model.multimodal_encoder.builder import build_vision_tower\n"
            "class ReconMetaModel:\n"
            "    def forward(self):\n"
            "        return build_pixel_decoder(), build_vision_tower()\n",
            encoding="utf-8",
        )
        (repo / "recon" / "model" / "pixel_decoder" / "builder.py").write_text(
            "def build_pixel_decoder():\n"
            "    return None\n",
            encoding="utf-8",
        )
        (repo / "recon" / "model" / "multimodal_encoder" / "builder.py").write_text(
            "def build_vision_tower():\n"
            "    return None\n",
            encoding="utf-8",
        )
        (repo / "train_vla.py").write_text(
            "from recon.model.recon_arch import ReconMetaModel\n"
            "model = ReconMetaModel()\n",
            encoding="utf-8",
        )

        repo_info = ingest_repo(str(repo), ["architecture", "model"])

        self.assertEqual(repo_info.architecture_entry_candidates[0], "recon/model/recon_arch.py")
        self.assertTrue(
            any("submodule_builder_penalty" in reason for reason in repo_info.ast_candidate_reasons["recon/model/pixel_decoder/builder.py"])
        )

    def test_ast_parse_failure_does_not_break_ingest(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_ast_parse_failure"
        repo = root / "repo"
        (repo / "models").mkdir(parents=True, exist_ok=True)
        (repo / "models" / "broken_model.py").write_text("class Broken(\n", encoding="utf-8")
        (repo / "models" / "policy.py").write_text("class Policy:\n    pass\n", encoding="utf-8")

        repo_info = ingest_repo(str(repo), ["architecture"])

        self.assertIn("models/broken_model.py", repo_info.ast_file_tags)
        self.assertIn("ast_parse_failed", repo_info.ast_file_tags["models/broken_model.py"])

    def test_ast_rerank_lifts_acot_style_skeleton_and_filters_script_like_component_noise(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_ast_skeleton_component"
        repo = root / "repo"
        (repo / "src" / "openpi" / "models").mkdir(parents=True, exist_ok=True)
        (repo / "scripts").mkdir(parents=True, exist_ok=True)

        (repo / "src" / "openpi" / "models" / "acot_vla.py").write_text(
            "from openpi.models.model import BaseModel\n"
            "from openpi.models.pi0 import Pi0\n"
            "from openpi.models.vit import VisionTransformer\n"
            "class ACOTVLA(BaseModel):\n"
            "    def sample_actions(self):\n"
            "        return Pi0, VisionTransformer\n",
            encoding="utf-8",
        )
        (repo / "src" / "openpi" / "models" / "model.py").write_text(
            "import abc\n"
            "class BaseModel(abc.ABC):\n"
            "    def compute_loss(self):\n"
            "        return 0\n"
            "    def sample_actions(self):\n"
            "        return None\n",
            encoding="utf-8",
        )
        (repo / "src" / "openpi" / "models" / "pi0.py").write_text(
            "from openpi.models import model as _model\n"
            "import openpi.models.vit as vit\n"
            "class Pi0(_model.BaseModel):\n"
            "    def sample_actions(self):\n"
            "        return vit.VisionTransformer\n",
            encoding="utf-8",
        )
        (repo / "src" / "openpi" / "models" / "vit.py").write_text(
            "class Encoder:\n"
            "    pass\n"
            "class VisionTransformer:\n"
            "    pass\n",
            encoding="utf-8",
        )
        (repo / "src" / "openpi" / "models" / "projector.py").write_text(
            "class Projector:\n"
            "    pass\n",
            encoding="utf-8",
        )
        (repo / "scripts" / "compute_norm_stats.py").write_text(
            "import argparse\n"
            "def main():\n"
            "    parser = argparse.ArgumentParser()\n"
            "    return parser\n",
            encoding="utf-8",
        )

        repo_info = ingest_repo(str(repo), ["architecture", "model"])

        self.assertIn("src/openpi/models/model.py", repo_info.architecture_skeleton_candidates[:5])
        self.assertIn("src/openpi/models/pi0.py", repo_info.architecture_skeleton_candidates[:5])
        self.assertIn("src/openpi/models/vit.py", repo_info.architecture_skeleton_candidates[:5])
        self.assertIn("src/openpi/models/projector.py", repo_info.architecture_component_candidates[:5])
        self.assertNotIn("scripts/compute_norm_stats.py", repo_info.architecture_component_candidates[:5])
        self.assertIn("script_like", repo_info.ast_file_tags["scripts/compute_norm_stats.py"])
        self.assertTrue(
            any("script_penalty" in reason for reason in repo_info.ast_candidate_reasons["scripts/compute_norm_stats.py"])
        )

    def test_ast_root_reference_expands_flat_world_model_repo_candidates(self) -> None:
        root = Path.cwd() / ".tmp" / "test_repo_evidence_ast_root_reference"
        repo = root / "repo"
        repo.mkdir(parents=True, exist_ok=True)

        (repo / "jepa.py").write_text(
            "from torch import nn\n"
            "class JEPA(nn.Module):\n"
            "    def __init__(self, encoder, predictor):\n"
            "        super().__init__()\n"
            "        self.encoder = encoder\n"
            "        self.predictor = predictor\n"
            "    def encode(self, info):\n"
            "        return info\n"
            "    def predict(self, emb, act_emb):\n"
            "        return emb\n"
            "    def rollout(self, info, action_sequence):\n"
            "        return info\n"
            "    def get_cost(self, info_dict, action_candidates):\n"
            "        return action_candidates\n",
            encoding="utf-8",
        )
        (repo / "module.py").write_text(
            "from torch import nn\n"
            "class Transformer(nn.Module):\n"
            "    pass\n"
            "class Embedder(nn.Module):\n"
            "    pass\n"
            "class ARPredictor(nn.Module):\n"
            "    pass\n"
            "class Attention(nn.Module):\n"
            "    pass\n",
            encoding="utf-8",
        )
        (repo / "train.py").write_text(
            "from jepa import JEPA\n"
            "from module import ARPredictor, Embedder\n"
            "model = JEPA(Embedder(), ARPredictor())\n",
            encoding="utf-8",
        )
        (repo / "eval.py").write_text(
            "from jepa import JEPA\n"
            "def run(model: JEPA):\n"
            "    return model\n",
            encoding="utf-8",
        )

        repo_info = ingest_repo(str(repo), ["architecture", "model"])

        self.assertIn("jepa.py", repo_info.architecture_entry_candidates[:3])
        self.assertIn("module.py", repo_info.architecture_skeleton_candidates[:5])
        self.assertTrue(any("world_model_bonus" in reason for reason in repo_info.ast_candidate_reasons["jepa.py"]))


if __name__ == "__main__":
    unittest.main()
