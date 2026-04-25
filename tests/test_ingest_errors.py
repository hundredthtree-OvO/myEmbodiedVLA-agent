from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from study_agent.ingest import RepositoryPrepareError, ingest_repo


class IngestErrorTests(unittest.TestCase):
    def test_remote_clone_failure_suggests_local_repo_and_reports_proxy(self) -> None:
        cache_dir = Path(".tmp") / "repo-cache-test"

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            if command == ["git", "config", "--global", "--get", "http.proxy"]:
                return subprocess.CompletedProcess(command, 0, "http://127.0.0.1:7890\n", "")
            if command == ["git", "config", "--global", "--get", "https.proxy"]:
                return subprocess.CompletedProcess(command, 0, "http://127.0.0.1:7890\n", "")
            if command[:4] == ["git", "clone", "--depth", "1"]:
                Path(command[-1]).mkdir(parents=True, exist_ok=True)
                return subprocess.CompletedProcess(command, 128, "", "Failed to connect to github.com port 443")
            raise AssertionError(f"Unexpected command: {command}")

        with mock.patch("study_agent.ingest.shutil.which", return_value="git"):
            with mock.patch.dict(os.environ, {"HTTP_PROXY": "", "HTTPS_PROXY": ""}, clear=False):
                with mock.patch("study_agent.ingest.subprocess.run", side_effect=fake_run):
                    with self.assertRaises(RepositoryPrepareError) as ctx:
                        ingest_repo("https://github.com/example/repo.git", ["world_model"], cache_dir)

        message = str(ctx.exception)
        self.assertIn("If you already cloned the repo locally", message)
        self.assertIn("git http.proxy=http://127.0.0.1:7890", message)
        self.assertIn("Failed to connect to github.com port 443", message)
        self.assertFalse((cache_dir / "repo").exists())

    def test_missing_local_repo_path_has_local_hint(self) -> None:
        with self.assertRaises(RepositoryPrepareError) as ctx:
            ingest_repo("E:/missing/repo", ["bridge_attention"], Path(".tmp") / "repo-cache")

        self.assertIn("Repository path does not exist", str(ctx.exception))
        self.assertIn("--repo E:\\path\\to\\repo", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
