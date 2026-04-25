from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeEnvironment:
    workspace_root: Path
    uv_cache_dir: Path
    pythonpath: str
    uv_cache_was_auto_set: bool
    pythonpath_was_auto_set: bool


def configure_runtime_environment(workspace_root: Path | None = None) -> RuntimeEnvironment:
    root = (workspace_root or Path.cwd()).resolve()
    uv_cache_dir = root / ".tmp" / "uv-cache"
    src_dir = root / "src"

    uv_cache_was_auto_set = False
    if not os.environ.get("UV_CACHE_DIR"):
        os.environ["UV_CACHE_DIR"] = str(uv_cache_dir)
        uv_cache_was_auto_set = True
    uv_cache_dir.mkdir(parents=True, exist_ok=True)

    pythonpath_was_auto_set = False
    if not os.environ.get("PYTHONPATH"):
        os.environ["PYTHONPATH"] = str(src_dir)
        pythonpath_was_auto_set = True

    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    return RuntimeEnvironment(
        workspace_root=root,
        uv_cache_dir=uv_cache_dir,
        pythonpath=os.environ["PYTHONPATH"],
        uv_cache_was_auto_set=uv_cache_was_auto_set,
        pythonpath_was_auto_set=pythonpath_was_auto_set,
    )
