from __future__ import annotations

from PyQt5.QtGui import QColor, QTextCharFormat
from PyQt5.QtWidgets import QPlainTextEdit


class OutputPanel(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

    def append_info(self, text: str) -> None:
        self.appendPlainText(text.rstrip("\n"))

    def append_error(self, text: str) -> None:
        self.appendPlainText(f"[erro] {text.rstrip()}" )

    def clear_output(self) -> None:
        self.clear()
