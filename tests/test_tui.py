from __future__ import annotations

import unittest

from study_agent.tui import cleanup_choices, default_form_values, next_step


class TuiTests(unittest.TestCase):
    def test_default_form_values_prefill_last_request(self) -> None:
        defaults = default_form_values(
            {
                "paper_source": "paper.pdf",
                "zotero_title": "Demo Paper",
                "repo_source": ".",
                "focus": ["EAR", "IAR"],
                "output_path": "notes/demo.md",
                "mode": "paper-aligned",
                "engine": "codex",
            }
        )

        self.assertEqual(defaults.paper, "paper.pdf")
        self.assertEqual(defaults.zotero_title, "Demo Paper")
        self.assertEqual(defaults.focus, "EAR,IAR")
        self.assertEqual(defaults.out, "notes/demo.md")

    def test_cleanup_choices_and_step_switching(self) -> None:
        self.assertEqual(cleanup_choices(), ["none", "temp", "repo", "all"])
        self.assertEqual(next_step("input"), "repo")
        self.assertEqual(next_step("cleanup"), "run")


if __name__ == "__main__":
    unittest.main()
