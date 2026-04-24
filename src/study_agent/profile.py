from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import TasteProfile


PROFILE_PATH = Path(".study-agent") / "profile.json"

PRESETS: dict[str, dict[str, Any]] = {
    "default": {},
    "concise-code-first": {
        "verbosity": "low",
        "reading_order_style": "entrypoint-first",
        "depth_default": "module-function",
        "focus_bias": ["entrypoints", "call-chain", "config-switches"],
    },
    "paper-first": {
        "verbosity": "medium",
        "reading_order_style": "concept-first",
        "focus_bias": ["concepts", "architecture", "paper-figures"],
    },
}


def load_profile(path: Path = PROFILE_PATH) -> TasteProfile:
    if not path.exists():
        profile = TasteProfile()
        save_profile(profile, path)
        return profile

    data = json.loads(path.read_text(encoding="utf-8"))
    return TasteProfile(**data)


def save_profile(profile: TasteProfile, path: Path = PROFILE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(profile), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def apply_preset(profile: TasteProfile, preset: str) -> TasteProfile:
    if preset not in PRESETS:
        known = ", ".join(sorted(PRESETS))
        raise ValueError(f"Unknown preset '{preset}'. Known presets: {known}")
    data = asdict(profile)
    data.update(PRESETS[preset])
    return TasteProfile(**data)


def apply_feedback(profile: TasteProfile, note: str) -> TasteProfile:
    data = asdict(profile)
    text = note.lower()

    if any(token in text for token in ["code-first", "代码优先", "更重视代码", "多讲实现"]):
        data["reading_order_style"] = "entrypoint-first"
        data["focus_bias"] = sorted(set(data["focus_bias"] + ["entrypoints", "call-chain"]))

    if any(token in text for token in ["paper-first", "论文优先", "多讲概念", "背景"]):
        data["reading_order_style"] = "concept-first"
        data["focus_bias"] = sorted(set(data["focus_bias"] + ["concepts", "architecture"]))

    if any(token in text for token in ["少讲", "concise", "简洁"]):
        data["verbosity"] = "low"

    if any(token in text for token in ["详细", "deep", "展开", "shape", "张量"]):
        data["verbosity"] = "high"
        data["depth_default"] = "module-function-shape"

    if any(token in text for token in ["不确定", "证据", "confirmed", "inferred"]):
        data["evidence_style"] = "CONFIRMED/INFERRED"

    return TasteProfile(**data)
