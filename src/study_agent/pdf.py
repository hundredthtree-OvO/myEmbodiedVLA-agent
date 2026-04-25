from __future__ import annotations

import hashlib
import os
import sys
import shutil
import subprocess
from pathlib import Path


PDF_PYTHON_ENV_VARS = ("STUDY_AGENT_PDF_PYTHON", "STUDY_AGENT_BUNDLED_PYTHON")


def extract_pdf_text(path: Path, timeout_seconds: int = 120) -> str:
    if not path.exists():
        raise FileNotFoundError(f"PDF does not exist: {path}")

    try:
        return _run_local_pypdf(path)
    except ImportError:
        pass

    bundled = _bundled_python()
    if bundled:
        try:
            return _run_bundled_pypdf(bundled, path, timeout_seconds)
        except subprocess.CalledProcessError:
            pass

    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        try:
            return _run_pdftotext(pdftotext, path, timeout_seconds)
        except subprocess.CalledProcessError:
            safe_path = _ascii_pdf_copy(path)
            return _run_pdftotext(pdftotext, safe_path, timeout_seconds)

    raise RuntimeError("No PDF extractor found. Install pypdf or ensure pdftotext is on PATH.")


def _run_local_pypdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _bundled_python() -> Path | None:
    env_candidate = _bundled_python_from_env()
    candidates = [
        candidate
        for candidate in (
            env_candidate,
            Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "python.exe",
        )
        if candidate is not None
    ]
    for candidate in candidates:
        if candidate.exists() and candidate != Path(sys.executable):
            return candidate
    return None


def _bundled_python_from_env() -> Path | None:
    for name in PDF_PYTHON_ENV_VARS:
        value = os.environ.get(name, "").strip()
        if value:
            return Path(value)
    return None


def _run_bundled_pypdf(python: Path, path: Path, timeout_seconds: int) -> str:
    code = (
        "from pypdf import PdfReader\n"
        "import sys\n"
        "reader = PdfReader(sys.argv[1])\n"
        "print('\\n\\n'.join(page.extract_text() or '' for page in reader.pages))\n"
    )
    completed = subprocess.run(
        [str(python), "-c", code, str(path)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return completed.stdout


def _run_pdftotext(pdftotext: str, path: Path, timeout_seconds: int) -> str:
    completed = subprocess.run(
        [pdftotext, "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )
    return completed.stdout


def _ascii_pdf_copy(path: Path) -> Path:
    cache_dir = Path(".tmp") / "pdf-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
    target = cache_dir / f"{digest}.pdf"
    if not target.exists():
        shutil.copy2(path, target)
    return target


def focus_excerpt(text: str, focus_terms: list[str], max_chars: int = 14000) -> str:
    if not text:
        return ""
    lowered = text.lower()
    positions: list[int] = []
    for term in focus_terms:
        idx = lowered.find(term.lower())
        if idx >= 0:
            positions.append(idx)

    if not positions:
        keyword_positions = [lowered.find(term) for term in ["latent", "planning", "inference"]]
        positions = [idx for idx in keyword_positions if idx >= 0]

    if not positions:
        return text[:max_chars]

    center = min(positions)
    start = max(0, center - max_chars // 3)
    end = min(len(text), start + max_chars)
    return text[start:end]
