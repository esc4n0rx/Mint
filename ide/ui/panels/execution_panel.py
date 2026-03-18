from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ide.models.execution_request import ExecutionRecord, ExecutionRequest


class ExecutionPanel(QWidget):
    execute_requested = pyqtSignal(ExecutionRequest)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel('Centro de Execução')
        title.setObjectName('WorkbenchTitle')
        subtitle = QLabel('Execute programas Mint e registre parâmetros, status e saída.')
        subtitle.setObjectName('WorkbenchSubtitle')
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch(1)
        self.execute_btn = QPushButton('Executar')
        top.addWidget(self.execute_btn)
        root.addLayout(top)

        form_box = QGroupBox('Requisição de execução')
        form = QFormLayout(form_box)
        self.target_path = QLineEdit()
        self.function_name = QLineEdit()
        self.parameters = QLineEdit()
        form.addRow('Arquivo/programa', self.target_path)
        form.addRow('Função (futuro)', self.function_name)
        form.addRow('Parâmetros', self.parameters)
        root.addWidget(form_box)

        self.history = QTableWidget(0, 5)
        self.history.setHorizontalHeaderLabels(['Data', 'Objeto', 'Modo', 'Parâmetros', 'Status'])
        self.history.horizontalHeader().setStretchLastSection(True)
        root.addWidget(QLabel('Histórico'))
        root.addWidget(self.history)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        root.addWidget(QLabel('Output estruturado'))
        root.addWidget(self.output)

        self.execute_btn.clicked.connect(self._emit_execute)

    def _emit_execute(self) -> None:
        request = ExecutionRequest(
            target_path=self.target_path.text().strip(),
            mode='program' if not self.function_name.text().strip() else 'function',
            function_name=self.function_name.text().strip(),
            parameters=[part.strip() for part in self.parameters.text().split(',') if part.strip()],
        )
        self.execute_requested.emit(request)

    def set_history(self, entries: list[ExecutionRecord]) -> None:
        self.history.setRowCount(0)
        for entry in entries:
            row = self.history.rowCount()
            self.history.insertRow(row)
            for col, value in enumerate([
                entry.timestamp,
                entry.target_path,
                entry.mode,
                ', '.join(entry.parameters),
                entry.status,
            ]):
                self.history.setItem(row, col, QTableWidgetItem(str(value)))

    def append_output(self, text: str) -> None:
        self.output.append(text.rstrip())
