from __future__ import annotations

from datetime import datetime
from pathlib import Path


MEMORY_PATH = Path(".study-agent") / "taste_memory.md"


def read_taste_memory(path: Path = MEMORY_PATH) -> str:
    if not path.exists():
        return "No taste memory yet."
    return path.read_text(encoding="utf-8", errors="replace")[-12000:]


def append_taste_memory(text: str, path: Path = MEMORY_PATH) -> None:
    if not text.strip():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {stamp}\n\n{text.strip()}\n")
