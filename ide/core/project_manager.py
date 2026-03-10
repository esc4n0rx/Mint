from __future__ import annotations

from pathlib import Path
from typing import List

from .settings_manager import SettingsManager


class ProjectManager:
    def __init__(self, settings: SettingsManager) -> None:
        self.settings = settings

    def add_recent_file(self, file_path: str) -> None:
        path = str(Path(file_path).resolve())
        recent: List[str] = self.settings.load_all()["recent_files"]
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.settings.set("files/recent", recent[:15])

    def set_last_workspace(self, workspace_path: str) -> None:
        self.settings.set("workspace/last_path", str(Path(workspace_path).resolve()))

    def get_recent_files(self) -> List[str]:
        return self.settings.load_all()["recent_files"]
