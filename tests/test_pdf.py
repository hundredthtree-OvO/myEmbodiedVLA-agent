from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from study_agent.pdf import _bundled_python


class PdfTests(unittest.TestCase):
    def test_bundled_python_prefers_env_override(self) -> None:
        with patch.dict("os.environ", {"STUDY_AGENT_PDF_PYTHON": "D:/runtime/python.exe"}, clear=False):
            with patch("study_agent.pdf.Path.exists", return_value=True):
                python = _bundled_python()

        self.assertEqual(python, Path("D:/runtime/python.exe"))


if __name__ == "__main__":
    unittest.main()
