from __future__ import annotations

import sys

from PyQt5.QtWidgets import QApplication

from ide.ui.main_window import MainWindow


def create_app(argv=None) -> QApplication:
    app = QApplication(argv or sys.argv)
    app.setApplicationName("Mint IDE")
    app.setOrganizationName("MintLang")
    return app


def run() -> int:
    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec_()
