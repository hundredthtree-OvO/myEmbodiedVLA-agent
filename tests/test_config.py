from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from study_agent.config import (
    default_auth_path,
    default_zotero_data_dir,
    load_config,
    validate_model_name,
    with_model,
)
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

    def test_load_config_prefers_env_auth_path_over_saved_path(self) -> None:
        config_path = Path.cwd() / ".tmp" / "test_config_env_override" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            '{\n'
            '  "auth_path": "C:/saved/.codex/auth.json",\n'
            '  "api_url": "https://chatgpt.com/backend-api/codex/responses",\n'
            '  "model": "gpt-5.5"\n'
            '}\n',
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"STUDY_AGENT_CODEX_AUTH_PATH": "D:/portable/codex/auth.json"}, clear=False):
            config = load_config(config_path)

        self.assertEqual(config.auth_path, Path("D:/portable/codex/auth.json"))

    def test_default_auth_path_falls_back_to_home_codex_auth(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with patch("study_agent.config.Path.home", return_value=Path("C:/Users/tester")):
                path = default_auth_path()

        self.assertEqual(path, Path("C:/Users/tester/.codex/auth.json"))

    def test_default_auth_path_uses_codex_home_when_present(self) -> None:
        with patch.dict("os.environ", {"CODEX_HOME": "D:/portable/.codex"}, clear=True):
            path = default_auth_path()

        self.assertEqual(path, Path("D:/portable/.codex/auth.json"))

    def test_default_zotero_data_dir_falls_back_to_home_zotero(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with patch("study_agent.config.Path.home", return_value=Path("C:/Users/tester")):
                path = default_zotero_data_dir()

        self.assertEqual(path, Path("C:/Users/tester/Zotero"))

    def test_load_config_prefers_env_zotero_dir_over_saved_path(self) -> None:
        config_path = Path.cwd() / ".tmp" / "test_config_zotero_override" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            '{\n'
            '  "zotero_data_dir": "C:/saved/Zotero",\n'
            '  "api_url": "https://chatgpt.com/backend-api/codex/responses",\n'
            '  "model": "gpt-5.5"\n'
            '}\n',
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"STUDY_AGENT_ZOTERO_DATA_DIR": "D:/portable/Zotero"}, clear=False):
            config = load_config(config_path)

        self.assertEqual(config.zotero_data_dir, Path("D:/portable/Zotero"))


if __name__ == "__main__":
    unittest.main()
