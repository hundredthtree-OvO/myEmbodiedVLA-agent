from __future__ import annotations

from pathlib import Path

from .ast_index import PythonFileIndex


def rerank_architecture_entry_candidates(
    architecture_entry_candidates: list[str],
    train_candidates: list[str],
    inference_candidates: list[str],
    config_entry_candidates: list[str],
    deployment_entry_candidates: list[str],
    ast_index: dict[str, PythonFileIndex],
) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]]]:
    root_indexes = _root_indexes(
        train_candidates[:8] + inference_candidates[:8] + config_entry_candidates[:8] + deployment_entry_candidates[:8],
        ast_index,
    )
    candidate_pool = _expand_candidate_pool(
        architecture_entry_candidates[:16],
        ast_index,
        root_indexes,
        _entry_eligible,
        limit=16,
    )

    score_map: dict[str, tuple[float, list[str], list[str]]] = {}
    for path in candidate_pool:
        file_index = ast_index.get(path)
        reasons, tags = _initial_debug(file_index)
        score = 0.0
        if file_index is None or "ast_parse_failed" in tags:
            score_map[path] = (score, reasons, tags)
            continue

        score += _entry_concrete_model_bonus(path, file_index, reasons)
        score += _entry_assembly_bonus(path, file_index, reasons)
        score += _reverse_root_bonus(path, file_index, root_indexes, reasons, bonus=2.5)
        score += _shared_penalties(path, file_index, reasons)
        score += _entry_penalties(path, file_index, reasons)
        score_map[path] = (score, reasons, tags)

    return _finalize(candidate_pool, score_map)


def rerank_architecture_skeleton_candidates(
    architecture_skeleton_candidates: list[str],
    architecture_entry_candidates: list[str],
    core_model_candidates: list[str],
    train_candidates: list[str],
    inference_candidates: list[str],
    config_entry_candidates: list[str],
    deployment_entry_candidates: list[str],
    ast_index: dict[str, PythonFileIndex],
) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]]]:
    root_indexes = _root_indexes(
        architecture_entry_candidates[:8]
        + train_candidates[:8]
        + inference_candidates[:8]
        + config_entry_candidates[:8]
        + deployment_entry_candidates[:8],
        ast_index,
    )
    candidate_pool = _expand_candidate_pool(
        _candidate_pool(
            architecture_skeleton_candidates[:16],
            architecture_entry_candidates[:8],
            core_model_candidates[:16],
        ),
        ast_index,
        root_indexes,
        _skeleton_eligible,
        limit=16,
    )
    entry_set = set(architecture_entry_candidates[:8])

    score_map: dict[str, tuple[float, list[str], list[str]]] = {}
    for path in candidate_pool:
        file_index = ast_index.get(path)
        reasons, tags = _initial_debug(file_index)
        score = 0.0
        if file_index is None or "ast_parse_failed" in tags:
            score_map[path] = (score, reasons, tags)
            continue

        score += _skeleton_bonus(path, file_index, reasons)
        score += _assembly_bridge_bonus(path, file_index, reasons)
        score += _reverse_root_bonus(path, file_index, root_indexes, reasons, bonus=2.0)
        score += _shared_penalties(path, file_index, reasons)
        score += _skeleton_penalties(path, file_index, reasons, entry_set)
        score_map[path] = (score, reasons, tags)

    return _finalize(candidate_pool, score_map)


def rerank_architecture_component_candidates(
    architecture_component_candidates: list[str],
    architecture_skeleton_candidates: list[str],
    core_model_candidates: list[str],
    ast_index: dict[str, PythonFileIndex],
) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]]]:
    root_indexes = _root_indexes(
        architecture_skeleton_candidates[:8] + core_model_candidates[:16],
        ast_index,
    )
    candidate_pool = _expand_candidate_pool(
        _candidate_pool(
            architecture_component_candidates[:16],
            architecture_skeleton_candidates[:8],
            core_model_candidates[:16],
        ),
        ast_index,
        root_indexes,
        _component_eligible,
        limit=16,
    )

    score_map: dict[str, tuple[float, list[str], list[str]]] = {}
    for path in candidate_pool:
        file_index = ast_index.get(path)
        reasons, tags = _initial_debug(file_index)
        score = 0.0
        if file_index is None or "ast_parse_failed" in tags:
            score_map[path] = (score, reasons, tags)
            continue

        score += _component_bonus(path, file_index, reasons)
        score += _shared_penalties(path, file_index, reasons)
        score += _component_penalties(path, file_index, reasons)
        score_map[path] = (score, reasons, tags)

    return _finalize(candidate_pool, score_map)


def _candidate_pool(*groups: list[str]) -> list[str]:
    ordered: list[str] = []
    for group in groups:
        for path in group:
            if path not in ordered:
                ordered.append(path)
    return ordered


def _expand_candidate_pool(
    base_candidates: list[str],
    ast_index: dict[str, PythonFileIndex],
    root_indexes: dict[str, PythonFileIndex],
    eligibility_fn,
    limit: int,
) -> list[str]:
    ordered = list(dict.fromkeys(base_candidates))
    if len(ordered) >= limit:
        return ordered[:limit]

    symbol_map = _symbol_to_paths(ast_index)
    referenced_scores: dict[str, float] = {}
    for root_path, root_index in root_indexes.items():
        root_symbols = {
            *root_index.imported_names,
            *root_index.instantiated_names,
            *root_index.called_names,
        }
        for symbol in root_symbols:
            symbol_key = symbol.split(".")[-1].lower()
            for path in symbol_map.get(symbol_key, []):
                if path == root_path or path in ordered:
                    continue
                file_index = ast_index.get(path)
                if file_index is None or not eligibility_fn(path, file_index):
                    continue
                referenced_scores[path] = referenced_scores.get(path, 0.0) + 1.0

    extras = sorted(
        referenced_scores,
        key=lambda path: (referenced_scores[path], -_path_depth(path), -len(path), path),
        reverse=True,
    )
    for path in extras:
        ordered.append(path)
        if len(ordered) >= limit:
            break
    return ordered


def _symbol_to_paths(ast_index: dict[str, PythonFileIndex]) -> dict[str, list[str]]:
    symbol_map: dict[str, list[str]] = {}
    for path, file_index in ast_index.items():
        for symbol in [*file_index.defined_classes, *file_index.defined_functions]:
            if not _is_meaningful_symbol(symbol):
                continue
            symbol_map.setdefault(symbol.split(".")[-1].lower(), []).append(path)
    return symbol_map


def _root_indexes(root_candidates: list[str], ast_index: dict[str, PythonFileIndex]) -> dict[str, PythonFileIndex]:
    unique_roots = list(dict.fromkeys(root_candidates))
    return {path: ast_index[path] for path in unique_roots if path in ast_index}


def _initial_debug(file_index: PythonFileIndex | None) -> tuple[list[str], list[str]]:
    if file_index is None:
        return (["ast_missing"], [])
    tags = list(file_index.tags)
    if "ast_parse_failed" in tags:
        return (["ast_parse_failed"], tags)
    return ([], tags)


def _entry_concrete_model_bonus(path: str, file_index: PythonFileIndex, reasons: list[str]) -> float:
    score = 0.0
    class_names = {name.lower() for name in file_index.defined_classes}
    base_names = {name.lower() for name in file_index.base_classes}
    signal_names = set(file_index.architecture_signals)
    if "world_model_like" in file_index.tags:
        score += 4.0
        reasons.append("world_model_bonus")
    if "concrete_model_like" in file_index.tags:
        score += 4.0
        reasons.append("concrete_model_bonus")
    if any(
        token in name
        for token in ("policy", "model", "vla", "vlm", "forcausallm")
        for name in class_names
    ):
        score += 2.0
        reasons.append("concrete_model_class")
    if "forward" in signal_names or "predict_action" in signal_names or "sample_actions" in signal_names:
        score += 2.0
        reasons.append("architecture_forward_signal")
    if any(token in name for token in ("metamodel", "vlm", "pretrainedmodel", "basemodel") for name in base_names):
        score += 2.0
        reasons.append("concrete_model_inheritance")
    if Path(path).stem.lower().endswith("_arch"):
        score += 3.0
        reasons.append("concrete_model_arch_file")
    return score


def _entry_assembly_bonus(path: str, file_index: PythonFileIndex, reasons: list[str]) -> float:
    score = 0.0
    lowered_calls = {name.lower() for name in file_index.called_names}
    lowered_imports = {name.lower() for name in file_index.imports}
    build_calls = {name for name in lowered_calls if name.startswith("build_")}
    load_calls = {name for name in lowered_calls if name.startswith("load_")}
    assembly_hits = {
        "vision": any("vision" in name for name in lowered_calls | lowered_imports),
        "projector": any("projector" in name for name in lowered_calls | lowered_imports),
        "llm": any("llm" in name or "vlm" in name for name in lowered_calls | lowered_imports),
        "decoder": any("decoder" in name for name in lowered_calls | lowered_imports),
    }
    if len(build_calls) + len(load_calls) >= 2 or "assembly_like" in file_index.tags:
        score += 3.0
        reasons.append("assembly_bonus:multi_build_load")
    if sum(1 for matched in assembly_hits.values() if matched) >= 2:
        score += 3.0
        reasons.append("assembly_bonus:multi_major_modules")
    if "bridge_like" in file_index.tags:
        score += 2.0
        reasons.append("assembly_bonus:bridge_like")
    if Path(path).stem.lower().endswith("_arch"):
        score += 2.0
        reasons.append("assembly_bonus:arch_filename")
    return score


def _skeleton_bonus(path: str, file_index: PythonFileIndex, reasons: list[str]) -> float:
    score = 0.0
    stem = Path(path).stem.lower()
    if "world_model_like" in file_index.tags:
        score += 3.0
        reasons.append("skeleton_bonus:world_model")
    if "skeleton_like" in file_index.tags:
        score += 5.0
        reasons.append("skeleton_bonus")
    if "action_head_like" in file_index.tags:
        score += 2.0
        reasons.append("skeleton_bonus:action_head")
    if stem in {"model", "vit"} or stem.startswith("pi"):
        score += 2.5
        reasons.append("skeleton_bonus:core_model_stem")
    if "concrete_model_like" in file_index.tags and any(
        signal in file_index.architecture_signals for signal in ("sample_actions", "forward", "predict_action")
    ):
        score += 2.0
        reasons.append("skeleton_bonus:model_runtime_signal")
    return score


def _assembly_bridge_bonus(path: str, file_index: PythonFileIndex, reasons: list[str]) -> float:
    score = 0.0
    if "assembly_like" in file_index.tags:
        score += 3.0
        reasons.append("assembly_bonus")
    if "bridge_like" in file_index.tags:
        score += 2.0
        reasons.append("bridge_bonus")
    if any(signal in file_index.architecture_signals for signal in ("build_*", "load_*")):
        score += 2.0
        reasons.append("assembly_bonus:build_load_signal")
    return score


def _component_bonus(path: str, file_index: PythonFileIndex, reasons: list[str]) -> float:
    score = 0.0
    stem = Path(path).stem.lower()
    if "component_like" in file_index.tags:
        score += 5.0
        reasons.append("component_bonus")
    if "projector_like" in file_index.tags:
        score += 2.0
        reasons.append("component_bonus:projector")
    if stem in {"attention", "projector", "adapter", "mlp", "norm"}:
        score += 2.0
        reasons.append("component_bonus:component_stem")
    return score


def _entry_eligible(path: str, file_index: PythonFileIndex) -> bool:
    if any(tag in file_index.tags for tag in ("helper_like", "script_like")):
        return False
    return (
        "concrete_model_like" in file_index.tags
        or "world_model_like" in file_index.tags
        or "assembly_like" in file_index.tags
        or any(
            signal in file_index.architecture_signals
            for signal in ("forward", "predict_action", "sample_actions", "encode", "predict", "rollout", "get_cost")
        )
    )


def _skeleton_eligible(path: str, file_index: PythonFileIndex) -> bool:
    if any(tag in file_index.tags for tag in ("helper_like", "script_like")):
        return False
    return any(
        tag in file_index.tags
        for tag in ("skeleton_like", "assembly_like", "bridge_like", "world_model_like", "action_head_like")
    )


def _component_eligible(path: str, file_index: PythonFileIndex) -> bool:
    if any(tag in file_index.tags for tag in ("helper_like", "script_like")):
        return False
    return any(tag in file_index.tags for tag in ("component_like", "projector_like"))


def _reverse_root_bonus(
    candidate_path: str,
    candidate_index: PythonFileIndex,
    root_indexes: dict[str, PythonFileIndex],
    reasons: list[str],
    bonus: float,
) -> float:
    score = 0.0
    candidate_symbols = {
        *candidate_index.defined_classes,
        *candidate_index.defined_functions,
    }
    candidate_symbol_tokens = {symbol.lower() for symbol in candidate_symbols if _is_meaningful_symbol(symbol)}
    if not candidate_symbol_tokens:
        return score
    for root_path, root_index in root_indexes.items():
        if root_path == candidate_path:
            continue
        root_symbols = {
            *root_index.called_names,
            *root_index.imported_names,
            *root_index.instantiated_names,
        }
        matched = sorted(
            symbol
            for symbol in root_symbols
            if _is_meaningful_symbol(symbol) and symbol.lower() in candidate_symbol_tokens
        )
        if matched:
            score += bonus
            reasons.append(f"reverse_root_bonus:{root_path}->{matched[0]}")
    return score


def _shared_penalties(path: str, file_index: PythonFileIndex, reasons: list[str]) -> float:
    score = 0.0
    lowered = path.lower()
    stem = Path(path).stem.lower()
    if "helper_like" in file_index.tags:
        score -= 4.0
        reasons.append("helper_penalty")
    if "script_like" in file_index.tags:
        score -= 8.0
        reasons.append("script_penalty")
    if any(token in lowered for token in ("client", "server", "runtime", "serve", "deploy")):
        score -= 4.0
        reasons.append("deployment_leak_penalty")
    if "entrypoint_like" in file_index.tags and "model/" not in lowered and "/models/" not in lowered:
        score -= 3.0
        reasons.append("entrypoint_like_penalty")
    if "config_like" in file_index.tags and "concrete_model_like" not in file_index.tags and "model/" not in lowered:
        score -= 2.0
        reasons.append("config_like_penalty")
    if stem.startswith("base_"):
        score -= 3.0
        reasons.append("abstract_base_penalty:base_stem")
    if _is_test_file(lowered):
        score -= 5.0
        reasons.append("test_file_penalty")
    return score


def _entry_penalties(path: str, file_index: PythonFileIndex, reasons: list[str]) -> float:
    score = 0.0
    if "abstract_base" in file_index.tags:
        score -= 9.0
        reasons.append("abstract_base_penalty")
    if "submodule_builder" in file_index.tags and _has_top_level_architecture_hint(path):
        score -= 5.0
        reasons.append("submodule_builder_penalty")
    return score


def _skeleton_penalties(path: str, file_index: PythonFileIndex, reasons: list[str], entry_set: set[str]) -> float:
    score = 0.0
    stem = Path(path).stem.lower()
    if "component_like" in file_index.tags and "skeleton_like" not in file_index.tags:
        score -= 4.0
        reasons.append("component_penalty")
    if "projector_like" in file_index.tags:
        score -= 2.0
        reasons.append("component_penalty:projector")
    if "abstract_base" in file_index.tags and "assembly_like" not in file_index.tags:
        score -= 1.5
        reasons.append("abstract_base_penalty:weak")
    if path in entry_set and "skeleton_like" not in file_index.tags:
        score -= 2.0
        reasons.append("entry_overlap_penalty")
    if stem in {"tokenizer", "registry", "materialize"}:
        score -= 3.0
        reasons.append("auxiliary_file_penalty")
    return score


def _component_penalties(path: str, file_index: PythonFileIndex, reasons: list[str]) -> float:
    score = 0.0
    stem = Path(path).stem.lower()
    if "assembly_like" in file_index.tags:
        score -= 5.0
        reasons.append("assembly_penalty")
    if "bridge_like" in file_index.tags:
        score -= 2.0
        reasons.append("bridge_penalty")
    if "skeleton_like" in file_index.tags:
        score -= 4.0
        reasons.append("skeleton_penalty")
    if "concrete_model_like" in file_index.tags:
        score -= 5.0
        reasons.append("concrete_model_penalty")
    if "action_head_like" in file_index.tags:
        score -= 2.0
        reasons.append("skeleton_penalty:action_head")
    if "abstract_base" in file_index.tags and "component_like" not in file_index.tags:
        score -= 2.0
        reasons.append("abstract_base_penalty")
    if stem in {"tokenizer", "registry", "materialize"}:
        score -= 2.0
        reasons.append("auxiliary_file_penalty")
    return score


def _finalize(
    candidate_pool: list[str],
    score_map: dict[str, tuple[float, list[str], list[str]]],
) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]]]:
    ordered = sorted(
        candidate_pool,
        key=lambda path: (score_map[path][0], -_path_depth(path), -len(path), path),
        reverse=True,
    )
    ast_candidate_reasons = {path: score_map[path][1] for path in candidate_pool if score_map[path][1]}
    ast_file_tags = {path: score_map[path][2] for path in candidate_pool if score_map[path][2]}
    return ordered, ast_candidate_reasons, ast_file_tags


def _has_top_level_architecture_hint(path: str) -> bool:
    lowered = path.lower()
    return any(token in lowered for token in ("pixel_decoder/", "multimodal_encoder/", "multimodal_projector/"))


def _path_depth(path: str) -> int:
    return len(Path(path).parts)


def _is_meaningful_symbol(symbol: str) -> bool:
    tail = symbol.split(".")[-1]
    lowered = tail.lower()
    if lowered in {"forward", "list", "dict", "tuple", "optional", "torch", "np", "nn", "*"}:
        return False
    return (
        tail[:1].isupper()
        or any(
            token in lowered
            for token in ("policy", "model", "vla", "vlm", "decoder", "encoder", "projector", "head", "transformer")
        )
    )


def _is_test_file(lowered_path: str) -> bool:
    path = Path(lowered_path)
    name = path.name
    return (
        "/tests/" in lowered_path
        or "\\tests\\" in lowered_path
        or name.startswith("test_")
        or name.endswith("_test.py")
    )
