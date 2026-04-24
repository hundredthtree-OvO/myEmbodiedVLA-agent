from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import AgentConfig


CONFIG_PATH = Path(".study-agent") / "config.json"
DEFAULT_AUTH_PATH = Path("C:/Users/86157/.codex/auth.json")
DEFAULT_API_URL = "https://chatgpt.com/backend-api/codex/responses"
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_ZOTERO_DIR = Path("E:/zoteroData")


def load_config(path: Path = CONFIG_PATH) -> AgentConfig:
    if not path.exists():
        config = AgentConfig(
            auth_path=DEFAULT_AUTH_PATH,
            api_url=DEFAULT_API_URL,
            model=DEFAULT_MODEL,
            zotero_data_dir=DEFAULT_ZOTERO_DIR,
        )
        save_config(config, path)
        return config

    data = json.loads(path.read_text(encoding="utf-8"))
    return AgentConfig(
        auth_path=Path(data.get("auth_path", DEFAULT_AUTH_PATH)),
        api_url=data.get("api_url", DEFAULT_API_URL),
        model=data.get("model", DEFAULT_MODEL),
        timeout_seconds=int(data.get("timeout_seconds", 300)),
        max_evidence_chars=int(data.get("max_evidence_chars", 60000)),
        max_history_examples=int(data.get("max_history_examples", 3)),
        zotero_data_dir=Path(data["zotero_data_dir"]) if data.get("zotero_data_dir") else DEFAULT_ZOTERO_DIR,
    )


def save_config(config: AgentConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = asdict(config)
    for key, value in list(data.items()):
        if isinstance(value, Path):
            data[key] = str(value)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
