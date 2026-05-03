from __future__ import annotations

import unittest
from study_agent.paper import select_key_figure_pages


class PdfTests(unittest.TestCase):
    def test_select_key_figure_pages_scores_figure_and_focus_pages(self) -> None:
        pages = [
            "Introduction page",
            "Figure 5. Bridge Attention architecture overview with action query and KV.",
            "Appendix page",
        ]

        selected = select_key_figure_pages(pages, ["bridge_attention"])

        self.assertEqual(selected[0], 2)

    def test_select_key_figure_pages_falls_back_to_early_pages(self) -> None:
        pages = ["", "", "", "", ""]

        selected = select_key_figure_pages(pages, ["nonexistent"], max_pages=3)

        self.assertEqual(selected, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
