from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import QApplication

from ide.core.constants import DEFAULT_THEME


class ThemeManager:
    def __init__(self, assets_dir: Path | None = None) -> None:
        self.assets_dir = assets_dir or Path(__file__).resolve().parents[1] / "assets" / "themes"
        self._themes = {
            "dark": self.assets_dir / "dark.qss",
        }

    def available_themes(self) -> list[str]:
        return sorted(self._themes.keys())

    def apply(self, app: QApplication, theme_name: str | None = None) -> str:
        selected = theme_name or DEFAULT_THEME
        qss_path = self._themes.get(selected, self._themes[DEFAULT_THEME])
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        return selected
