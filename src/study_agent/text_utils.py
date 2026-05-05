from __future__ import annotations

import re


def sentence_with_term(text: str, term: str) -> str | None:
    if not text or not term:
        return None
    pattern = re.compile(r"([^。.!?\n]*" + re.escape(term) + r"[^。.!?\n]*[。.!?]?)", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()[:500]
