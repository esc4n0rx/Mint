from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QLabel


class ErpNavigationPanel(QWidget):
    object_requested = pyqtSignal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel('ERP Workbench')
        title.setObjectName('PanelTitle')
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._emit_request)
        layout.addWidget(title)
        layout.addWidget(self.tree)
        self.populate()

    def populate(self) -> None:
        self.tree.clear()
        projeto = QTreeWidgetItem(['Projeto'])
        for key, label in [
            ('tables', 'Tabelas'),
            ('modules', 'Módulos'),
            ('programs', 'Programas'),
            ('executions', 'Execuções'),
            ('structures', 'Estruturas futuras'),
        ]:
            child = QTreeWidgetItem([label])
            child.setData(0, Qt.UserRole, ('section', key))
            projeto.addChild(child)

        sistema = QTreeWidgetItem(['Sistema'])
        for key, label in [('logs', 'Logs'), ('settings', 'Configurações'), ('environment', 'Ambiente')]:
            child = QTreeWidgetItem([label])
            child.setData(0, Qt.UserRole, ('section', key))
            sistema.addChild(child)

        ajuda = QTreeWidgetItem(['Ajuda'])
        for key, label in [('syntax', 'Sintaxe Mint'), ('types', 'Tipos'), ('commands', 'Comandos'), ('examples', 'Exemplos')]:
            child = QTreeWidgetItem([label])
            child.setData(0, Qt.UserRole, ('section', key))
            ajuda.addChild(child)

        self.tree.addTopLevelItems([projeto, sistema, ajuda])
        self.tree.expandAll()

    def _emit_request(self, item: QTreeWidgetItem) -> None:
        payload = item.data(0, Qt.UserRole)
        if payload:
            self.object_requested.emit(payload[0], payload[1])
