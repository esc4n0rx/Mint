from __future__ import annotations

from typing import Any, Dict, List
from PyQt5.QtCore import QSettings

from .constants import (
    APP_NAME,
    APP_ORG,
    APP_DOMAIN,
    DEFAULT_THEME,
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    DEFAULT_TAB_SIZE,
    DEFAULT_USE_SPACES,
    DEFAULT_AUTO_LINT_ON_SAVE,
)


class SettingsManager:
    def __init__(self) -> None:
        self._settings = QSettings(APP_ORG, APP_NAME)
        self._settings.setFallbacksEnabled(True)
        self._settings.setValue("app/domain", APP_DOMAIN)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.value(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings.setValue(key, value)

    def sync(self) -> None:
        self._settings.sync()

    def load_all(self) -> Dict[str, Any]:
        return {
            "last_workspace": self.get("workspace/last_path", ""),
            "recent_files": self._ensure_list(self.get("files/recent", [])),
            "open_tabs": self._ensure_list(self.get("session/open_tabs", [])),
            "theme": self.get("editor/theme", DEFAULT_THEME),
            "font_family": self.get("editor/font_family", DEFAULT_FONT_FAMILY),
            "font_size": int(self.get("editor/font_size", DEFAULT_FONT_SIZE)),
            "tab_size": int(self.get("editor/tab_size", DEFAULT_TAB_SIZE)),
            "use_spaces": self._to_bool(self.get("editor/use_spaces", DEFAULT_USE_SPACES)),
            "auto_lint_on_save": self._to_bool(self.get("lint/auto_on_save", DEFAULT_AUTO_LINT_ON_SAVE)),
            "runtime_path": self.get("mint/runtime_path", ""),
            "linter_path": self.get("mint/linter_path", ""),
        }

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes"}

    @staticmethod
    def _ensure_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value if v]
        if isinstance(value, str):
            return [value] if value else []
        return []
