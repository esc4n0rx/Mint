from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFileSystemModel, QMenu, QTreeView, QWidget, QVBoxLayout


class FileExplorer(QWidget):
    open_file_requested = pyqtSignal(str)
    create_file_requested = pyqtSignal(str)
    create_folder_requested = pyqtSignal(str)
    rename_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = QFileSystemModel(self)
        self.model.setRootPath("")
        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.view.doubleClicked.connect(self._on_double_click)
        self.view.customContextMenuRequested.connect(self._on_context_menu)

    def set_root_path(self, path: str) -> None:
        idx = self.model.index(path)
        self.view.setRootIndex(idx)

    def _on_double_click(self, index):
        path = self.model.filePath(index)
        if Path(path).is_file():
            self.open_file_requested.emit(path)

    def _on_context_menu(self, pos):
        index = self.view.indexAt(pos)
        path = self.model.filePath(index) if index.isValid() else self.model.rootPath()
        menu = QMenu(self)
        menu.addAction("Novo arquivo", lambda: self.create_file_requested.emit(path))
        menu.addAction("Nova pasta", lambda: self.create_folder_requested.emit(path))
        menu.addAction("Renomear", lambda: self.rename_requested.emit(path))
        menu.addAction("Excluir", lambda: self.delete_requested.emit(path))
        menu.exec_(self.view.viewport().mapToGlobal(pos))
