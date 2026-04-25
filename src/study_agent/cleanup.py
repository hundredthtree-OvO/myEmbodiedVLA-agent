from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import urlparse


TMP_ROOT = Path(".tmp")
PDF_CACHE = Path(".tmp") / "pdf-cache"
REPO_CACHE = Path(".study-agent") / "repos"
TMP_TEST_CACHE_NAMES = ("repo-cache-test",)
TMP_DEBUG_OUTPUT_NAMES = ("demo-study-agent.md", "WAV-local-codex.md", "wav-offline.md")


def cleanup_after_analyze(mode: str, repo_source: str) -> list[Path]:
    removed: list[Path] = []
    if mode in {"temp", "all"}:
        removed.extend(remove_temp_artifacts())
    if mode in {"repo", "all"}:
        removed.extend(remove_repo_cache_for_source(repo_source))
    return removed


def remove_temp_artifacts() -> list[Path]:
    removed: list[Path] = []
    removed.extend(remove_pdf_cache())
    removed.extend(remove_tmp_test_artifacts())
    removed.extend(remove_tmp_debug_outputs())
    return removed


def remove_pdf_cache() -> list[Path]:
    return _remove_tree_if_safe(PDF_CACHE)


def remove_tmp_test_artifacts() -> list[Path]:
    removed: list[Path] = []
    for path in sorted(TMP_ROOT.glob("test_*")):
        if path.is_dir():
            removed.extend(_remove_tree_if_safe(path))
    for name in TMP_TEST_CACHE_NAMES:
        removed.extend(_remove_tree_if_safe(TMP_ROOT / name))
    return removed


def remove_tmp_debug_outputs() -> list[Path]:
    removed: list[Path] = []
    for name in TMP_DEBUG_OUTPUT_NAMES:
        removed.extend(_remove_path_if_safe(TMP_ROOT / name))
    return removed


def remove_repo_cache_for_source(repo_source: str) -> list[Path]:
    parsed = urlparse(repo_source)
    if parsed.scheme not in {"http", "https"}:
        return []
    repo_name = Path(parsed.path).stem
    if not repo_name:
        return []
    return _remove_tree_if_safe(REPO_CACHE / repo_name)


def remove_all_caches() -> list[Path]:
    removed: list[Path] = []
    removed.extend(remove_temp_artifacts())
    removed.extend(_remove_tree_if_safe(REPO_CACHE))
    return removed


def _remove_tree_if_safe(path: Path) -> list[Path]:
    root = Path.cwd().resolve()
    target = path.resolve()
    if not _is_within(target, root):
        raise RuntimeError(f"Refusing to remove path outside workspace: {target}")
    if not target.exists():
        return []
    shutil.rmtree(target)
    return [target]


def _remove_path_if_safe(path: Path) -> list[Path]:
    root = Path.cwd().resolve()
    target = path.resolve()
    if not _is_within(target, root):
        raise RuntimeError(f"Refusing to remove path outside workspace: {target}")
    if not target.exists():
        return []
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return [target]


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
