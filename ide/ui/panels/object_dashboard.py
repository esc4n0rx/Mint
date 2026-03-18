from __future__ import annotations

from PyQt5.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class ObjectDashboardPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        title = QLabel('Visão Geral do ERP Studio')
        title.setObjectName('WorkbenchTitle')
        subtitle = QLabel('Painel inicial com visão dos objetos do projeto, pronto para expansão futura.')
        subtitle.setObjectName('WorkbenchSubtitle')
        self.grid = QTableWidget(0, 3)
        self.grid.setHorizontalHeaderLabels(['Área', 'Objetos', 'Observações'])
        self.grid.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.grid)

    def set_rows(self, rows: list[tuple[str, str, str]]) -> None:
        self.grid.setRowCount(0)
        for area, count, notes in rows:
            row = self.grid.rowCount()
            self.grid.insertRow(row)
            for col, value in enumerate([area, count, notes]):
                self.grid.setItem(row, col, QTableWidgetItem(value))
