from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .ast_index import build_python_ast_index
from .graph_rank import (
    rerank_architecture_component_candidates,
    rerank_architecture_entry_candidates,
    rerank_architecture_skeleton_candidates,
)
from .models import CodeHit, CodeSymbol, PaperInfo, PaperSection, RepoInfo
from .pdf import extract_pdf_text


TEXT_SUFFIXES = {".md", ".txt", ".tex", ".rst"}
CODE_SUFFIXES = {".py", ".ipynb", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".cc", ".h", ".hpp", ".rs"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".json", ".toml", ".ini"}
DOC_SUFFIXES = {".md", ".rst", ".txt"}
SCRIPT_SUFFIXES = {".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd"}
REPO_TEXT_SUFFIXES = CODE_SUFFIXES | CONFIG_SUFFIXES | DOC_SUFFIXES | SCRIPT_SUFFIXES
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache", "dist", "build"}
TRAIN_NAMES = {"train", "fit", "compute_loss", "loss", "training_step"}
INFER_NAMES = {"sample", "sample_actions", "predict", "predict_action", "forward", "evaluate", "eval", "inference"}
FILE_GROUP_ORDER = [
    "docs",
    "train_scripts",
    "inference_scripts",
    "configs",
    "core_model",
    "deployment_policy",
    "model_policy",
    "loss_objective",
    "data",
    "env_robot_interface",
    "utils",
]
GROUP_PATTERNS: dict[str, tuple[str, ...]] = {
    "docs": ("readme", "docs/", ".md", ".rst", ".txt"),
    "train_scripts": ("train", "trainer", "fit", "training"),
    "inference_scripts": ("infer", "eval", "predict", "sample", "deploy", "serve"),
    "configs": ("config", "configs/", ".yaml", ".yml", ".json", ".toml", ".ini"),
    "core_model": (
        "models/",
        "transformer",
        "attention",
        "encoder",
        "decoder",
        "pipeline",
        "patches",
        "autoencoder",
        "backbone",
    ),
    "deployment_policy": (
        "web_infer_utils/",
        "web_infer_scripts/",
        "openpi_client/",
        "runtime/",
        "client",
        "websocket",
        "server",
        "deploy",
        "policy_agent",
        "base_policy",
    ),
    "model_policy": ("model", "models/", "policy", "agent", "network", "backbone", "encoder", "decoder"),
    "loss_objective": ("loss", "objective", "criterion"),
    "data": ("data", "dataset", "dataloader", "loader", "processor", "tokenizer"),
    "env_robot_interface": ("env", "environment", "robot", "sim", "wrapper", "controller", "interface"),
    "utils": ("utils", "common", "helpers"),
}
GROUP_RANK_BOOSTS: dict[str, tuple[str, ...]] = {
    "docs": ("readme",),
    "train_scripts": ("train", "trainer", "engine", "algorithm"),
    "inference_scripts": ("infer", "eval", "deploy", "server", "predict"),
    "configs": ("config",),
    "core_model": ("transformer", "pipeline", "patches", "attention", "backbone", "encoder", "decoder", "autoencoder"),
    "deployment_policy": ("policy", "client", "websocket", "server", "deploy", "runtime"),
    "model_policy": ("transformer", "pipeline", "patches", "attention", "expert", "policy", "backbone"),
    "loss_objective": ("loss", "objective", "criterion"),
    "data": ("dataset", "dataloader", "processor", "tokenizer"),
    "env_robot_interface": ("environment", "env", "wrapper", "controller", "sim"),
    "utils": ("utils", "helpers", "common"),
}
GROUP_LIMIT = 12


class RepositoryPrepareError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepoInputs:
    repo_path: Path
    files: list[Path]
    terms: list[str]


@dataclass(frozen=True)
class ScannedRepoEvidence:
    rel_paths: list[str]
    symbols: list[CodeSymbol]
    hits: list[CodeHit]
    config_hits: list[CodeHit]


@dataclass(frozen=True)
class ClassifiedRepoFiles:
    file_groups: dict[str, list[str]]
    candidate_lists: dict[str, list[str]]
    merged_model_candidates: list[str]


@dataclass(frozen=True)
class RerankedRoleCandidates:
    role_candidates: dict[str, list[str]]
    candidate_reasons: dict[str, list[str]]
    ast_candidate_reasons: dict[str, list[str]]
    ast_file_tags: dict[str, list[str]]


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
    inputs = _prepare_repo_inputs(source, focus, cache_dir)
    scanned = _scan_repo_evidence(inputs.repo_path, inputs.files, inputs.terms)
    classified = _classify_repo_files(scanned.rel_paths)
    reranked = _assign_and_rerank_role_candidates(inputs.repo_path, scanned.rel_paths, classified)
    return _build_repo_info(
        source,
        inputs.repo_path,
        len(inputs.files),
        scanned,
        classified,
        reranked,
    )


def _prepare_repo_inputs(source: str, focus: list[str], cache_dir: Path) -> RepoInputs:
    repo_path = _prepare_repo(source, cache_dir)
    return RepoInputs(
        repo_path=repo_path,
        files=list(_iter_repo_files(repo_path)),
        terms=_analysis_terms(focus),
    )


def _scan_repo_evidence(repo_path: Path, files: list[Path], terms: list[str]) -> ScannedRepoEvidence:
    symbols: list[CodeSymbol] = []
    hits: list[CodeHit] = []
    config_hits: list[CodeHit] = []
    rel_paths: list[str] = []

    for file_path in files:
        rel = file_path.relative_to(repo_path).as_posix()
        rel_paths.append(rel)
        text = file_path.read_text(encoding="utf-8", errors="replace")
        if file_path.suffix.lower() in CODE_SUFFIXES:
            symbols.extend(_extract_symbols(rel, text))
        file_hits = _find_hits(rel, text, terms)
        hits.extend(file_hits)
        if "config" in rel.lower() or file_path.suffix.lower() in CONFIG_SUFFIXES:
            config_hits.extend(file_hits)

    return ScannedRepoEvidence(
        rel_paths=rel_paths,
        symbols=symbols,
        hits=hits,
        config_hits=config_hits,
    )


def _classify_repo_files(rel_paths: list[str]) -> ClassifiedRepoFiles:
    file_groups = _build_file_groups(rel_paths)
    return ClassifiedRepoFiles(
        file_groups=file_groups,
        candidate_lists={
            "docs": _candidate_list(file_groups, "docs"),
            "train_scripts": _candidate_list(file_groups, "train_scripts"),
            "inference_scripts": _candidate_list(file_groups, "inference_scripts"),
            "configs": _candidate_list(file_groups, "configs"),
            "core_model": _candidate_list(file_groups, "core_model"),
            "deployment_policy": _candidate_list(file_groups, "deployment_policy"),
            "loss_objective": _candidate_list(file_groups, "loss_objective"),
            "data": _candidate_list(file_groups, "data"),
            "env_robot_interface": _candidate_list(file_groups, "env_robot_interface"),
            "utils": _candidate_list(file_groups, "utils"),
        },
        merged_model_candidates=_merged_model_candidates(file_groups),
    )


def _assign_and_rerank_role_candidates(
    repo_path: Path,
    rel_paths: list[str],
    classified: ClassifiedRepoFiles,
) -> RerankedRoleCandidates:
    repo_tokens = _repo_name_tokens(repo_path)
    role_candidates, candidate_reasons = _build_role_candidates(rel_paths, classified.file_groups, repo_tokens)
    ast_index = build_python_ast_index(repo_path, rel_paths)
    reranked_architecture_entry, entry_ast_reasons, entry_ast_tags = rerank_architecture_entry_candidates(
        role_candidates["architecture_entry"],
        classified.candidate_lists["train_scripts"][:8],
        classified.candidate_lists["inference_scripts"][:8],
        role_candidates["config_entry"][:8],
        role_candidates["deployment_entry"][:8],
        ast_index,
    )
    role_candidates["architecture_entry"] = reranked_architecture_entry
    reranked_architecture_skeleton, skeleton_ast_reasons, skeleton_ast_tags = rerank_architecture_skeleton_candidates(
        role_candidates["architecture_skeleton"],
        role_candidates["architecture_entry"],
        classified.candidate_lists["core_model"][:16],
        classified.candidate_lists["train_scripts"][:8],
        classified.candidate_lists["inference_scripts"][:8],
        role_candidates["config_entry"][:8],
        role_candidates["deployment_entry"][:8],
        ast_index,
    )
    role_candidates["architecture_skeleton"] = reranked_architecture_skeleton
    reranked_architecture_component, component_ast_reasons, component_ast_tags = rerank_architecture_component_candidates(
        role_candidates["architecture_component"],
        role_candidates["architecture_skeleton"],
        classified.candidate_lists["core_model"][:16],
        ast_index,
    )
    role_candidates["architecture_component"] = reranked_architecture_component
    ast_candidate_reasons = _merge_reason_maps(
        _prefix_reason_map("architecture_entry", entry_ast_reasons),
        _prefix_reason_map("architecture_skeleton", skeleton_ast_reasons),
        _prefix_reason_map("architecture_component", component_ast_reasons),
    )
    ast_file_tags = {path: index.tags for path, index in ast_index.items() if index.tags}
    ast_file_tags.update(entry_ast_tags)
    ast_file_tags.update(skeleton_ast_tags)
    ast_file_tags.update(component_ast_tags)
    return RerankedRoleCandidates(
        role_candidates=role_candidates,
        candidate_reasons=candidate_reasons,
        ast_candidate_reasons=ast_candidate_reasons,
        ast_file_tags=ast_file_tags,
    )


def _build_repo_info(
    source: str,
    repo_path: Path,
    files_scanned: int,
    scanned: ScannedRepoEvidence,
    classified: ClassifiedRepoFiles,
    reranked: RerankedRoleCandidates,
) -> RepoInfo:
    entry_candidates = _candidate_symbols(
        _merge_role_entry_paths(reranked.role_candidates, classified.file_groups),
        scanned.symbols,
        scanned.hits,
    )
    train_path = _symbols_by_names(scanned.symbols, TRAIN_NAMES)
    infer_path = _symbols_by_names(scanned.symbols, INFER_NAMES)

    return RepoInfo(
        source=source,
        path=repo_path,
        files_scanned=files_scanned,
        file_groups=classified.file_groups,
        entry_candidates=entry_candidates[:8],
        architecture_entry_candidates=reranked.role_candidates["architecture_entry"][:8],
        architecture_skeleton_candidates=reranked.role_candidates["architecture_skeleton"][:8],
        architecture_component_candidates=reranked.role_candidates["architecture_component"][:8],
        config_entry_candidates=reranked.role_candidates["config_entry"][:8],
        deployment_entry_candidates=reranked.role_candidates["deployment_entry"][:8],
        docs_candidates=classified.candidate_lists["docs"],
        train_candidates=classified.candidate_lists["train_scripts"],
        inference_candidates=classified.candidate_lists["inference_scripts"],
        config_candidates=classified.candidate_lists["configs"],
        core_model_candidates=classified.candidate_lists["core_model"],
        deployment_policy_candidates=classified.candidate_lists["deployment_policy"],
        model_candidates=classified.merged_model_candidates,
        loss_candidates=classified.candidate_lists["loss_objective"],
        data_candidates=classified.candidate_lists["data"],
        env_candidates=classified.candidate_lists["env_robot_interface"],
        utils_candidates=classified.candidate_lists["utils"],
        candidate_reasons=reranked.candidate_reasons,
        ast_candidate_reasons=reranked.ast_candidate_reasons,
        ast_file_tags=reranked.ast_file_tags,
        symbols=scanned.symbols[:500],
        hits=scanned.hits[:250],
        config_hits=scanned.config_hits[:80],
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


def _iter_repo_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if _should_scan_file(path):
            yield path


def _should_scan_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    name = path.name.lower()
    return suffix in REPO_TEXT_SUFFIXES or name.startswith("readme")


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

    def score(symbol: CodeSymbol) -> tuple[int, int, int, str]:
        name = symbol.name.lower()
        s = hit_counts.get(symbol.path, 0)
        if any(token in name for token in ["model", "vla", "policy", "agent", "head"]):
            s += 20
        if symbol.kind == "class":
            s += 5
        if "readme" in symbol.path.lower():
            s += 2
        return (s, -_path_depth(symbol.path), -symbol.line, symbol.path)

    return sorted(symbols, key=score, reverse=True)


def _symbols_by_names(symbols: list[CodeSymbol], names: set[str]) -> list[CodeSymbol]:
    matched = []
    for symbol in symbols:
        lowered = symbol.name.lower()
        if lowered in names or any(name in lowered for name in names):
            matched.append(symbol)
    return matched


def _build_file_groups(rel_paths: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {name: [] for name in FILE_GROUP_ORDER}
    for rel in rel_paths:
        matched = _matching_groups(rel)
        for group in matched:
            grouped[group].append(rel)

    return {
        group: _rank_group_paths(group, paths)[:GROUP_LIMIT]
        for group, paths in grouped.items()
    }


def _matching_groups(rel_path: str) -> list[str]:
    lowered = rel_path.lower()
    tokens = _path_tokens(lowered)
    parts = Path(lowered).parts
    matches: list[str] = []
    deployment_match = any(
        _pattern_matches(pattern, lowered, tokens, parts)
        for pattern in GROUP_PATTERNS["deployment_policy"]
    )
    core_match = any(
        _pattern_matches(pattern, lowered, tokens, parts)
        for pattern in GROUP_PATTERNS["core_model"]
    )
    for group, patterns in GROUP_PATTERNS.items():
        if group == "deployment_policy":
            if deployment_match:
                matches.append(group)
            continue
        if group == "core_model":
            if not deployment_match and core_match:
                matches.append(group)
            continue
        if group == "model_policy":
            if deployment_match or core_match or any(
                _pattern_matches(pattern, lowered, tokens, parts) for pattern in patterns
            ):
                matches.append(group)
            continue
        if any(_pattern_matches(pattern, lowered, tokens, parts) for pattern in patterns):
            matches.append(group)
    return matches


def _rank_group_paths(group: str, paths: list[str]) -> list[str]:
    unique = sorted(set(paths))

    def score(path: str) -> tuple[int, int, int, str]:
        lowered = path.lower()
        tokens = _path_tokens(lowered)
        parts = Path(lowered).parts
        strong_hits = sum(1 for pattern in GROUP_PATTERNS[group] if _pattern_matches(pattern, lowered, tokens, parts))
        strong_hits += sum(2 for token in GROUP_RANK_BOOSTS.get(group, ()) if token in tokens)
        if "tests/" in lowered or lowered.startswith("tests/"):
            strong_hits -= 2
        if group == "docs" and lowered != "readme.md" and lowered.endswith(".md"):
            strong_hits -= 1
        if Path(lowered).name == "__init__.py":
            strong_hits -= 4
        if Path(lowered).suffix in SCRIPT_SUFFIXES and group in {"train_scripts", "inference_scripts"}:
            strong_hits += 2
        return (strong_hits, -_path_depth(path), -len(path), path)

    return sorted(unique, key=score, reverse=True)


def _candidate_list(file_groups: dict[str, list[str]], group: str, limit: int = 8) -> list[str]:
    return list(file_groups.get(group, [])[:limit])


def _merged_model_candidates(file_groups: dict[str, list[str]], limit: int = 8) -> list[str]:
    merged: list[str] = []
    for path in file_groups.get("core_model", []):
        if path not in merged:
            merged.append(path)
        if len(merged) >= limit:
            return merged
    for path in file_groups.get("deployment_policy", []):
        if path not in merged:
            merged.append(path)
        if len(merged) >= limit:
            return merged
    for path in file_groups.get("model_policy", []):
        if path not in merged:
            merged.append(path)
        if len(merged) >= limit:
            return merged
    return merged


def _build_role_candidates(
    rel_paths: list[str],
    file_groups: dict[str, list[str]],
    repo_tokens: set[str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    architecture_scored: list[tuple[str, list[str], int]] = []
    architecture_skeleton_scored: list[tuple[str, list[str], int]] = []
    architecture_component_scored: list[tuple[str, list[str], int]] = []
    config_scored: list[tuple[str, list[str], int]] = []
    deployment_scored: list[tuple[str, list[str], int]] = []
    candidate_reasons: dict[str, list[str]] = {}

    for path in rel_paths:
        arch_reasons = _architecture_entry_reasons(path, file_groups, repo_tokens)
        if arch_reasons:
            architecture_scored.append((path, arch_reasons, _architecture_entry_score(path, arch_reasons)))
            candidate_reasons.setdefault(path, []).extend(f"architecture_entry:{reason}" for reason in arch_reasons)

        skeleton_reasons = _architecture_skeleton_reasons(path, file_groups, repo_tokens)
        if skeleton_reasons:
            architecture_skeleton_scored.append((path, skeleton_reasons, _architecture_skeleton_score(path, skeleton_reasons)))
            candidate_reasons.setdefault(path, []).extend(
                f"architecture_skeleton:{reason}" for reason in skeleton_reasons
            )

        component_reasons = _architecture_component_reasons(path, file_groups, repo_tokens)
        if component_reasons:
            architecture_component_scored.append(
                (path, component_reasons, _architecture_component_score(path, component_reasons))
            )
            candidate_reasons.setdefault(path, []).extend(
                f"architecture_component:{reason}" for reason in component_reasons
            )

        config_reasons = _config_entry_reasons(path, file_groups)
        if config_reasons:
            config_scored.append((path, config_reasons, _config_entry_score(path, config_reasons)))
            candidate_reasons.setdefault(path, []).extend(f"config_entry:{reason}" for reason in config_reasons)

        deployment_reasons = _deployment_entry_reasons(path, file_groups)
        if deployment_reasons:
            deployment_scored.append((path, deployment_reasons, _deployment_entry_score(path, deployment_reasons)))
            candidate_reasons.setdefault(path, []).extend(
                f"deployment_entry:{reason}" for reason in deployment_reasons
            )

    return (
        {
            "architecture_entry": _sort_role_candidates(architecture_scored, limit=16),
            "architecture_skeleton": _sort_role_candidates(architecture_skeleton_scored, limit=16),
            "architecture_component": _sort_role_candidates(architecture_component_scored, limit=16),
            "config_entry": _sort_role_candidates(config_scored, limit=16),
            "deployment_entry": _sort_role_candidates(deployment_scored, limit=16),
        },
        candidate_reasons,
    )


def _architecture_entry_reasons(path: str, file_groups: dict[str, list[str]], repo_tokens: set[str]) -> list[str]:
    lowered = path.lower()
    parts = Path(lowered).parts
    tokens = _path_tokens(lowered)
    stem = Path(lowered).stem
    reasons: list[str] = []

    if _is_noise_or_metadata_path(lowered) or Path(lowered).suffix not in CODE_SUFFIXES:
        return reasons

    model_namespaces = {"model", "models", "vlm", "vlms", "vla", "vlas"}
    entry_tokens = {"arch", "builder", "model", "vla", "vlm", "policy"}
    entry_stems = {"builder", "model", "policy"}

    if path in file_groups.get("core_model", []):
        reasons.append("core_model_group")
    if any(part in model_namespaces for part in parts):
        reasons.append("model_namespace")
    if any(part in {"vlms", "vlas"} for part in parts):
        reasons.append("vla_namespace")
    if stem in entry_stems or stem.endswith(("_arch", "_model", "_vla", "_vlm", "_policy")):
        reasons.append("entry_filename")
    matched_tokens = sorted(token for token in entry_tokens if token in tokens)
    reasons.extend(f"entry_token:{token}" for token in matched_tokens[:2])
    matched_repo_tokens = sorted(token for token in repo_tokens if token and token in tokens and token not in {"repo"})
    reasons.extend(f"project_stem_match:{token}" for token in matched_repo_tokens[:2])

    if not reasons:
        return reasons

    if Path(lowered).name == "__init__.py":
        return []
    return reasons


def _architecture_skeleton_reasons(path: str, file_groups: dict[str, list[str]], repo_tokens: set[str]) -> list[str]:
    lowered = path.lower()
    parts = Path(lowered).parts
    tokens = _path_tokens(lowered)
    stem = Path(lowered).stem
    reasons: list[str] = []

    if _is_noise_or_metadata_path(lowered) or Path(lowered).suffix not in CODE_SUFFIXES:
        return reasons

    model_namespaces = {"model", "models", "vlm", "vlms", "vla", "vlas"}
    skeleton_namespaces = {"backbone", "backbones", "head", "heads", "encoder", "encoders", "decoder", "decoders"}
    skeleton_tokens = {"backbone", "head", "encoder", "decoder", "neck", "trunk"}
    skeleton_suffixes = ("_backbone", "_head", "_encoder", "_decoder", "_trunk", "_neck")

    if path in file_groups.get("core_model", []):
        reasons.append("core_model_group")
    if any(part in model_namespaces for part in parts):
        reasons.append("model_namespace")
    if any(part in {"vlms", "vlas"} for part in parts):
        reasons.append("vla_namespace")
    if any(part in skeleton_namespaces for part in parts):
        reasons.append("skeleton_namespace")
    if stem in skeleton_tokens or stem.endswith(skeleton_suffixes):
        reasons.append("skeleton_filename")
    matched_tokens = sorted(token for token in skeleton_tokens if token in tokens)
    reasons.extend(f"skeleton_token:{token}" for token in matched_tokens[:2])
    matched_repo_tokens = sorted(token for token in repo_tokens if token and token in tokens and token not in {"repo"})
    reasons.extend(f"project_stem_match:{token}" for token in matched_repo_tokens[:2])

    if not any(
        reason == "skeleton_namespace" or reason == "skeleton_filename" or reason.startswith("skeleton_token:")
        for reason in reasons
    ):
        return []
    if Path(lowered).name == "__init__.py":
        return []
    return reasons


def _architecture_component_reasons(path: str, file_groups: dict[str, list[str]], repo_tokens: set[str]) -> list[str]:
    lowered = path.lower()
    parts = Path(lowered).parts
    tokens = _path_tokens(lowered)
    stem = Path(lowered).stem
    reasons: list[str] = []

    if _is_noise_or_metadata_path(lowered) or Path(lowered).suffix not in CODE_SUFFIXES:
        return reasons

    model_namespaces = {"model", "models", "vlm", "vlms", "vla", "vlas"}
    component_namespaces = {"layer", "layers", "module", "modules", "block", "blocks", "component", "components"}
    component_tokens = {
        "attention",
        "projector",
        "adapter",
        "embed",
        "embedding",
        "block",
        "layer",
        "module",
        "mlp",
        "ffn",
        "patch",
        "norm",
    }
    component_suffixes = (
        "_attention",
        "_projector",
        "_adapter",
        "_block",
        "_layer",
        "_module",
        "_embedding",
        "_embed",
        "_mlp",
        "_ffn",
        "_patch",
    )

    if path in file_groups.get("core_model", []):
        reasons.append("core_model_group")
    if any(part in model_namespaces for part in parts):
        reasons.append("model_namespace")
    if any(part in component_namespaces for part in parts):
        reasons.append("component_namespace")
    if stem in component_tokens or stem.endswith(component_suffixes):
        reasons.append("component_filename")
    matched_tokens = sorted(token for token in component_tokens if token in tokens)
    reasons.extend(f"component_token:{token}" for token in matched_tokens[:2])
    matched_repo_tokens = sorted(token for token in repo_tokens if token and token in tokens and token not in {"repo"})
    reasons.extend(f"project_stem_match:{token}" for token in matched_repo_tokens[:2])

    if not any(
        reason == "component_namespace" or reason == "component_filename" or reason.startswith("component_token:")
        for reason in reasons
    ):
        return []
    if Path(lowered).name == "__init__.py":
        return []
    return reasons


def _config_entry_reasons(path: str, file_groups: dict[str, list[str]]) -> list[str]:
    lowered = path.lower()
    parts = Path(lowered).parts
    stem = Path(lowered).stem
    reasons: list[str] = []

    if _is_noise_or_metadata_path(lowered):
        return reasons

    if path in file_groups.get("configs", []):
        reasons.append("config_group")
    if "conf" in parts:
        reasons.append("conf_namespace")
    if lowered.endswith("config.py") or lowered.endswith("_config.py"):
        reasons.append("python_config")
    if "training/config.py" in lowered:
        reasons.append("training_config")
    if "policy_config.py" in lowered:
        reasons.append("policy_config")
    if stem == "config":
        reasons.append("config_stem")

    return reasons


def _deployment_entry_reasons(path: str, file_groups: dict[str, list[str]]) -> list[str]:
    lowered = path.lower()
    parts = Path(lowered).parts
    tokens = _path_tokens(lowered)
    reasons: list[str] = []

    if path in file_groups.get("deployment_policy", []):
        reasons.append("deployment_group")
    if any(part in {"serving", "runtime"} for part in parts):
        reasons.append("runtime_namespace")
    matched_tokens = sorted(
        token for token in {"deploy", "server", "client", "websocket", "runtime", "serve", "subscriber"} if token in tokens
    )
    reasons.extend(f"deployment_token:{token}" for token in matched_tokens[:3])
    return reasons


def _architecture_entry_score(path: str, reasons: list[str]) -> int:
    score = 0
    for reason in reasons:
        if reason == "core_model_group":
            score += 5
        elif reason == "model_namespace":
            score += 3
        elif reason == "vla_namespace":
            score += 4
        elif reason == "entry_filename":
            score += 6
        elif reason.startswith("entry_token:"):
            score += 3
        elif reason.startswith("project_stem_match:"):
            score += 2
    if _is_component_like_path(path):
        score -= 6
    elif _is_skeleton_like_path(path):
        score -= 2
    if _is_deployment_like_path(path):
        score -= 8
    if Path(path.lower()).name == "__init__.py":
        score -= 6
    if _is_test_file(path.lower()):
        score -= 4
    return score


def _architecture_skeleton_score(path: str, reasons: list[str]) -> int:
    score = 0
    for reason in reasons:
        if reason == "core_model_group":
            score += 4
        elif reason == "model_namespace":
            score += 2
        elif reason == "vla_namespace":
            score += 2
        elif reason == "skeleton_namespace":
            score += 4
        elif reason == "skeleton_filename":
            score += 5
        elif reason.startswith("skeleton_token:"):
            score += 3
        elif reason.startswith("project_stem_match:"):
            score += 1
    if _is_component_like_path(path):
        score -= 3
    if "backbone" in _path_tokens(path):
        score += 2
    if _is_deployment_like_path(path):
        score -= 6
    if Path(path.lower()).name == "__init__.py":
        score -= 6
    if _is_test_file(path.lower()):
        score -= 4
    return score


def _architecture_component_score(path: str, reasons: list[str]) -> int:
    score = 0
    for reason in reasons:
        if reason == "core_model_group":
            score += 3
        elif reason == "model_namespace":
            score += 2
        elif reason == "component_namespace":
            score += 4
        elif reason == "component_filename":
            score += 5
        elif reason.startswith("component_token:"):
            score += 3
        elif reason.startswith("project_stem_match:"):
            score += 1
    if _is_deployment_like_path(path):
        score -= 6
    if Path(path.lower()).name == "__init__.py":
        score -= 6
    if _is_test_file(path.lower()):
        score -= 4
    return score


def _config_entry_score(path: str, reasons: list[str]) -> int:
    lowered = path.lower()
    score = 0
    for reason in reasons:
        if reason == "conf_namespace":
            score += 6
        elif reason == "training_config":
            score += 5
        elif reason == "policy_config":
            score += 5
        elif reason == "python_config":
            score += 4
        elif reason == "config_group":
            score += 2
        elif reason == "config_stem":
            score += 2
    if any(noise in lowered for noise in [".pre-commit-config.yaml", "tokenizer.json", "tokenizer_config.json", "vocab.json", "processor_config.json", "generation_config.json"]):
        score -= 5
    return score


def _deployment_entry_score(path: str, reasons: list[str]) -> int:
    score = 0
    for reason in reasons:
        if reason == "deployment_group":
            score += 5
        elif reason == "runtime_namespace":
            score += 4
        elif reason.startswith("deployment_token:"):
            score += 2
    return score


def _sort_role_candidates(scored: list[tuple[str, list[str], int]], limit: int = 8) -> list[str]:
    ordered = sorted(
        scored,
        key=lambda item: (item[2], -_path_depth(item[0]), -len(item[0]), item[0]),
        reverse=True,
    )
    result: list[str] = []
    for path, _, _ in ordered:
        if path not in result:
            result.append(path)
        if len(result) >= limit:
            break
    return result


def _merge_reason_maps(*maps: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for mapping in maps:
        for path, reasons in mapping.items():
            bucket = merged.setdefault(path, [])
            for reason in reasons:
                if reason not in bucket:
                    bucket.append(reason)
    return merged


def _prefix_reason_map(prefix: str, mapping: dict[str, list[str]]) -> dict[str, list[str]]:
    return {path: [f"{prefix}:{reason}" for reason in reasons] for path, reasons in mapping.items()}


def _merge_role_entry_paths(role_candidates: dict[str, list[str]], file_groups: dict[str, list[str]], limit: int = 8) -> list[str]:
    merged: list[str] = []
    ordered_groups = [
        role_candidates.get("architecture_entry", []),
        role_candidates.get("architecture_skeleton", []),
        role_candidates.get("architecture_component", []),
        _candidate_list(file_groups, "train_scripts"),
        role_candidates.get("config_entry", []),
        role_candidates.get("deployment_entry", []),
    ]
    for group in ordered_groups:
        for path in group:
            if path not in merged:
                merged.append(path)
            if len(merged) >= limit:
                return merged
    return merged


def _candidate_symbols(paths: list[str], symbols: list[CodeSymbol], hits: list[CodeHit]) -> list[CodeSymbol]:
    selected: list[CodeSymbol] = []
    for path in paths:
        file_symbols = [symbol for symbol in symbols if symbol.path == path]
        if file_symbols:
            chosen = sorted(
                file_symbols,
                key=lambda item: (item.kind != "class", item.line, item.name.lower()),
            )[0]
            if chosen not in selected:
                selected.append(chosen)
            continue

        file_hits = [hit for hit in hits if hit.path == path]
        if file_hits:
            chosen_hit = sorted(file_hits, key=lambda item: (item.line, item.term.lower()))[0]
            selected.append(
                CodeSymbol(
                    name=Path(path).stem,
                    kind="file",
                    path=path,
                    line=chosen_hit.line,
                    evidence=chosen_hit.text or "role-aware file candidate",
                )
            )
            continue

        selected.append(
            CodeSymbol(
                name=Path(path).stem,
                kind="file",
                path=path,
                line=1,
                evidence="role-aware file candidate",
            )
        )
    return selected


def _repo_name_tokens(repo_path: Path) -> set[str]:
    tokens = _path_tokens(repo_path.name.lower())
    expanded = set(tokens)
    for token in list(tokens):
        for suffix in ("vla", "vlm"):
            if token.endswith(suffix) and token != suffix and len(token) > len(suffix) + 1:
                expanded.add(token[: -len(suffix)])
                expanded.add(suffix)
    return expanded


def _is_test_file(lowered_path: str) -> bool:
    name = Path(lowered_path).name
    return lowered_path.startswith("tests/") or "/tests/" in lowered_path or name.endswith("_test.py")


def _is_noise_or_metadata_path(lowered_path: str) -> bool:
    return any(
        marker in lowered_path
        for marker in [
            "egg-info/",
            "extern/hf/",
            "pretrained_models/configs/",
            "diffusion_utils/",
            "__pycache__/",
        ]
    ) or _is_test_file(lowered_path)


def _path_depth(path: str) -> int:
    return len(Path(path).parts)


def _path_tokens(path: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", path.lower()) if token}


def _is_skeleton_like_path(path: str) -> bool:
    tokens = _path_tokens(path)
    return any(token in tokens for token in {"backbone", "head", "encoder", "decoder", "trunk", "neck"})


def _is_component_like_path(path: str) -> bool:
    tokens = _path_tokens(path)
    return any(
        token in tokens
        for token in {"attention", "projector", "adapter", "embed", "embedding", "block", "layer", "module", "mlp", "ffn", "patch", "norm"}
    )


def _is_deployment_like_path(path: str) -> bool:
    tokens = _path_tokens(path)
    return any(token in tokens for token in {"client", "server", "deploy", "runtime", "websocket", "serve"})


def _pattern_matches(pattern: str, lowered_path: str, tokens: set[str], parts: tuple[str, ...]) -> bool:
    if pattern.endswith("/"):
        return pattern.removesuffix("/") in parts
    if pattern.startswith("."):
        return lowered_path.endswith(pattern)
    return pattern in tokens
