from __future__ import annotations

import unittest

from study_agent.codex_client import _consume_codex_stream, _extract_sse_output_text


class CodexClientTests(unittest.TestCase):
    def test_extract_sse_output_text_dedupes_final_text(self) -> None:
        body = (
            'data: {"type":"response.output_text.delta","delta":"OK"}\n\n'
            'data: {"type":"response.output_text.done","text":"OK"}\n\n'
            "data: [DONE]\n\n"
        )

        self.assertEqual(_extract_sse_output_text(body), "OK")

    def test_consume_codex_stream_emits_callback_chunks(self) -> None:
        events = [
            b'data: {"type":"response.output_text.delta","delta":"He"}\n',
            b"\n",
            b'data: {"type":"response.output_text.delta","delta":"llo"}\n',
            b"\n",
            b"data: [DONE]\n",
        ]
        seen: list[str] = []

        result = _consume_codex_stream(events, on_text=seen.append)

        self.assertEqual(result, "Hello")
        self.assertEqual(seen, ["He", "llo"])


if __name__ == "__main__":
    unittest.main()
