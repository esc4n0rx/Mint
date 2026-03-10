from __future__ import annotations

from pathlib import Path
from typing import Optional


class WorkspaceManager:
    def __init__(self) -> None:
        self._workspace: Optional[Path] = None

    @property
    def current(self) -> Optional[Path]:
        return self._workspace

    def open_workspace(self, path: str) -> Path:
        workspace = Path(path).resolve()
        if not workspace.exists() or not workspace.is_dir():
            raise ValueError(f"Workspace inválido: {workspace}")
        self._workspace = workspace
        return workspace

    def close_workspace(self) -> None:
        self._workspace = None

    def base_dir_for(self, file_path: Optional[str]) -> Path:
        if self._workspace is not None:
            return self._workspace
        if file_path:
            return Path(file_path).resolve().parent
        return Path.cwd()
