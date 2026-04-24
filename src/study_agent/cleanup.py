from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import urlparse


PDF_CACHE = Path(".tmp") / "pdf-cache"
REPO_CACHE = Path(".study-agent") / "repos"


def cleanup_after_analyze(mode: str, repo_source: str) -> list[Path]:
    removed: list[Path] = []
    if mode in {"temp", "all"}:
        removed.extend(remove_pdf_cache())
    if mode in {"repo", "all"}:
        removed.extend(remove_repo_cache_for_source(repo_source))
    return removed


def remove_pdf_cache() -> list[Path]:
    return _remove_if_safe(PDF_CACHE)


def remove_repo_cache_for_source(repo_source: str) -> list[Path]:
    parsed = urlparse(repo_source)
    if parsed.scheme not in {"http", "https"}:
        return []
    repo_name = Path(parsed.path).stem
    if not repo_name:
        return []
    return _remove_if_safe(REPO_CACHE / repo_name)


def remove_all_caches() -> list[Path]:
    removed: list[Path] = []
    removed.extend(_remove_if_safe(PDF_CACHE))
    removed.extend(_remove_if_safe(REPO_CACHE))
    return removed


def _remove_if_safe(path: Path) -> list[Path]:
    root = Path.cwd().resolve()
    target = path.resolve()
    if not _is_within(target, root):
        raise RuntimeError(f"Refusing to remove path outside workspace: {target}")
    if not target.exists():
        return []
    shutil.rmtree(target)
    return [target]


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
