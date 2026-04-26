from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import EvidencePack, SecondPassEvidence


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


def save_session(
    session_dir: Path,
    evidence: EvidencePack,
    prompt: str,
    output: str,
    taste_delta: str = "",
    second_pass: SecondPassEvidence | None = None,
    second_pass_round1_raw: str = "",
    second_pass_round2_raw: str = "",
) -> None:
    (session_dir / "request.json").write_text(
        json.dumps(_safe_asdict(evidence.request), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (session_dir / "evidence.md").write_text(prompt, encoding="utf-8")
    (session_dir / "output.md").write_text(output, encoding="utf-8")
    if taste_delta:
        (session_dir / "taste_delta.md").write_text(taste_delta, encoding="utf-8")
    if second_pass:
        (session_dir / "second-pass-round-1.json").write_text(
            json.dumps(_safe_asdict(second_pass.round_1), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if second_pass_round1_raw:
            (session_dir / "second-pass-round-1.md").write_text(second_pass_round1_raw, encoding="utf-8")
        if second_pass.round_2:
            (session_dir / "second-pass-round-2.json").write_text(
                json.dumps(_safe_asdict(second_pass.round_2), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            if second_pass_round2_raw:
                (session_dir / "second-pass-round-2.md").write_text(second_pass_round2_raw, encoding="utf-8")
        (session_dir / "concept2code.json").write_text(
            json.dumps(_safe_asdict(second_pass.final_concept2code_links), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _safe_asdict(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, list):
        return [_safe_asdict(item) for item in obj]
    if isinstance(obj, tuple):
        return [_safe_asdict(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _safe_asdict(value) for key, value in obj.items()}
    try:
        data = asdict(obj)
    except TypeError:
        return obj
    for key, value in list(data.items()):
        data[key] = _safe_asdict(value)
    return data
