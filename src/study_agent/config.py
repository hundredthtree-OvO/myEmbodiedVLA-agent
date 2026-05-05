from __future__ import annotations

import json
import os
from dataclasses import replace
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import AgentConfig


CONFIG_PATH = Path(".study-agent") / "config.json"
AUTH_PATH_ENV_VARS = ("STUDY_AGENT_CODEX_AUTH_PATH", "CODEX_AUTH_PATH")
CODEX_HOME_ENV_VAR = "CODEX_HOME"
ZOTERO_DIR_ENV_VARS = ("STUDY_AGENT_ZOTERO_DATA_DIR", "ZOTERO_DATA_DIR")
DEFAULT_API_URL = "https://chatgpt.com/backend-api/codex/responses"
DEFAULT_MODEL = "gpt-5.5"
SUPPORTED_MODELS = ("gpt-5.4", "gpt-5.5")


def load_config(path: Path = CONFIG_PATH) -> AgentConfig:
    if not path.exists():
        config = AgentConfig(
            auth_path=resolve_auth_path(),
            api_url=DEFAULT_API_URL,
            model=DEFAULT_MODEL,
            zotero_data_dir=resolve_zotero_data_dir(),
        )
        save_config(config, path)
        return config

    data = json.loads(path.read_text(encoding="utf-8"))
    return AgentConfig(
        auth_path=resolve_auth_path(data.get("auth_path")),
        api_url=data.get("api_url", DEFAULT_API_URL),
        model=validate_model_name(data.get("model", DEFAULT_MODEL)),
        timeout_seconds=int(data.get("timeout_seconds", 300)),
        zotero_data_dir=resolve_zotero_data_dir(data.get("zotero_data_dir")),
    )


def save_config(config: AgentConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = asdict(config)
    for key, value in list(data.items()):
        if isinstance(value, Path):
            data[key] = str(value)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_auth_path(config_auth_path: str | Path | None = None) -> Path:
    env_override = _auth_path_from_env()
    if env_override is not None:
        return env_override
    if config_auth_path:
        return Path(config_auth_path)
    return default_auth_path()


def resolve_zotero_data_dir(config_zotero_data_dir: str | Path | None = None) -> Path:
    env_override = _zotero_dir_from_env()
    if env_override is not None:
        return env_override
    if config_zotero_data_dir:
        return Path(config_zotero_data_dir)
    return default_zotero_data_dir()


def default_auth_path() -> Path:
    codex_home = os.environ.get(CODEX_HOME_ENV_VAR, "").strip()
    if codex_home:
        return Path(codex_home) / "auth.json"
    return Path.home() / ".codex" / "auth.json"


def default_zotero_data_dir() -> Path:
    return Path.home() / "Zotero"


def _auth_path_from_env() -> Path | None:
    for name in AUTH_PATH_ENV_VARS:
        value = os.environ.get(name, "").strip()
        if value:
            return Path(value)
    return None


def _zotero_dir_from_env() -> Path | None:
    for name in ZOTERO_DIR_ENV_VARS:
        value = os.environ.get(name, "").strip()
        if value:
            return Path(value)
    return None


def validate_model_name(model: str) -> str:
    normalized = model.strip()
    if normalized not in SUPPORTED_MODELS:
        allowed = ", ".join(SUPPORTED_MODELS)
        raise ValueError(f"Unsupported model: {model}. Expected one of: {allowed}")
    return normalized


def with_model(config: AgentConfig, model: str | None) -> AgentConfig:
    if not model:
        return config
    return replace(config, model=validate_model_name(model))
