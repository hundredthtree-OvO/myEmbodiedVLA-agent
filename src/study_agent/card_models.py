from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CardArtifact:
    card_id: str
    card_type: str
    title: str
    topic: str
    markdown: str
    source_session_id: str = ""
