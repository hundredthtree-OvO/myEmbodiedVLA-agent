from __future__ import annotations

import unittest
from pathlib import Path

from study_agent.ingest import ingest_repo


class AstRegressionTests(unittest.TestCase):
    def test_reconvla_architecture_entry_regression(self) -> None:
        repo = Path("E:/my-embodied/.study-agent/repos/ReconVLA")
        if not repo.exists():
            self.skipTest("ReconVLA repo is not available locally.")

        repo_info = ingest_repo(str(repo), ["architecture", "model"])

        self.assertIn("reconvla/recon/model/recon_arch.py", repo_info.architecture_entry_candidates[:5])
        self.assertIn("reconvla/recon/model/language_model/recon_qwen.py", repo_info.architecture_entry_candidates[:5])
        self.assertNotIn("reconvla/recon/model/pixel_decoder/builder.py", repo_info.architecture_entry_candidates[:8])

    def test_vla_adapter_architecture_entry_regression(self) -> None:
        repo = Path("E:/my-embodied/.study-agent/repos/VLA-Adapter")
        if not repo.exists():
            self.skipTest("VLA-Adapter repo is not available locally.")

        repo_info = ingest_repo(str(repo), ["architecture", "model"])

        self.assertIn("prismatic/models/vlas/openvla.py", repo_info.architecture_entry_candidates[:4])
        self.assertIn("prismatic/models/vlms/prismatic.py", repo_info.architecture_entry_candidates[:4])
        self.assertNotIn("prismatic/models/vlms/base_vlm.py", repo_info.architecture_entry_candidates[:8])
        self.assertIn("action_head_like", repo_info.ast_file_tags.get("prismatic/models/action_heads.py", []))
        self.assertIn("projector_like", repo_info.ast_file_tags.get("prismatic/models/projectors.py", []))

    def test_lewm_flat_world_model_regression(self) -> None:
        repo = Path("E:/my-embodied/.study-agent/repos/le-wm")
        if not repo.exists():
            self.skipTest("le-wm repo is not available locally.")

        repo_info = ingest_repo(str(repo), ["architecture", "model"])

        self.assertIn("jepa.py", repo_info.architecture_entry_candidates[:5])
        self.assertIn("module.py", repo_info.architecture_skeleton_candidates[:5])
        self.assertNotIn("train.py", repo_info.architecture_entry_candidates[:5])


if __name__ == "__main__":
    unittest.main()
