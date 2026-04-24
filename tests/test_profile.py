from __future__ import annotations

import unittest

from study_agent.models import TasteProfile
from study_agent.profile import apply_feedback, apply_preset


class ProfileTests(unittest.TestCase):
    def test_apply_preset_code_first(self) -> None:
        profile = apply_preset(TasteProfile(), "concise-code-first")
        self.assertEqual(profile.verbosity, "low")
        self.assertIn("entrypoints", profile.focus_bias)

    def test_apply_feedback_sets_depth_for_shape(self) -> None:
        profile = apply_feedback(TasteProfile(), "请更详细展开 shape 和张量路径")
        self.assertEqual(profile.verbosity, "high")
        self.assertEqual(profile.depth_default, "module-function-shape")


if __name__ == "__main__":
    unittest.main()
