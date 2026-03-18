from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
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

from ide.models.execution_request import ExecutionRecord, ExecutionRequest, FunctionParameter


class ExecutionPanel(QWidget):
    execute_requested = pyqtSignal(ExecutionRequest)
    target_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel('Centro de Execução')
        title.setObjectName('WorkbenchTitle')
        subtitle = QLabel('Execute programas inteiros ou funções específicas com parâmetros tipados.')
        subtitle.setObjectName('WorkbenchSubtitle')
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch(1)
        self.execute_btn = QPushButton('Executar agora')
        top.addWidget(self.execute_btn)
        root.addLayout(top)

        config_box = QGroupBox('Configuração da execução')
        config_form = QFormLayout(config_box)
        self.target_path = QLineEdit()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['program', 'function'])
        self.function_name = QComboBox()
        self.function_name.setEnabled(False)
        config_form.addRow('Arquivo/programa', self.target_path)
        config_form.addRow('Modo', self.mode_combo)
        config_form.addRow('Função', self.function_name)
        root.addWidget(config_box)

        self.parameters_table = QTableWidget(0, 3)
        self.parameters_table.setHorizontalHeaderLabels(['Parâmetro', 'Tipo', 'Valor'])
        self.parameters_table.horizontalHeader().setStretchLastSection(True)
        self.parameters_table.verticalHeader().setVisible(False)
        self.parameters_table.setMinimumHeight(180)
        root.addWidget(QLabel('Parâmetros dinâmicos'))
        root.addWidget(self.parameters_table)

        self.history = QTableWidget(0, 5)
        self.history.setHorizontalHeaderLabels(['Data', 'Objeto', 'Modo', 'Parâmetros', 'Status'])
        self.history.horizontalHeader().setStretchLastSection(True)
        root.addWidget(QLabel('Histórico'))
        root.addWidget(self.history)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        root.addWidget(QLabel('Resultado / output'))
        root.addWidget(self.output, 1)

        self.execute_btn.clicked.connect(self._emit_execute)
        self.target_path.editingFinished.connect(lambda: self.target_changed.emit(self.target_path.text().strip()))
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.function_name.currentIndexChanged.connect(self._load_selected_function)

    def _on_mode_changed(self, mode: str) -> None:
        self.function_name.setEnabled(mode == 'function')
        if mode != 'function':
            self.parameters_table.setRowCount(0)

    def set_target_path(self, path: str) -> None:
        self.target_path.setText(path)
        self.target_changed.emit(path)

    def set_functions(self, functions: list[tuple[str, list[FunctionParameter], str | None]]) -> None:
        current = self.function_name.currentText()
        self.function_name.blockSignals(True)
        self.function_name.clear()
        self.function_name.addItem('')
        for name, params, return_type in functions:
            label = name if not return_type else f'{name} -> {return_type}'
            self.function_name.addItem(label, (name, params, return_type))
        index = self.function_name.findText(current)
        self.function_name.setCurrentIndex(index if index >= 0 else 0)
        self.function_name.blockSignals(False)
        self._load_selected_function(self.function_name.currentIndex())

    def _load_selected_function(self, index: int) -> None:
        payload = self.function_name.itemData(index)
        params = payload[1] if payload else []
        self.set_parameters(params)

    def set_parameters(self, params: list[FunctionParameter]) -> None:
        self.parameters_table.setRowCount(0)
        for param in params:
            row = self.parameters_table.rowCount()
            self.parameters_table.insertRow(row)
            self.parameters_table.setItem(row, 0, QTableWidgetItem(param.name))
            self.parameters_table.setItem(row, 1, QTableWidgetItem(param.param_type))
            self.parameters_table.setItem(row, 2, QTableWidgetItem(param.value))

    def _emit_execute(self) -> None:
        mode = self.mode_combo.currentText()
        function_name = ''
        if mode == 'function':
            payload = self.function_name.currentData()
            function_name = payload[0] if payload else ''
        parameters = []
        for row in range(self.parameters_table.rowCount()):
            item = self.parameters_table.item(row, 2)
            parameters.append(item.text().strip() if item else '')
        request = ExecutionRequest(
            target_path=self.target_path.text().strip(),
            mode=mode,
            function_name=function_name,
            parameters=parameters,
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
