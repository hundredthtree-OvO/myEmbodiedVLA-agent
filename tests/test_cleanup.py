from __future__ import annotations

import unittest
from pathlib import Path

from study_agent.cleanup import cleanup_after_analyze, remove_pdf_cache, remove_temp_artifacts


class CleanupTests(unittest.TestCase):
    def test_remove_pdf_cache(self) -> None:
        cache = Path.cwd() / ".tmp" / "pdf-cache"
        cache.mkdir(parents=True, exist_ok=True)
        marker = cache / "marker.txt"
        marker.write_text("temporary", encoding="utf-8")

        removed = remove_pdf_cache()

        self.assertTrue(removed)
        self.assertFalse(cache.exists())

    def test_repo_cleanup_skips_local_repo_source(self) -> None:
        removed = cleanup_after_analyze("repo", ".")

        self.assertEqual(removed, [])

    def test_remove_temp_artifacts_cleans_test_dirs_but_keeps_shared_caches(self) -> None:
        tmp_root = Path.cwd() / ".tmp"
        test_dir = tmp_root / "test_cleanup_artifacts"
        repo_cache_test = tmp_root / "repo-cache-test"
        uv_cache = tmp_root / "uv-cache"
        repo_cache = tmp_root / "repo-cache"
        debug_output = tmp_root / "demo-study-agent.md"

        test_dir.mkdir(parents=True, exist_ok=True)
        repo_cache_test.mkdir(parents=True, exist_ok=True)
        uv_cache.mkdir(parents=True, exist_ok=True)
        repo_cache.mkdir(parents=True, exist_ok=True)
        debug_output.write_text("debug", encoding="utf-8")

        removed = remove_temp_artifacts()
        removed_paths = {path.name for path in removed}

        self.assertIn("test_cleanup_artifacts", removed_paths)
        self.assertIn("repo-cache-test", removed_paths)
        self.assertIn("demo-study-agent.md", removed_paths)
        self.assertFalse(test_dir.exists())
        self.assertFalse(repo_cache_test.exists())
        self.assertFalse(debug_output.exists())
        self.assertTrue(uv_cache.exists())
        self.assertTrue(repo_cache.exists())


if __name__ == "__main__":
    unittest.main()
