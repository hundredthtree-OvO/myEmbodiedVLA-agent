from __future__ import annotations

import unittest
from unittest import mock

from study_agent.tui import cleanup_choices, default_form_values, next_step, _fixed_output_path


class TuiTests(unittest.TestCase):
    def test_default_form_values_are_clean_defaults(self) -> None:
        with mock.patch("study_agent.tui.load_config") as mock_load_config:
            mock_load_config.return_value.model = "gpt-5.5"
            defaults = default_form_values()

        self.assertEqual(defaults.paper, "")
        self.assertEqual(defaults.zotero_title, "")
        self.assertEqual(defaults.focus, "")
        self.assertEqual(defaults.repo, ".")
        self.assertEqual(defaults.model, "gpt-5.5")
        self.assertEqual(defaults.mode, "paper-aligned")
        self.assertEqual(defaults.engine, "codex")

    def test_cleanup_choices_and_step_switching(self) -> None:
        self.assertEqual(cleanup_choices(), ["none", "temp", "repo", "all"])
        self.assertEqual(next_step("input"), "repo")
        self.assertEqual(next_step("focus"), "cleanup")
        self.assertEqual(next_step("cleanup"), "run")

    def test_fixed_output_path_uses_result_workspace(self) -> None:
        path = _fixed_output_path(r"E:\papers\VLA-Adapter.pdf", "")
        self.assertEqual(path, "result/vla-adapter/outputs/study-note.md")


if __name__ == "__main__":
    unittest.main()
