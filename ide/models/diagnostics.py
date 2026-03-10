from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Diagnostic:
    severity: str
    message: str
    file_path: str = ""
    line: int = 0
    column: int = 0
