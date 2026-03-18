from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFileSystemModel, QHBoxLayout, QLabel, QMenu, QPushButton, QTreeView, QVBoxLayout, QWidget


class ModuleBrowserPanel(QWidget):
    open_file_requested = pyqtSignal(str)
    create_module_requested = pyqtSignal(str)
    create_file_requested = pyqtSignal(str)
    rename_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel('Módulos Mint')
        title.setObjectName('WorkbenchTitle')
        subtitle = QLabel('Organize módulos ERP reutilizáveis com pastas e arquivos .mint.')
        subtitle.setObjectName('WorkbenchSubtitle')
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch(1)
        self.new_module_btn = QPushButton('Novo módulo')
        self.new_file_btn = QPushButton('Novo arquivo .mint')
        top.addWidget(self.new_module_btn)
        top.addWidget(self.new_file_btn)
        root.addLayout(top)

        self.model = QFileSystemModel(self)
        self.model.setRootPath(str(Path.cwd()))
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.doubleClicked.connect(self._on_double_click)
        self.tree.customContextMenuRequested.connect(self._on_context)
        for idx in [1, 2, 3]:
            self.tree.hideColumn(idx)
        root.addWidget(self.tree)

        self.new_module_btn.clicked.connect(lambda: self.create_module_requested.emit(self.current_folder()))
        self.new_file_btn.clicked.connect(lambda: self.create_file_requested.emit(self.current_folder()))

    def set_root_path(self, path: str) -> None:
        index = self.model.setRootPath(path)
        self.tree.setRootIndex(index)

    def current_folder(self) -> str:
        index = self.tree.currentIndex()
        if index.isValid():
            path = Path(self.model.filePath(index))
            return str(path if path.is_dir() else path.parent)
        return self.model.rootPath()

    def _on_double_click(self, index) -> None:
        path = Path(self.model.filePath(index))
        if path.is_file() and path.suffix.lower() == '.mint':
            self.open_file_requested.emit(str(path))

    def _on_context(self, pos) -> None:
        index = self.tree.indexAt(pos)
        path = self.model.filePath(index) if index.isValid() else self.model.rootPath()
        menu = QMenu(self)
        menu.addAction('Novo módulo', lambda: self.create_module_requested.emit(str(path)))
        menu.addAction('Novo arquivo .mint', lambda: self.create_file_requested.emit(str(path)))
        menu.addSeparator()
        menu.addAction('Renomear', lambda: self.rename_requested.emit(str(path)))
        menu.addAction('Excluir', lambda: self.delete_requested.emit(str(path)))
        menu.exec_(self.tree.viewport().mapToGlobal(pos))
