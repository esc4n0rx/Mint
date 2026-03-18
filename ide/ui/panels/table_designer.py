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

    SUMMARY_HEADERS = ['Campo', 'Tipo', 'Obrig.', 'PK']

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._syncing = False
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title = QLabel('Modelador de Tabelas')
        self.title.setObjectName('WorkbenchTitle')
        self.subtitle = QLabel('Estruture a tabela em blocos legíveis: cabeçalho, lista de campos e detalhe do campo.')
        self.subtitle.setObjectName('WorkbenchSubtitle')
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        header.addLayout(title_box)
        header.addStretch(1)
        self.new_btn = QPushButton('Nova tabela')
        self.save_btn = QPushButton('Salvar definição')
        self.generate_btn = QPushButton('Gerar Mint')
        self.delete_btn = QPushButton('Excluir')
        for btn in [self.new_btn, self.save_btn, self.generate_btn, self.delete_btn]:
            header.addWidget(btn)
        root.addLayout(header)

        top_split = QSplitter(Qt.Horizontal)
        top_split.addWidget(self._build_header_box())
        top_split.addWidget(self._build_summary_box())
        top_split.setSizes([720, 420])
        root.addWidget(top_split)

        field_split = QSplitter(Qt.Horizontal)
        field_split.addWidget(self._build_fields_box())
        field_split.addWidget(self._build_field_detail_box())
        field_split.setSizes([640, 560])
        root.addWidget(field_split, 1)

        self.new_btn.clicked.connect(self.clear_form)
        self.add_row_btn.clicked.connect(self._append_field)
        self.remove_row_btn.clicked.connect(self._remove_selected_field)
        self.save_btn.clicked.connect(self._emit_save)
        self.generate_btn.clicked.connect(self._emit_generate)
        self.delete_btn.clicked.connect(self._emit_delete)
        self.fields_table.currentCellChanged.connect(self._load_selected_field)

        self._connect_detail_signals()
        self.clear_form()

    def _build_header_box(self) -> QWidget:
        box = QGroupBox('Cabeçalho técnico da tabela')
        form = QFormLayout(box)
        self.name_edit = QLineEdit()
        self.description_edit = QLineEdit()
        self.module_edit = QLineEdit('core')
        self.notes = QTextEdit()
        self.notes.setMinimumHeight(100)
        self.notes.setPlaceholderText('Contexto funcional, restrições, integração com MintDB, observações do objeto ERP...')
        form.addRow('Nome técnico', self.name_edit)
        form.addRow('Descrição', self.description_edit)
        form.addRow('Módulo ERP', self.module_edit)
        form.addRow('Notas da tabela', self.notes)
        return box

    def _build_summary_box(self) -> QWidget:
        box = QGroupBox('Resumo estrutural')
        layout = QVBoxLayout(box)
        self.summary_label = QLabel('Nenhuma tabela carregada.')
        self.summary_label.setWordWrap(True)
        self.generated_path = QLabel('-')
        self.generated_path.setWordWrap(True)
        self.generated_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.summary_label)
        layout.addWidget(QLabel('Artefato Mint gerado'))
        layout.addWidget(self.generated_path)
        layout.addStretch(1)
        return box

    def _build_fields_box(self) -> QWidget:
        box = QGroupBox('Campos da tabela')
        layout = QVBoxLayout(box)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel('Selecione um campo para editar os detalhes ao lado.'))
        toolbar.addStretch(1)
        self.add_row_btn = QPushButton('Adicionar campo')
        self.remove_row_btn = QPushButton('Remover campo')
        toolbar.addWidget(self.add_row_btn)
        toolbar.addWidget(self.remove_row_btn)
        layout.addLayout(toolbar)

        self.fields_table = QTableWidget(0, len(self.SUMMARY_HEADERS))
        self.fields_table.setHorizontalHeaderLabels(self.SUMMARY_HEADERS)
        self.fields_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.fields_table.setSelectionMode(QTableWidget.SingleSelection)
        self.fields_table.setWordWrap(True)
        self.fields_table.verticalHeader().setVisible(False)
        self.fields_table.verticalHeader().setDefaultSectionSize(42)
        header = self.fields_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(90)
        header.resizeSection(0, 220)
        header.resizeSection(1, 130)
        header.resizeSection(2, 90)
        header.resizeSection(3, 70)
        layout.addWidget(self.fields_table)
        return box

    def _build_field_detail_box(self) -> QWidget:
        box = QGroupBox('Detalhe do campo selecionado')
        form = QFormLayout(box)
        self.field_name_edit = QLineEdit()
        self.field_description_edit = QLineEdit()
        self.field_type_combo = QComboBox()
        self.field_type_combo.addItems(SUPPORTED_FIELD_TYPES)
        self.field_length_edit = QLineEdit()
        self.field_scale_edit = QLineEdit()
        self.field_required = QCheckBox('Obrigatório')
        self.field_primary = QCheckBox('Chave primária')
        self.field_default_edit = QLineEdit()
        self.field_notes_edit = QTextEdit()
        self.field_notes_edit.setMinimumHeight(120)

        form.addRow('Nome técnico', self.field_name_edit)
        form.addRow('Descrição', self.field_description_edit)
        form.addRow('Tipo', self.field_type_combo)
        form.addRow('Tamanho', self.field_length_edit)
        form.addRow('Precisão / escala', self.field_scale_edit)
        form.addRow(self.field_required)
        form.addRow(self.field_primary)
        form.addRow('Valor default', self.field_default_edit)
        form.addRow('Observações', self.field_notes_edit)
        return box

    def _connect_detail_signals(self) -> None:
        widgets = [
            self.field_name_edit,
            self.field_description_edit,
            self.field_length_edit,
            self.field_scale_edit,
            self.field_default_edit,
        ]
        for widget in widgets:
            widget.textChanged.connect(self._save_selected_field)
        self.field_notes_edit.textChanged.connect(self._save_selected_field)
        self.field_type_combo.currentTextChanged.connect(self._save_selected_field)
        self.field_required.toggled.connect(self._save_selected_field)
        self.field_primary.toggled.connect(self._save_selected_field)

    def clear_form(self) -> None:
        self.name_edit.clear()
        self.description_edit.clear()
        self.module_edit.setText('core')
        self.notes.clear()
        self.generated_path.setText('-')
        self.fields_table.setRowCount(0)
        self._append_field(primary_key=True)
        self._refresh_summary()

    def load_definition(self, definition: TableDefinition) -> None:
        self._syncing = True
        self.name_edit.setText(definition.name)
        self.description_edit.setText(definition.description)
        self.module_edit.setText(definition.module)
        self.notes.setPlainText('')
        self.generated_path.setText(definition.generated_code_path or '-')
        self.fields_table.setRowCount(0)
        for field in definition.fields:
            self._append_field(field)
        self._syncing = False
        if self.fields_table.rowCount():
            self.fields_table.selectRow(0)
            self._load_selected_field(0, 0, -1, -1)
        self._refresh_summary(definition)

    def collect_definition(self) -> TableDefinition | None:
        self._save_selected_field()
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Tabela', 'Informe o nome técnico da tabela.')
            return None
        fields = []
        for row in range(self.fields_table.rowCount()):
            field = self._field_from_row(row)
            if field and field.name.strip():
                fields.append(field)
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
        field = field or FieldDefinition(name='new_field', field_type='string', required=primary_key, primary_key=primary_key)
        row = self.fields_table.rowCount()
        self.fields_table.insertRow(row)
        self._store_field_in_row(row, field)
        if row == 0:
            self.fields_table.selectRow(0)
            self._load_selected_field(0, 0, -1, -1)

    def _remove_selected_field(self) -> None:
        row = self.fields_table.currentRow()
        if row >= 0:
            self.fields_table.removeRow(row)
            if self.fields_table.rowCount():
                self.fields_table.selectRow(max(0, row - 1))
                self._load_selected_field(self.fields_table.currentRow(), 0, -1, -1)
            else:
                self._set_detail_field(None)

    def _field_from_row(self, row: int) -> FieldDefinition | None:
        item = self.fields_table.item(row, 0)
        if item is None:
            return None
        data = item.data(Qt.UserRole)
        if isinstance(data, dict):
            return FieldDefinition.from_dict(data)
        return None

    def _store_field_in_row(self, row: int, field: FieldDefinition) -> None:
        values = [field.name, field.field_type, 'Sim' if field.required else 'Não', 'Sim' if field.primary_key else 'Não']
        for col, value in enumerate(values):
            item = self.fields_table.item(row, col)
            if item is None:
                item = QTableWidgetItem()
                self.fields_table.setItem(row, col, item)
            item.setText(value)
            if col == 0:
                item.setData(Qt.UserRole, field.to_dict())
        self._refresh_summary()

    def _load_selected_field(self, current_row: int, _current_col: int, _previous_row: int, _previous_col: int) -> None:
        field = self._field_from_row(current_row) if current_row >= 0 else None
        self._set_detail_field(field)

    def _set_detail_field(self, field: FieldDefinition | None) -> None:
        self._syncing = True
        if field is None:
            self.field_name_edit.clear()
            self.field_description_edit.clear()
            self.field_type_combo.setCurrentText('string')
            self.field_length_edit.clear()
            self.field_scale_edit.clear()
            self.field_required.setChecked(False)
            self.field_primary.setChecked(False)
            self.field_default_edit.clear()
            self.field_notes_edit.clear()
        else:
            self.field_name_edit.setText(field.name)
            self.field_description_edit.setText(field.description)
            self.field_type_combo.setCurrentText(field.field_type or 'string')
            self.field_length_edit.setText(field.length)
            self.field_scale_edit.setText(field.scale)
            self.field_required.setChecked(field.required)
            self.field_primary.setChecked(field.primary_key)
            self.field_default_edit.setText(field.default_value)
            self.field_notes_edit.setPlainText(field.notes)
        self._syncing = False

    def _save_selected_field(self) -> None:
        if self._syncing:
            return
        row = self.fields_table.currentRow()
        if row < 0:
            return
        field = FieldDefinition(
            name=self.field_name_edit.text().strip(),
            description=self.field_description_edit.text().strip(),
            field_type=self.field_type_combo.currentText(),
            length=self.field_length_edit.text().strip(),
            scale=self.field_scale_edit.text().strip(),
            required=self.field_required.isChecked(),
            primary_key=self.field_primary.isChecked(),
            default_value=self.field_default_edit.text().strip(),
            notes=self.field_notes_edit.toPlainText().strip(),
        )
        self._store_field_in_row(row, field)

    def _refresh_summary(self, definition: TableDefinition | None = None) -> None:
        fields_count = self.fields_table.rowCount()
        definition = definition or TableDefinition(
            name=self.name_edit.text().strip() or 'nova_tabela',
            description=self.description_edit.text().strip(),
            module=self.module_edit.text().strip() or 'core',
            fields=[],
        )
        self.summary_label.setText(
            f"Tabela <b>{definition.name}</b><br>"
            f"Módulo: <b>{definition.module}</b><br>"
            f"Descrição: {definition.description or 'Sem descrição'}<br>"
            f"Campos cadastrados: <b>{fields_count}</b>"
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
