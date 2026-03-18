from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionRequest:
    target_path: str
    mode: str = "program"
    function_name: str = ""
    parameters: list[str] = field(default_factory=list)
    workspace: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_path": self.target_path,
            "mode": self.mode,
            "function_name": self.function_name,
            "parameters": list(self.parameters),
            "workspace": self.workspace,
        }


@dataclass
class ExecutionRecord:
    timestamp: str
    target_path: str
    mode: str
    parameters: list[str] = field(default_factory=list)
    exit_code: int | None = None
    status: str = "pending"
    output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
