from __future__ import annotations

import re
import shutil
import subprocess
import os
from pathlib import Path
from urllib.parse import urlparse

from .models import CodeHit, CodeSymbol, PaperInfo, PaperSection, RepoInfo
from .pdf import extract_pdf_text


TEXT_SUFFIXES = {".md", ".txt", ".tex", ".rst"}
CODE_SUFFIXES = {".py", ".ipynb", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".cc", ".h", ".hpp", ".rs"}
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache", "dist", "build"}
TRAIN_NAMES = {"train", "fit", "compute_loss", "loss", "training_step"}
INFER_NAMES = {"sample", "sample_actions", "predict", "predict_action", "forward", "evaluate", "eval", "inference"}


class RepositoryPrepareError(RuntimeError):
    pass


def ingest_paper(source: str) -> PaperInfo:
    path = Path(source)
    if path.exists() and path.suffix.lower() in TEXT_SUFFIXES:
        text = path.read_text(encoding="utf-8", errors="replace")
        title = _extract_title(text) or path.stem
        return PaperInfo(source=source, title=title, sections=_split_sections(text), raw_excerpt=text[:6000], text=text)

    if path.exists() and path.suffix.lower() == ".pdf":
        text = extract_pdf_text(path)
        return PaperInfo(
            source=source,
            title=_extract_title(text) or path.stem,
            sections=_split_sections(text),
            raw_excerpt=text[:6000],
            text=text,
        )

    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        title = _title_from_url(source)
        return PaperInfo(
            source=source,
            title=title,
            sections=[PaperSection("Remote paper", f"Remote source registered: {source}")],
            raw_excerpt=f"Remote paper source: {source}",
            text="",
        )

    return PaperInfo(
        source=source,
        title=source,
        sections=[PaperSection("Unknown paper source", "The source could not be read locally.")],
        raw_excerpt=source,
        text="",
    )


def ingest_repo(source: str, focus: list[str], cache_dir: Path = Path(".study-agent") / "repos") -> RepoInfo:
    repo_path = _prepare_repo(source, cache_dir)
    files = list(_iter_code_files(repo_path))
    symbols: list[CodeSymbol] = []
    hits: list[CodeHit] = []
    config_hits: list[CodeHit] = []

    terms = _analysis_terms(focus)
    for file_path in files:
        rel = file_path.relative_to(repo_path).as_posix()
        text = file_path.read_text(encoding="utf-8", errors="replace")
        symbols.extend(_extract_symbols(rel, text))
        file_hits = _find_hits(rel, text, terms)
        hits.extend(file_hits)
        if "config" in rel.lower() or "setting" in rel.lower():
            config_hits.extend(file_hits)

    entry_candidates = _rank_entry_candidates(symbols, hits)
    train_path = _symbols_by_names(symbols, TRAIN_NAMES)
    infer_path = _symbols_by_names(symbols, INFER_NAMES)

    return RepoInfo(
        source=source,
        path=repo_path,
        files_scanned=len(files),
        entry_candidates=entry_candidates[:8],
        symbols=symbols[:500],
        hits=hits[:250],
        config_hits=config_hits[:80],
        train_path=train_path[:12],
        infer_path=infer_path[:12],
    )


def _prepare_repo(source: str, cache_dir: Path) -> Path:
    path = Path(source)
    if path.exists():
        return path.resolve()

    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"}:
        raise RepositoryPrepareError(
            f"Repository path does not exist: {source}. "
            "If you already cloned the repo locally, rerun with `--repo E:\\path\\to\\repo`."
        )

    if shutil.which("git") is None:
        raise RepositoryPrepareError("Git is required to clone remote repositories, but it was not found on PATH.")

    cache_dir.mkdir(parents=True, exist_ok=True)
    repo_name = Path(parsed.path).stem or "repo"
    target = cache_dir / repo_name
    if target.exists():
        return target.resolve()

    completed = subprocess.run(
        ["git", "clone", "--depth", "1", source, str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        reason = (completed.stderr.strip() or completed.stdout.strip() or "Unknown git clone failure.")[-800:]
        git_http = _git_config_value("http.proxy")
        git_https = _git_config_value("https.proxy")
        env_http = os.environ.get("HTTP_PROXY", "") or os.environ.get("http_proxy", "")
        env_https = os.environ.get("HTTPS_PROXY", "") or os.environ.get("https_proxy", "")
        raise RepositoryPrepareError(
            f"GitHub clone failed for {source}. "
            f"If you already cloned the repo locally, rerun with `--repo E:\\path\\to\\repo`. "
            f"git http.proxy={git_http or '(unset)'}, "
            f"git https.proxy={git_https or '(unset)'}, "
            f"env HTTP_PROXY={env_http or '(unset)'}, "
            f"env HTTPS_PROXY={env_https or '(unset)'}. "
            f"Reason: {reason}"
        )
    return target.resolve()


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


def _iter_code_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in CODE_SUFFIXES or path.name.lower() in {"readme.md", "config.yaml", "config.yml"}:
            yield path


def _extract_title(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped.startswith("\\title{") and stripped.endswith("}"):
            return stripped.removeprefix("\\title{").removesuffix("}").strip()
    return None


def _split_sections(text: str) -> list[PaperSection]:
    sections: list[PaperSection] = []
    current_title = "Abstract / Overview"
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.append(PaperSection(current_title, "\n".join(current_lines).strip()))
            current_title = line.lstrip("#").strip() or current_title
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append(PaperSection(current_title, "\n".join(current_lines).strip()))
    return sections[:20]


def _title_from_url(source: str) -> str:
    parsed = urlparse(source)
    name = Path(parsed.path).name or parsed.netloc
    return name.replace(".pdf", "").replace("-", " ").strip() or source


def _analysis_terms(focus: list[str]) -> list[str]:
    defaults = [
        "model",
        "policy",
        "action",
        "reason",
        "attention",
        "cache",
        "train",
        "loss",
        "sample",
        "predict",
        "config",
    ]
    return sorted({term for term in focus + defaults if term})


def _extract_symbols(rel: str, text: str) -> list[CodeSymbol]:
    symbols: list[CodeSymbol] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        py_match = re.match(r"(class|def)\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
        js_match = re.match(r"(export\s+)?(class|function)\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
        if py_match:
            kind, name = py_match.group(1), py_match.group(2)
            symbols.append(CodeSymbol(name=name, kind=kind, path=rel, line=idx, evidence=stripped))
        elif js_match:
            kind, name = js_match.group(2), js_match.group(3)
            symbols.append(CodeSymbol(name=name, kind=kind, path=rel, line=idx, evidence=stripped))
    return symbols


def _find_hits(rel: str, text: str, terms: list[str]) -> list[CodeHit]:
    hits: list[CodeHit] = []
    lowered_terms = [(term, term.lower()) for term in terms]
    for idx, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        for raw, term in lowered_terms:
            if term and term in lowered:
                hits.append(CodeHit(term=raw, path=rel, line=idx, text=line.strip()[:240]))
                break
    return hits


def _rank_entry_candidates(symbols: list[CodeSymbol], hits: list[CodeHit]) -> list[CodeSymbol]:
    hit_counts: dict[str, int] = {}
    for hit in hits:
        hit_counts[hit.path] = hit_counts.get(hit.path, 0) + 1

    def score(symbol: CodeSymbol) -> tuple[int, int, str]:
        name = symbol.name.lower()
        s = hit_counts.get(symbol.path, 0)
        if any(token in name for token in ["model", "vla", "policy", "agent", "head"]):
            s += 20
        if symbol.kind == "class":
            s += 5
        if "readme" in symbol.path.lower():
            s += 2
        return (s, -symbol.line, symbol.path)

    return sorted(symbols, key=score, reverse=True)


def _symbols_by_names(symbols: list[CodeSymbol], names: set[str]) -> list[CodeSymbol]:
    matched = []
    for symbol in symbols:
        lowered = symbol.name.lower()
        if lowered in names or any(name in lowered for name in names):
            matched.append(symbol)
    return matched
