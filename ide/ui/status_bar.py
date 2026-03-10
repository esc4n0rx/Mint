from __future__ import annotations

from PyQt5.QtWidgets import QStatusBar, QLabel


class IdeStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_label = QLabel("Arquivo: -")
        self.pos_label = QLabel("Ln 1, Col 1")
        self.lang_label = QLabel("Mint")
        self.workspace_label = QLabel("Workspace: -")
        self.addPermanentWidget(self.file_label)
        self.addPermanentWidget(self.pos_label)
        self.addPermanentWidget(self.lang_label)
        self.addPermanentWidget(self.workspace_label)

    def set_file(self, file_path: str) -> None:
        self.file_label.setText(f"Arquivo: {file_path or '-'}")

    def set_cursor(self, line: int, col: int) -> None:
        self.pos_label.setText(f"Ln {line}, Col {col}")

    def set_workspace(self, ws: str) -> None:
        self.workspace_label.setText(f"Workspace: {ws or '-'}")
