from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from study_agent.github_check import check_github_clone


class GitHubCheckTests(unittest.TestCase):
    def test_check_github_clone_success_cleans_probe_directory(self) -> None:
        workspace = Path.cwd()

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            if command[:4] == ["git", "config", "--global", "--get"]:
                return subprocess.CompletedProcess(command, 1, "", "")
            if command[:4] == ["git", "clone", "--depth", "1"]:
                Path(command[-1]).mkdir(parents=True, exist_ok=True)
                return subprocess.CompletedProcess(command, 0, "", "Cloning into 'probe'...")
            raise AssertionError(f"Unexpected command: {command}")

        with mock.patch("study_agent.github_check.PROBE_ROOT", Path(".tmp") / "github-clone-check-tests"):
            with mock.patch("study_agent.github_check.subprocess.run", side_effect=fake_run):
                result = check_github_clone("https://github.com/example/repo.git", workspace)

        self.assertTrue(result.success)
        self.assertTrue(result.cleanup_ok)
        self.assertFalse(result.probe_path.exists())
        self.assertIn("Result      : OK", result.summary)
        self.assertIn("Cleanup     : OK", result.summary)

    def test_check_github_clone_failure_reports_proxy_and_reason(self) -> None:
        workspace = Path.cwd()

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            if command == ["git", "config", "--global", "--get", "http.proxy"]:
                return subprocess.CompletedProcess(command, 0, "http://127.0.0.1:7890\n", "")
            if command == ["git", "config", "--global", "--get", "https.proxy"]:
                return subprocess.CompletedProcess(command, 0, "http://127.0.0.1:7890\n", "")
            if command[:4] == ["git", "clone", "--depth", "1"]:
                return subprocess.CompletedProcess(
                    command,
                    128,
                    "",
                    "Failed to connect to github.com port 443 via 127.0.0.1",
                )
            raise AssertionError(f"Unexpected command: {command}")

        env = {"HTTP_PROXY": "", "HTTPS_PROXY": ""}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("study_agent.github_check.PROBE_ROOT", Path(".tmp") / "github-clone-check-tests"):
                with mock.patch("study_agent.github_check.subprocess.run", side_effect=fake_run):
                    result = check_github_clone("https://github.com/example/repo.git", workspace)

        self.assertFalse(result.success)
        self.assertTrue(result.cleanup_ok)
        self.assertIn("git http    : http://127.0.0.1:7890", result.summary)
        self.assertIn("Result      : FAILED", result.summary)
        self.assertIn("Failed to connect to github.com port 443", result.summary)


if __name__ == "__main__":
    unittest.main()
