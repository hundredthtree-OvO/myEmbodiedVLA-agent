from __future__ import annotations

import io
import unittest

from study_agent.progress import TerminalProgress


class ProgressTests(unittest.TestCase):
    def test_terminal_progress_renders_stage_order(self) -> None:
        stream = io.StringIO()
        progress = TerminalProgress(stream=stream)

        progress.stage("Resolving inputs")
        progress.stage("Preparing repo", "demo")
        progress.output("hello")

        text = stream.getvalue()
        self.assertIn("[Resolving inputs]", text)
        self.assertIn("[Preparing repo] - demo", text)
        self.assertIn("--- assistant output ---", text)
        self.assertTrue(text.index("[Resolving inputs]") < text.index("[Preparing repo]"))


if __name__ == "__main__":
    unittest.main()
