from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QDir, Qt, pyqtSignal
from PyQt5.QtWidgets import QFileSystemModel, QMenu, QTreeView, QWidget, QVBoxLayout


class FileExplorer(QWidget):
    open_file_requested = pyqtSignal(str)
    create_file_requested = pyqtSignal(str)
    create_folder_requested = pyqtSignal(str)
    rename_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root_path = str(Path.cwd())

        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.model.setOption(QFileSystemModel.DontUseCustomDirectoryIcons, True)
        initial_index = self.model.setRootPath(self._root_path)

        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.setRootIndex(initial_index)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.setAnimated(False)
        self.view.setUniformRowHeights(True)
        self.view.setSortingEnabled(False)
        self.view.setHeaderHidden(False)

        # Exibe só a coluna de nome para reduzir custo de layout/render
        self.view.hideColumn(1)
        self.view.hideColumn(2)
        self.view.hideColumn(3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.view.doubleClicked.connect(self._on_double_click)
        self.view.customContextMenuRequested.connect(self._on_context_menu)

    def set_root_path(self, path: str) -> None:
        self._root_path = path
        idx = self.model.setRootPath(path)
        self.view.setRootIndex(idx)

    def _on_double_click(self, index):
        path = self.model.filePath(index)
        if Path(path).is_file():
            self.open_file_requested.emit(path)

    def _resolve_context_path(self, index) -> str:
        if index.isValid():
            return self.model.filePath(index)

        root_idx = self.view.rootIndex()
        if root_idx.isValid():
            return self.model.filePath(root_idx)
        return self._root_path

    def _on_context_menu(self, pos):
        index = self.view.indexAt(pos)
        path = self._resolve_context_path(index)

        menu = QMenu(self)
        menu.addAction("Novo arquivo", lambda: self.create_file_requested.emit(path))
        menu.addAction("Nova pasta", lambda: self.create_folder_requested.emit(path))
        menu.addSeparator()
        menu.addAction("Renomear", lambda: self.rename_requested.emit(path))
        menu.addAction("Excluir", lambda: self.delete_requested.emit(path))
        menu.exec_(self.view.viewport().mapToGlobal(pos))
