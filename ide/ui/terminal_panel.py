from __future__ import annotations

from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QPlainTextEdit


class TerminalPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Comando shell (workspace)")
        self.run_btn = QPushButton("Run")
        self.clear_btn = QPushButton("Clear")

        controls = QHBoxLayout()
        controls.addWidget(self.input)
        controls.addWidget(self.run_btn)
        controls.addWidget(self.clear_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.output)
        layout.addLayout(controls)

        self._process = QProcess(self)
        self._process.readyReadStandardOutput.connect(self._stdout)
        self._process.readyReadStandardError.connect(self._stderr)

        self.run_btn.clicked.connect(self.run_command)
        self.input.returnPressed.connect(self.run_command)
        self.clear_btn.clicked.connect(self.output.clear)

    def run_command(self) -> None:
        cmd = self.input.text().strip()
        if not cmd:
            return
        self.output.appendPlainText(f"$ {cmd}")
        self._process.start("bash", ["-lc", cmd])

    def _stdout(self):
        self.output.appendPlainText(bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace"))

    def _stderr(self):
        self.output.appendPlainText(bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace"))

    def append_text(self, text: str) -> None:
        self.output.appendPlainText(text.rstrip())
