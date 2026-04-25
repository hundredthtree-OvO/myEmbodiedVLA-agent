from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TextIO


STAGES = [
    "Resolving inputs",
    "Querying Zotero",
    "Extracting PDF text",
    "Preparing repo",
    "Building evidence pack",
    "Calling Codex",
    "Saving session",
    "Done",
]


class ProgressSink:
    def stage(self, name: str, detail: str = "") -> None:
        pass

    def info(self, message: str) -> None:
        pass

    def output(self, text: str) -> None:
        pass


class NullProgress(ProgressSink):
    pass


@dataclass
class TerminalProgress(ProgressSink):
    stream: TextIO = sys.stdout
    _output_started: bool = field(default=False, init=False)

    def stage(self, name: str, detail: str = "") -> None:
        suffix = f" - {detail}" if detail else ""
        self.stream.write(f"\n[{name}]{suffix}\n")
        self.stream.flush()

    def info(self, message: str) -> None:
        self.stream.write(f"{message}\n")
        self.stream.flush()

    def output(self, text: str) -> None:
        if not text:
            return
        if not self._output_started:
            self.stream.write("\n--- assistant output ---\n")
            self._output_started = True
        self.stream.write(text)
        self.stream.flush()
