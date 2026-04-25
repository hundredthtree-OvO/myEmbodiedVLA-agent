from __future__ import annotations

import unittest
from pathlib import Path

from study_agent.config import validate_model_name, with_model
from study_agent.models import AgentConfig


class ConfigTests(unittest.TestCase):
    def test_validate_model_name_accepts_supported_models(self) -> None:
        self.assertEqual(validate_model_name("gpt-5.4"), "gpt-5.4")
        self.assertEqual(validate_model_name("gpt-5.5"), "gpt-5.5")

    def test_validate_model_name_rejects_unknown_model(self) -> None:
        with self.assertRaises(ValueError):
            validate_model_name("gpt-4.1")

    def test_with_model_returns_updated_copy(self) -> None:
        config = AgentConfig(
            auth_path=Path("C:/Users/86157/.codex/auth.json"),
            api_url="https://chatgpt.com/backend-api/codex/responses",
            model="gpt-5.5",
            zotero_data_dir=Path("E:/zoteroData"),
        )

        updated = with_model(config, "gpt-5.4")

        self.assertEqual(updated.model, "gpt-5.4")
        self.assertEqual(config.model, "gpt-5.5")


if __name__ == "__main__":
    unittest.main()
