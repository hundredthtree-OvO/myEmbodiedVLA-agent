from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ParsedSymbol:
    name: str
    kind: str
    line_start: int
    line_end: int
    bases: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedImport:
    module: str
    imported_name: str | None
    line: int


@dataclass(frozen=True)
class ParsedRelation:
    relation_type: str
    source_symbol: str | None
    target_name: str
    line: int


@dataclass(frozen=True)
class ParsedCodeFile:
    path: str
    language: str
    symbols: list[ParsedSymbol]
    imports: list[ParsedImport]
    relations: list[ParsedRelation]


class CodeParser(Protocol):
    def supports_language(self, language: str) -> bool: ...

    def parse_file(self, path: Path, text: str) -> ParsedCodeFile: ...


class PythonAstCodeParser(CodeParser):
    """Compatibility parser for the current codebase.

    This adapter keeps the project running while the main parser backend
    transitions to tree-sitter. New business logic should depend on the
    `CodeParser` protocol rather than directly on `ast`.
    """

    def supports_language(self, language: str) -> bool:
        return language.lower() == "python"

    def parse_file(self, path: Path, text: str) -> ParsedCodeFile:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return ParsedCodeFile(
                path=path.as_posix(),
                language="python",
                symbols=[],
                imports=[],
                relations=[],
            )
        symbols: list[ParsedSymbol] = []
        imports: list[ParsedImport] = []
        relations: list[ParsedRelation] = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                symbols.append(
                    ParsedSymbol(
                        name=node.name,
                        kind="class",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        bases=[_expr_name(base) for base in node.bases if _expr_name(base)],
                    )
                )
                relations.extend(_class_relations(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(
                    ParsedSymbol(
                        name=node.name,
                        kind="function",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                    )
                )
                relations.extend(_function_relations(node))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ParsedImport(module=alias.name, imported_name=None, line=node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(ParsedImport(module=module, imported_name=alias.name, line=node.lineno))

        return ParsedCodeFile(
            path=path.as_posix(),
            language="python",
            symbols=symbols,
            imports=imports,
            relations=relations,
        )


def _class_relations(node: ast.ClassDef) -> list[ParsedRelation]:
    relations: list[ParsedRelation] = []
    for base in node.bases:
        target = _expr_name(base)
        if target:
            relations.append(
                ParsedRelation(
                    relation_type="inherits",
                    source_symbol=node.name,
                    target_name=target,
                    line=getattr(base, "lineno", node.lineno),
                )
            )
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            relations.extend(_function_relations(child, source_symbol=f"{node.name}.{child.name}"))
    return relations


def _function_relations(node: ast.AST, source_symbol: str | None = None) -> list[ParsedRelation]:
    relations: list[ParsedRelation] = []
    source = source_symbol or getattr(node, "name", None)
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            target = _expr_name(child.func)
            if target:
                relations.append(
                    ParsedRelation(
                        relation_type="calls",
                        source_symbol=source,
                        target_name=target,
                        line=getattr(child, "lineno", 0),
                    )
                )
            if _looks_like_constructor_name(target):
                relations.append(
                    ParsedRelation(
                        relation_type="instantiates",
                        source_symbol=source,
                        target_name=target or "",
                        line=getattr(child, "lineno", 0),
                    )
                )
    return relations


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
    return ""


def _looks_like_constructor_name(name: str | None) -> bool:
    if not name:
        return False
    last = name.split(".")[-1]
    return bool(last) and last[0].isupper()
