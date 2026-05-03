from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


ARCHITECTURE_SIGNAL_NAMES = {
    "encode",
    "forward",
    "get_cost",
    "predict_action",
    "predict",
    "from_pretrained",
    "get_model",
    "get_vlm",
    "load_vla",
    "rollout",
    "sample_actions",
}
HELPER_PATH_TOKENS = {"utils", "common", "helpers", "ops", "io", "logging", "transforms"}
SUBMODULE_BUILDER_TOKENS = {"pixel_decoder", "multimodal_encoder", "multimodal_projector", "decoder", "encoder", "projector"}
SKELETON_ROLE_TOKENS = {
    "backbone",
    "backbones",
    "head",
    "heads",
    "actionhead",
    "actionheads",
    "encoder",
    "encoders",
    "decoder",
    "decoders",
    "bridge",
    "wrapper",
    "trunk",
    "neck",
    "vit",
    "transformer",
    "predictor",
    "embedder",
}
COMPONENT_ROLE_TOKENS = {
    "attention",
    "projector",
    "projectors",
    "adapter",
    "embedding",
    "embed",
    "block",
    "blocks",
    "layer",
    "layers",
    "mlp",
    "ffn",
    "norm",
    "patch",
}
SCRIPT_IMPORT_TOKENS = {"argparse", "tyro", "draccus"}
SCRIPT_NAME_PREFIXES = ("compute_", "prepare_", "convert_", "export_", "dump_")
SCRIPT_NAME_SUFFIXES = ("_stats", "_script")
MAJOR_MODULE_TOKENS = {"vision", "projector", "decoder", "llm", "vlm", "action", "head", "backbone", "encoder"}


@dataclass(frozen=True)
class PythonFileIndex:
    path: str
    imports: list[str]
    imported_names: list[str]
    defined_classes: list[str]
    defined_functions: list[str]
    base_classes: list[str]
    called_names: list[str]
    instantiated_names: list[str]
    tags: list[str]
    architecture_signals: list[str]


def build_python_ast_index(repo_root: Path, rel_paths: list[str]) -> dict[str, PythonFileIndex]:
    index: dict[str, PythonFileIndex] = {}
    for rel_path in rel_paths:
        if Path(rel_path).suffix.lower() != ".py":
            continue
        file_path = repo_root / rel_path
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(text, filename=rel_path)
        except SyntaxError:
            index[rel_path] = PythonFileIndex(
                path=rel_path,
                imports=[],
                imported_names=[],
                defined_classes=[],
                defined_functions=[],
                base_classes=[],
                called_names=[],
                instantiated_names=[],
                tags=["ast_parse_failed"],
                architecture_signals=[],
            )
            continue

        visitor = _PythonFileVisitor()
        visitor.visit(tree)
        tags = _infer_tags(rel_path, visitor)
        architecture_signals = _infer_architecture_signals(visitor)
        index[rel_path] = PythonFileIndex(
            path=rel_path,
            imports=sorted(visitor.imports),
            imported_names=sorted(visitor.imported_names),
            defined_classes=sorted(visitor.defined_classes),
            defined_functions=sorted(visitor.defined_functions),
            base_classes=sorted(visitor.base_classes),
            called_names=sorted(visitor.called_names),
            instantiated_names=sorted(visitor.instantiated_names),
            tags=tags,
            architecture_signals=architecture_signals,
        )
    return index


class _PythonFileVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.imported_names: set[str] = set()
        self.defined_classes: set[str] = set()
        self.defined_functions: set[str] = set()
        self.base_classes: set[str] = set()
        self.called_names: set[str] = set()
        self.instantiated_names: set[str] = set()
        self._has_main_guard = False

    @property
    def has_main_guard(self) -> bool:
        return self._has_main_guard

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name:
                self.imports.add(alias.name)
                self.imported_names.add(alias.asname or alias.name.split(".")[-1])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module)
        for alias in node.names:
            if alias.name:
                if node.module:
                    self.imports.add(f"{node.module}.{alias.name}")
                self.imported_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.defined_classes.add(node.name)
        for base in node.bases:
            base_name = _expr_name(base)
            if base_name:
                self.base_classes.add(base_name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        call_name = _expr_name(node.func)
        if call_name:
            self.called_names.add(call_name)
            if _looks_like_constructor(call_name):
                self.instantiated_names.add(call_name)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        if _is_main_guard(node.test):
            self._has_main_guard = True
        self.generic_visit(node)


def _infer_tags(rel_path: str, visitor: _PythonFileVisitor) -> list[str]:
    tags: set[str] = set()
    lowered = rel_path.lower()
    tokens = _path_tokens(rel_path)
    stem = Path(rel_path).stem.lower()
    class_names = {name.lower() for name in visitor.defined_classes}
    function_names = {name.lower() for name in visitor.defined_functions}
    base_names = {name.lower() for name in visitor.base_classes}
    imported = {name.lower() for name in visitor.imported_names}
    called = {name.lower() for name in visitor.called_names}

    if any(token in HELPER_PATH_TOKENS for token in tokens):
        tags.add("helper_like")
    if stem.startswith("base_") or "abc" in base_names or any(name.startswith("base") for name in class_names):
        tags.add("abstract_base")
    imported_or_called = imported | called

    if visitor.has_main_guard or imported_or_called & SCRIPT_IMPORT_TOKENS:
        tags.add("entrypoint_like")
        tags.add("script_like")
    if (
        any("config" in name for name in class_names)
        or stem.endswith("config")
        or "choiceregistry" in base_names
        or ("dataclass" in imported and any("config" in name for name in class_names | function_names | {stem}))
    ):
        tags.add("config_like")
    if stem == "builder" and any(token in lowered for token in SUBMODULE_BUILDER_TOKENS):
        tags.add("submodule_builder")
    if stem in {"action_head", "action_heads"} or any("actionhead" in name.replace("_", "") for name in class_names):
        tags.add("action_head_like")
        tags.add("skeleton_like")
    if stem in {"projector", "projectors"} or any("projector" in name for name in class_names):
        tags.add("projector_like")
        tags.add("component_like")
    if any(_is_model_like_class_name(name) for name in visitor.defined_classes) and "abstract_base" not in tags:
        tags.add("concrete_model_like")
    if "abstract_base" not in tags and ("forward" in function_names or "predict_action" in function_names) and (
        any(_is_model_like_class_name(name) for name in visitor.defined_classes)
        or any(_is_model_like_base(name) for name in visitor.base_classes)
    ):
        tags.add("concrete_model_like")
    if _is_world_model_like(visitor):
        tags.add("world_model_like")
        tags.add("assembly_like")
    if _has_multi_module_assembly(imported_or_called):
        tags.add("assembly_like")
    if _has_bridge_behavior(imported_or_called):
        tags.add("bridge_like")
    if _has_skeleton_signature(tokens, class_names, function_names, base_names, stem):
        tags.add("skeleton_like")
    if _has_component_signature(tokens, class_names, function_names, base_names, stem):
        tags.add("component_like")
    if _looks_like_script(tokens, stem, imported_or_called):
        tags.add("script_like")
    return sorted(tags)


def _infer_architecture_signals(visitor: _PythonFileVisitor) -> list[str]:
    signals: set[str] = set()
    lowered_calls = {name.lower() for name in visitor.called_names}
    lowered_functions = {name.lower() for name in visitor.defined_functions}
    for name in ARCHITECTURE_SIGNAL_NAMES:
        if name in lowered_functions or name in lowered_calls:
            signals.add(name)
    for call_name in lowered_calls:
        if call_name.startswith("build_"):
            signals.add("build_*")
        if call_name.startswith("load_"):
            signals.add("load_*")
    return sorted(signals)


def _expr_name(node: ast.AST | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _expr_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return _expr_name(node.func)
    if isinstance(node, ast.Subscript):
        return _expr_name(node.value)
    return ""


def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return False
    left = _expr_name(node.left)
    comparator = node.comparators[0]
    if not isinstance(comparator, ast.Constant) or comparator.value != "__main__":
        return False
    return left == "__name__"


def _looks_like_constructor(name: str) -> bool:
    tail = name.split(".")[-1]
    return bool(re.match(r"[A-Z][A-Za-z0-9_]*$", tail))


def _path_tokens(path: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", path.lower()) if token}


def bases_or_imports(base_names: set[str], imported: set[str]) -> set[str]:
    return set(base_names) | set(imported)


def _camel_tokens(name: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return [token.lower() for token in re.split(r"[^A-Za-z0-9]+|\s+", normalized) if token]


def _is_model_like_class_name(name: str) -> bool:
    tokens = _camel_tokens(name)
    if not tokens:
        return False
    if any(token in {"config", "arguments", "trainer"} for token in tokens):
        return False
    return any(token in {"policy", "model", "vla", "vlm"} for token in tokens) or "forcausallm" in name.lower()


def _is_model_like_base(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("model", "vlm", "policy", "pretrainedmodel", "forcausallm"))


def _is_world_model_like(visitor: _PythonFileVisitor) -> bool:
    if len(visitor.defined_classes) != 1:
        return False
    base_names = {name.lower() for name in visitor.base_classes}
    function_names = {name.lower() for name in visitor.defined_functions}
    if not any(token in base for token in ("module", "nn.module", "lightningmodule") for base in base_names):
        return False
    architecture_hits = {
        name
        for name in function_names
        if name in {"encode", "predict", "rollout", "get_cost", "sample_actions", "forward", "predict_action"}
    }
    return len(architecture_hits) >= 2


def _has_skeleton_signature(
    path_tokens: set[str],
    class_names: set[str],
    function_names: set[str],
    base_names: set[str],
    stem: str,
) -> bool:
    return any(
        token in SKELETON_ROLE_TOKENS
        for token in (
            path_tokens
            | {stem}
            | _expanded_name_tokens(class_names)
            | _expanded_name_tokens(function_names)
            | _expanded_name_tokens(base_names)
        )
    )


def _has_component_signature(
    path_tokens: set[str],
    class_names: set[str],
    function_names: set[str],
    base_names: set[str],
    stem: str,
) -> bool:
    del function_names
    return any(
        token in COMPONENT_ROLE_TOKENS
        for token in (
            path_tokens
            | {stem}
            | _expanded_name_tokens(class_names)
            | _expanded_name_tokens(base_names)
        )
    )


def _has_multi_module_assembly(names: set[str]) -> bool:
    major_hits = {token for token in MAJOR_MODULE_TOKENS if any(token in name for name in names)}
    build_hits = {name for name in names if name.startswith("build_") or name.startswith("load_")}
    return len(major_hits) >= 2 or len(build_hits) >= 2


def _has_bridge_behavior(names: set[str]) -> bool:
    groups = {
        "vision": any(token in name for token in ("vision", "siglip", "vit") for name in names),
        "language": any(token in name for token in ("llm", "vlm", "gemma", "qwen") for name in names),
        "action": any(token in name for token in ("action", "head", "decoder") for name in names),
    }
    return sum(1 for matched in groups.values() if matched) >= 2


def _looks_like_script(tokens: set[str], stem: str, names: set[str]) -> bool:
    if "scripts" in tokens or "script" in tokens:
        return True
    if stem.startswith(SCRIPT_NAME_PREFIXES) or stem.endswith(SCRIPT_NAME_SUFFIXES):
        return True
    if "stats" in tokens and "model" not in tokens and "models" not in tokens:
        return True
    return bool(names & SCRIPT_IMPORT_TOKENS)


def _expanded_name_tokens(names: set[str]) -> set[str]:
    tokens: set[str] = set()
    for name in names:
        lowered = name.lower()
        tokens.update(_camel_tokens(name))
        tokens.update(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
        tokens.add(lowered.replace("_", ""))
    return tokens
