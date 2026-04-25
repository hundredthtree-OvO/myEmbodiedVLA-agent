from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import EvidencePack


SESSION_ROOT = Path(".study-agent") / "sessions"


def create_session_dir(root: Path = SESSION_ROOT) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = root / stamp
    counter = 1
    while path.exists():
        path = root / f"{stamp}-{counter}"
        counter += 1
    path.mkdir()
    return path


def latest_session_dir(root: Path = SESSION_ROOT) -> Path | None:
    if not root.exists():
        return None
    candidates = sorted((path for path in root.iterdir() if path.is_dir()), key=lambda item: item.name, reverse=True)
    return candidates[0] if candidates else None


def save_session(session_dir: Path, evidence: EvidencePack, prompt: str, output: str, taste_delta: str = "") -> None:
    (session_dir / "request.json").write_text(
        json.dumps(_safe_asdict(evidence.request), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (session_dir / "evidence.md").write_text(prompt, encoding="utf-8")
    (session_dir / "output.md").write_text(output, encoding="utf-8")
    if taste_delta:
        (session_dir / "taste_delta.md").write_text(taste_delta, encoding="utf-8")


def _safe_asdict(obj):
    data = asdict(obj)
    for key, value in list(data.items()):
        if isinstance(value, Path):
            data[key] = str(value)
    return data
