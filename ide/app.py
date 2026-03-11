from __future__ import annotations

import sys

from PyQt5.QtWidgets import QApplication

from ide.core.settings_manager import SettingsManager
from ide.core.theme_manager import ThemeManager
from ide.ui.main_window import MainWindow


def create_app(argv=None) -> QApplication:
    app = QApplication(argv or sys.argv)
    app.setApplicationName("Mint IDE")
    app.setOrganizationName("MintLang")

    settings = SettingsManager()
    selected_theme = settings.load_all().get("theme", "dark")
    ThemeManager().apply(app, selected_theme)
    return app


def run() -> int:
    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec_()
