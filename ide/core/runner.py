from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt5.QtCore import QObject, QProcess, pyqtSignal


class MintRunner(QObject):
    started = pyqtSignal(str)
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self._process = QProcess()
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)

    def is_running(self) -> bool:
        return self._process.state() != QProcess.NotRunning

    def run_file(self, file_path: str, cwd: str) -> None:
        if self.is_running():
            self.stop()
        self.started.emit(file_path)
        env = self._process.processEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        self._process.setProcessEnvironment(env)
        self._process.setProgram(sys.executable)
        self._process.setArguments(["-m", "mintlang.cli", "-file", str(Path(file_path))])
        self._process.setWorkingDirectory(cwd)
        self._process.start()

    def stop(self) -> None:
        if self.is_running():
            self._process.kill()

    def _on_stdout(self) -> None:
        data = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.output.emit(data)

    def _on_stderr(self) -> None:
        data = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
        if data:
            self.error.emit(data)

    def _on_finished(self, exit_code: int) -> None:
        self.finished.emit(exit_code)
