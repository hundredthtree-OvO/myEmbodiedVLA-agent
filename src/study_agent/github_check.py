from __future__ import annotations

import os
import shutil
import stat
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


DEFAULT_REPO_URL = "https://github.com/Win-commit/WAV"
PROBE_ROOT = Path(".tmp") / "github-clone-check"


@dataclass(frozen=True)
class GitHubCheckResult:
    repo_url: str
    probe_path: Path
    http_proxy: str
    https_proxy: str
    env_http_proxy: str
    env_https_proxy: str
    success: bool
    cleanup_ok: bool
    cleanup_error: str
    summary: str


def check_github_clone(
    repo_url: str = DEFAULT_REPO_URL,
    workspace_root: Path | None = None,
) -> GitHubCheckResult:
    workspace = (workspace_root or Path.cwd()).resolve()
    probe_root = (workspace / PROBE_ROOT).resolve()
    probe_root.mkdir(parents=True, exist_ok=True)
    probe_path = probe_root / f"{_repo_slug(repo_url)}-{uuid.uuid4().hex[:8]}"

    http_proxy = _git_config_value("http.proxy")
    https_proxy = _git_config_value("https.proxy")
    env_http_proxy = os.environ.get("HTTP_PROXY", "")
    env_https_proxy = os.environ.get("HTTPS_PROXY", "")

    success = False
    stdout = ""
    stderr = ""
    cleanup_ok = True
    cleanup_error = ""

    try:
        completed = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(probe_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        success = completed.returncode == 0
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        stderr = f"git clone timed out after {exc.timeout} seconds."
    except FileNotFoundError:
        stderr = "git executable was not found on PATH."
    finally:
        try:
            cleanup_ok = _cleanup_probe_path(probe_path, workspace)
        except OSError as exc:
            cleanup_ok = False
            cleanup_error = str(exc)
        try:
            _cleanup_probe_root(probe_root, workspace)
        except OSError as exc:
            cleanup_ok = False
            cleanup_error = cleanup_error or str(exc)

    summary = _build_summary(
        repo_url=repo_url,
        probe_path=probe_path,
        http_proxy=http_proxy,
        https_proxy=https_proxy,
        env_http_proxy=env_http_proxy,
        env_https_proxy=env_https_proxy,
        success=success,
        cleanup_ok=cleanup_ok,
        cleanup_error=cleanup_error,
        stdout=stdout,
        stderr=stderr,
    )
    return GitHubCheckResult(
        repo_url=repo_url,
        probe_path=probe_path,
        http_proxy=http_proxy,
        https_proxy=https_proxy,
        env_http_proxy=env_http_proxy,
        env_https_proxy=env_https_proxy,
        success=success,
        cleanup_ok=cleanup_ok,
        cleanup_error=cleanup_error,
        summary=summary,
    )


def _git_config_value(key: str) -> str:
    completed = subprocess.run(
        ["git", "config", "--global", "--get", key],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _repo_slug(repo_url: str) -> str:
    slug = repo_url.rstrip("/").rsplit("/", 1)[-1]
    slug = slug.removesuffix(".git")
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in slug.lower())
    return safe.strip("-") or "github-probe"


def _cleanup_probe_path(probe_path: Path, workspace: Path) -> bool:
    if not probe_path.exists():
        return True
    if not _is_within(probe_path.resolve(), workspace):
        raise RuntimeError(f"Refusing to remove probe path outside workspace: {probe_path}")
    _remove_tree_with_retries(probe_path)
    return not probe_path.exists()


def _cleanup_probe_root(probe_root: Path, workspace: Path) -> None:
    if not probe_root.exists():
        return
    if not _is_within(probe_root.resolve(), workspace):
        raise RuntimeError(f"Refusing to remove probe root outside workspace: {probe_root}")
    try:
        probe_root.rmdir()
    except OSError:
        return


def _remove_tree_with_retries(path: Path, attempts: int = 6, delay_seconds: float = 0.25) -> None:
    last_error: OSError | None = None
    for attempt in range(attempts):
        _make_tree_writable(path)
        try:
            shutil.rmtree(path, onerror=_handle_remove_error)
            return
        except OSError as exc:
            last_error = exc
            if attempt + 1 == attempts:
                break
            time.sleep(delay_seconds * (attempt + 1))
    if last_error is not None:
        raise last_error


def _make_tree_writable(path: Path) -> None:
    if not path.exists():
        return
    for current in [path, *path.rglob("*")]:
        try:
            os.chmod(current, stat.S_IWRITE | stat.S_IREAD)
        except OSError:
            continue


def _handle_remove_error(function, target: str, excinfo) -> None:
    del excinfo
    os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
    function(target)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _build_summary(
    repo_url: str,
    probe_path: Path,
    http_proxy: str,
    https_proxy: str,
    env_http_proxy: str,
    env_https_proxy: str,
    success: bool,
    cleanup_ok: bool,
    cleanup_error: str,
    stdout: str,
    stderr: str,
) -> str:
    lines = [
        f"Repo URL    : {repo_url}",
        f"Probe path  : {probe_path}",
        f"git http    : {http_proxy or '(unset)'}",
        f"git https   : {https_proxy or '(unset)'}",
        f"env HTTP    : {env_http_proxy or '(unset)'}",
        f"env HTTPS   : {env_https_proxy or '(unset)'}",
    ]
    if success:
        preview = (stderr.strip().splitlines() or stdout.strip().splitlines() or ["git clone succeeded"])[0]
        lines.append("Result      : OK")
        lines.append(f"Clone says  : {preview}")
    else:
        reason = (stderr.strip() or stdout.strip() or "Unknown git clone failure.")[-600:]
        lines.append("Result      : FAILED")
        lines.append(f"Reason      : {reason}")
    lines.append(f"Cleanup     : {'OK' if cleanup_ok else 'FAILED'}")
    if cleanup_error:
        lines.append(f"Cleanup why : {cleanup_error[-300:]}")
    return "\n".join(lines)
