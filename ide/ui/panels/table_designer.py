from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ide.models.table_definition import FieldDefinition, SUPPORTED_FIELD_TYPES, TableDefinition


class TableDesignerPanel(QWidget):
    save_requested = pyqtSignal(TableDefinition)
    generate_requested = pyqtSignal(TableDefinition)
    delete_requested = pyqtSignal(str)

    HEADERS = ['Campo', 'Descrição', 'Tipo', 'Tam.', 'Esc.', 'Obrig.', 'PK', 'Default', 'Observação']

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.current_name = ''
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header = QHBoxLayout()
        self.title = QLabel('Modelador de Tabelas')
        self.title.setObjectName('WorkbenchTitle')
        self.subtitle = QLabel('Defina metadados técnicos e estrutura de campos em padrão ERP.')
        self.subtitle.setObjectName('WorkbenchSubtitle')
        header_left = QVBoxLayout()
        header_left.addWidget(self.title)
        header_left.addWidget(self.subtitle)
        header.addLayout(header_left)
        header.addStretch(1)
        self.new_btn = QPushButton('Nova tabela')
        self.save_btn = QPushButton('Salvar definição')
        self.generate_btn = QPushButton('Gerar Mint')
        self.delete_btn = QPushButton('Excluir')
        for btn in [self.new_btn, self.save_btn, self.generate_btn, self.delete_btn]:
            header.addWidget(btn)
        root.addLayout(header)

        splitter = QSplitter(Qt.Vertical)

        top = QWidget()
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)

        form_box = QGroupBox('Cabeçalho técnico')
        form = QFormLayout(form_box)
        self.name_edit = QLineEdit()
        self.description_edit = QLineEdit()
        self.module_edit = QLineEdit('core')
        form.addRow('Nome técnico', self.name_edit)
        form.addRow('Descrição', self.description_edit)
        form.addRow('Módulo ERP', self.module_edit)

        summary_box = QGroupBox('Resumo estrutural')
        summary_layout = QVBoxLayout(summary_box)
        self.summary_label = QLabel('Nenhuma tabela carregada.')
        self.summary_label.setWordWrap(True)
        self.generated_path = QLabel('-')
        self.generated_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        summary_layout.addWidget(self.summary_label)
        summary_layout.addWidget(QLabel('Artefato Mint gerado:'))
        summary_layout.addWidget(self.generated_path)
        summary_layout.addStretch(1)

        top_layout.addWidget(form_box, 3)
        top_layout.addWidget(summary_box, 2)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        fields_header = QHBoxLayout()
        fields_header.addWidget(QLabel('Grid de campos'))
        self.add_row_btn = QPushButton('Adicionar campo')
        self.remove_row_btn = QPushButton('Remover linha')
        fields_header.addStretch(1)
        fields_header.addWidget(self.add_row_btn)
        fields_header.addWidget(self.remove_row_btn)
        bottom_layout.addLayout(fields_header)
        self.fields_table = QTableWidget(0, len(self.HEADERS))
        self.fields_table.setHorizontalHeaderLabels(self.HEADERS)
        self.fields_table.horizontalHeader().setStretchLastSection(True)
        self.fields_table.verticalHeader().setVisible(False)
        bottom_layout.addWidget(self.fields_table)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText('Notas de modelagem, constraints futuras, observações de integração...')
        bottom_layout.addWidget(QLabel('Notas da tabela'))
        bottom_layout.addWidget(self.notes)

        splitter.addWidget(top)
        splitter.addWidget(bottom)
        splitter.setSizes([180, 420])
        root.addWidget(splitter)

        self.new_btn.clicked.connect(self.clear_form)
        self.add_row_btn.clicked.connect(lambda: self._append_field())
        self.remove_row_btn.clicked.connect(self._remove_selected_field)
        self.save_btn.clicked.connect(self._emit_save)
        self.generate_btn.clicked.connect(self._emit_generate)
        self.delete_btn.clicked.connect(self._emit_delete)

        self.clear_form()

    def clear_form(self) -> None:
        self.current_name = ''
        self.name_edit.clear()
        self.description_edit.clear()
        self.module_edit.setText('core')
        self.notes.clear()
        self.generated_path.setText('-')
        self.fields_table.setRowCount(0)
        self._append_field(primary_key=True)
        self._refresh_summary()

    def load_definition(self, definition: TableDefinition) -> None:
        self.current_name = definition.name
        self.name_edit.setText(definition.name)
        self.description_edit.setText(definition.description)
        self.module_edit.setText(definition.module)
        self.generated_path.setText(definition.generated_code_path or '-')
        self.notes.setPlainText('\n'.join(field.notes for field in definition.fields if field.notes))
        self.fields_table.setRowCount(0)
        for field in definition.fields:
            self._append_field(field)
        self._refresh_summary()

    def collect_definition(self) -> TableDefinition | None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Tabela', 'Informe o nome técnico da tabela.')
            return None
        fields: list[FieldDefinition] = []
        for row in range(self.fields_table.rowCount()):
            name_item = self.fields_table.item(row, 0)
            if not name_item or not name_item.text().strip():
                continue
            fields.append(
                FieldDefinition(
                    name=name_item.text().strip(),
                    description=(self.fields_table.item(row, 1).text() if self.fields_table.item(row, 1) else ''),
                    field_type=self._combo_value(row, 2),
                    length=(self.fields_table.item(row, 3).text() if self.fields_table.item(row, 3) else ''),
                    scale=(self.fields_table.item(row, 4).text() if self.fields_table.item(row, 4) else ''),
                    required=self._checkbox_value(row, 5),
                    primary_key=self._checkbox_value(row, 6),
                    default_value=(self.fields_table.item(row, 7).text() if self.fields_table.item(row, 7) else ''),
                    notes=(self.fields_table.item(row, 8).text() if self.fields_table.item(row, 8) else ''),
                )
            )
        if not fields:
            QMessageBox.warning(self, 'Tabela', 'Adicione ao menos um campo à tabela.')
            return None
        definition = TableDefinition(
            name=name,
            description=self.description_edit.text().strip(),
            module=self.module_edit.text().strip() or 'core',
            fields=fields,
            generated_code_path='' if self.generated_path.text() == '-' else self.generated_path.text(),
        )
        self._refresh_summary(definition)
        return definition

    def _append_field(self, field: FieldDefinition | None = None, primary_key: bool = False) -> None:
        row = self.fields_table.rowCount()
        self.fields_table.insertRow(row)
        field = field or FieldDefinition(primary_key=primary_key, required=primary_key)
        for col, value in enumerate([
            field.name,
            field.description,
            None,
            field.length,
            field.scale,
            None,
            None,
            field.default_value,
            field.notes,
        ]):
            if value is None:
                continue
            self.fields_table.setItem(row, col, QTableWidgetItem(str(value)))
        combo = QComboBox()
        combo.addItems(SUPPORTED_FIELD_TYPES)
        combo.setCurrentText(field.field_type or 'string')
        self.fields_table.setCellWidget(row, 2, combo)
        for col, checked in [(5, field.required), (6, field.primary_key)]:
            checkbox = QCheckBox()
            checkbox.setChecked(checked)
            checkbox.setStyleSheet('margin-left:18px;')
            self.fields_table.setCellWidget(row, col, checkbox)

    def _remove_selected_field(self) -> None:
        row = self.fields_table.currentRow()
        if row >= 0:
            self.fields_table.removeRow(row)

    def _combo_value(self, row: int, col: int) -> str:
        combo = self.fields_table.cellWidget(row, col)
        return combo.currentText() if isinstance(combo, QComboBox) else 'string'

    def _checkbox_value(self, row: int, col: int) -> bool:
        checkbox = self.fields_table.cellWidget(row, col)
        return checkbox.isChecked() if isinstance(checkbox, QCheckBox) else False

    def _refresh_summary(self, definition: TableDefinition | None = None) -> None:
        definition = definition or TableDefinition(
            name=self.name_edit.text().strip() or 'nova_tabela',
            description=self.description_edit.text().strip(),
            module=self.module_edit.text().strip() or 'core',
            fields=[],
        )
        self.summary_label.setText(
            f"Tabela <b>{definition.name}</b> no módulo <b>{definition.module}</b>.<br>"
            f"Descrição: {definition.description or 'Sem descrição'}"
        )

    def _emit_save(self) -> None:
        definition = self.collect_definition()
        if definition:
            self.save_requested.emit(definition)

    def _emit_generate(self) -> None:
        definition = self.collect_definition()
        if definition:
            self.generate_requested.emit(definition)

    def _emit_delete(self) -> None:
        name = self.name_edit.text().strip()
        if name:
            self.delete_requested.emit(name)
