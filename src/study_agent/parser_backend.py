from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .repo.code_parser import ParsedCodeFile, PythonAstCodeParser


@dataclass(frozen=True)
class ParserResult:
    path: str
    language: str
    parsed: ParsedCodeFile


class ParserBackend(Protocol):
    backend_name: str

    def supports_path(self, path: Path) -> bool: ...

    def parse_file(self, path: Path, text: str) -> ParserResult: ...


def detect_language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".js", ".jsx"}:
        return "javascript"
    if suffix in {".ts", ".tsx"}:
        return "typescript"
    if suffix in {".rs"}:
        return "rust"
    if suffix in {".cpp", ".cc", ".cxx", ".hpp", ".h"}:
        return "cpp"
    if suffix in {".java"}:
        return "java"
    if suffix in {".json", ".yaml", ".yml", ".toml", ".ini"}:
        return "config"
    if suffix in {".md", ".rst", ".txt"}:
        return "text"
    return "text"


class PythonAstBackend:
    backend_name = "python-ast"

    def __init__(self) -> None:
        self._parser = PythonAstCodeParser()

    def supports_path(self, path: Path) -> bool:
        return detect_language(path) == "python"

    def parse_file(self, path: Path, text: str) -> ParserResult:
        parsed = self._parser.parse_file(path, text)
        return ParserResult(path=path.as_posix(), language="python", parsed=parsed)


class TextFallbackBackend:
    backend_name = "text-fallback"

    def supports_path(self, path: Path) -> bool:
        return True

    def parse_file(self, path: Path, text: str) -> ParserResult:
        language = detect_language(path)
        parsed = ParsedCodeFile(
            path=path.as_posix(),
            language=language,
            symbols=[],
            imports=[],
            relations=[],
        )
        return ParserResult(path=path.as_posix(), language=language, parsed=parsed)


class CompositeParserBackend:
    backend_name = "python-ast+text-fallback"

    def __init__(self) -> None:
        self.backends: list[ParserBackend] = [
            PythonAstBackend(),
            TextFallbackBackend(),
        ]

    def parse_file(self, path: Path, text: str) -> ParserResult:
        for backend in self.backends:
            if backend.supports_path(path):
                return backend.parse_file(path, text)
        return TextFallbackBackend().parse_file(path, text)
