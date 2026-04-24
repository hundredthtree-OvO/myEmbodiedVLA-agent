from __future__ import annotations

import unittest

from study_agent.codex_client import _extract_sse_output_text


class CodexClientTests(unittest.TestCase):
    def test_extract_sse_output_text_dedupes_final_text(self) -> None:
        body = (
            'data: {"type":"response.output_text.delta","delta":"OK"}\n\n'
            'data: {"type":"response.output_text.done","text":"OK"}\n\n'
            "data: [DONE]\n\n"
        )

        self.assertEqual(_extract_sse_output_text(body), "OK")


if __name__ == "__main__":
    unittest.main()
