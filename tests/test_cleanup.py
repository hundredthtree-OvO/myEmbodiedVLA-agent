from __future__ import annotations

import unittest
from pathlib import Path

from study_agent.cleanup import cleanup_after_analyze, remove_pdf_cache


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


if __name__ == "__main__":
    unittest.main()
