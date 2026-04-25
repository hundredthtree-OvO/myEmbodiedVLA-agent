from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from study_agent.runtime_env import configure_runtime_environment


class RuntimeEnvTests(unittest.TestCase):
    def test_configure_runtime_environment_sets_workspace_uv_cache(self) -> None:
        root = Path.cwd()
        with mock.patch.dict(os.environ, {}, clear=True):
            env = configure_runtime_environment(root)
            self.assertEqual(os.environ["UV_CACHE_DIR"], str(root / ".tmp" / "uv-cache"))

        self.assertEqual(env.uv_cache_dir, root / ".tmp" / "uv-cache")
        self.assertTrue(env.uv_cache_was_auto_set)


if __name__ == "__main__":
    unittest.main()
