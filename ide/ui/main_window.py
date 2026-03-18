from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ide.core.file_manager import FileManager
from ide.core.linter_bridge import LinterBridge
from ide.core.project_manager import ProjectManager
from ide.core.realtime_validator import RealtimeValidator
from ide.core.runner import MintRunner
from ide.core.settings_manager import SettingsManager
from ide.core.theme_manager import ThemeManager
from ide.core.workspace_manager import WorkspaceManager
from ide.models.diagnostics import Diagnostic
from ide.models.execution_request import ExecutionRecord, ExecutionRequest
from ide.models.table_definition import TableDefinition
from ide.services.execution_service import ExecutionService
from ide.services.module_service import ModuleService
from ide.services.table_service import TableService
from ide.services.workbench_service import WorkbenchService
from ide.ui.dialogs import SettingsDialog
from ide.ui.editor_tabs import EditorTabs
from ide.ui.panels.execution_panel import ExecutionPanel
from ide.ui.panels.help_panel import HelpPanel
from ide.ui.panels.module_browser import ModuleBrowserPanel
from ide.ui.panels.object_dashboard import ObjectDashboardPanel
from ide.ui.panels.table_designer import TableDesignerPanel
from ide.ui.status_bar import IdeStatusBar
from ide.ui.widgets.erp_navigation import ErpNavigationPanel


HELP_TOPICS = {
    'syntax': ('Sintaxe Mint', '<h3>Sintaxe Mint</h3><p>Use <b>program init.</b>, <b>initialization.</b> e <b>endprogram.</b> para programas executáveis.</p><p>Structs, funções, imports e comandos MintDB continuam disponíveis no estúdio.</p>'),
    'types': ('Tipos suportados', '<ul><li>int</li><li>float</li><li>string</li><li>char</li><li>bool</li><li>decimal</li><li>date</li><li>datetime</li><li>time</li><li>text</li><li>long</li><li>double</li><li>bytes</li><li>uuid</li><li>json</li></ul>'),
    'commands': ('Comandos', '<p>Destaques atuais: IMPORT, QUERY, LOAD, SAVE, EXPORT, FOR, TRY/CATCH, DB CREATE/OPEN, SHOW TABLES, DESCRIBE, INDEX CREATE, UPSERT, JOIN, ALTER TABLE.</p>'),
    'examples': ('Exemplos', '<p>Abra os exemplos em <code>modules/</code>, <code>programs/</code> e <code>.mint_workbench/tables/</code> para consultar artefatos reais do projeto.</p>'),
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Mint ERP Studio')
        self.resize(1560, 940)

        self.settings = SettingsManager()
        self.config = self.settings.load_all()
        self.workspace = WorkspaceManager()
        self.project = ProjectManager(self.settings)
        self.files = FileManager()
        self.linter = LinterBridge()
        self.realtime_validator = RealtimeValidator(self)
        self.runner = MintRunner()
        self._latest_validation_request = 0
        self._active_execution_record: ExecutionRecord | None = None
        self._execution_output_buffer: list[str] = []

        workspace_path = self._default_workspace()
        self.workbench = WorkbenchService(workspace_path)
        self.table_service = TableService(self.workbench)
        self.module_service = ModuleService(self.workbench)
        self.execution_service = ExecutionService(self.workbench)
        self.module_service.ensure_examples()
        self.table_service.ensure_example_table()
        self._ensure_example_programs()

        self.navigation = ErpNavigationPanel()
        self.navigation.object_requested.connect(self._handle_navigation)

        self.dashboard_panel = ObjectDashboardPanel()
        self.table_panel = TableDesignerPanel()
        self.module_panel = ModuleBrowserPanel()
        self.execution_panel = ExecutionPanel()
        self.help_panel = HelpPanel()

        self.table_list = QTableWidget(0, 4)
        self.table_list.setHorizontalHeaderLabels(['Tabela', 'Descrição', 'Módulo', 'Campos'])
        self.table_list.horizontalHeader().setStretchLastSection(True)
        self.table_list.cellDoubleClicked.connect(self._open_selected_table)

        self.editor_tabs = EditorTabs(self.config['tab_size'], self.config['use_spaces'])
        self.editor_tabs.file_changed.connect(self._on_file_modified)
        self.editor_tabs.cursor_changed.connect(self._on_cursor_changed)
        self.editor_tabs.currentChanged.connect(self._on_tab_changed)
        self.editor_tabs.tabCloseRequested.connect(self._close_tab)

        self.problems_table = QTableWidget(0, 6)
        self.problems_table.setHorizontalHeaderLabels(['Tipo', 'Mensagem', 'Arquivo', 'Linha', 'Coluna', 'Sugestão'])
        self.problems_table.cellDoubleClicked.connect(self._go_to_problem)
        self.problems_table.horizontalHeader().setStretchLastSection(True)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        self.detail_tabs = QTabWidget()
        self.detail_tabs.addTab(self.table_list, 'Catálogo de tabelas')
        self.detail_tabs.addTab(self.table_panel, 'Designer de tabela')
        self.detail_tabs.addTab(self.module_panel, 'Módulos ERP')
        self.detail_tabs.addTab(self.editor_tabs, 'Editor Mint')
        self.detail_tabs.addTab(self.execution_panel, 'Execução')
        self.detail_tabs.addTab(self.help_panel, 'Ajuda')

        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.addTab(self.problems_table, 'Diagnósticos')
        self.bottom_tabs.addTab(self.log_view, 'Logs do workbench')

        center_split = QSplitter(Qt.Vertical)
        center_split.addWidget(self.detail_tabs)
        center_split.addWidget(self.bottom_tabs)
        center_split.setSizes([760, 180])

        root_split = QSplitter(Qt.Horizontal)
        root_split.addWidget(self.navigation)
        root_split.addWidget(center_split)
        root_split.setSizes([280, 1280])

        dashboard_container = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_container)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_layout.addWidget(self.dashboard_panel)
        dashboard_layout.addWidget(root_split)
        dashboard_layout.setStretch(0, 0)
        dashboard_layout.setStretch(1, 1)
        self.setCentralWidget(dashboard_container)

        self.status = IdeStatusBar()
        self.setStatusBar(self.status)
        self.status.set_workspace(str(self.workbench.workspace))

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._wire_runner()
        self._wire_realtime_validator()
        self._wire_business_actions()
        self._apply_editor_font()
        self._restore_last_workspace()
        self._refresh_table_catalog()
        self._refresh_dashboard()
        self._refresh_execution_history()
        self.module_panel.set_root_path(str(self.workbench.modules_dir))
        self.help_panel.set_topic(*HELP_TOPICS['syntax'])
        self.log_view.setPlainText('Mint ERP Studio inicializado.\nUse a árvore à esquerda como navegação principal do workbench.')

    def _default_workspace(self) -> str:
        last = self.config.get('last_workspace')
        if last and Path(last).exists():
            return last
        return str(Path.cwd())

    def _ensure_example_programs(self) -> None:
        example = self.workbench.programs_dir / 'daily_close.mint'
        if not example.exists():
            example.write_text(
                'program init.\n'
                '  var process_name type string = "Daily close".\n'
                'initialization.\n'
                '  write(process_name).\n'
                'endprogram.\n',
                encoding='utf-8',
            )

    def _build_actions(self) -> None:
        self.act_new_module = QAction('Novo módulo', self, triggered=lambda: self._create_module(str(self.workbench.modules_dir)))
        self.act_new_table = QAction('Nova tabela', self, triggered=self.table_panel.clear_form)
        self.act_open_workspace = QAction('Abrir projeto', self, shortcut='Ctrl+Shift+O', triggered=self.open_workspace_dialog)
        self.act_open_file = QAction('Abrir .mint', self, shortcut='Ctrl+O', triggered=self.open_file_dialog)
        self.act_save = QAction('Salvar', self, shortcut='Ctrl+S', triggered=self.save_current)
        self.act_save_all = QAction('Salvar todos', self, triggered=self.save_all)
        self.act_run = QAction('Executar', self, shortcut='F5', triggered=self.run_current)
        self.act_lint = QAction('Validar', self, shortcut='F8', triggered=self.lint_current)
        self.act_settings = QAction('Configurações', self, triggered=self.open_settings)
        self.act_about = QAction('Sobre', self, triggered=self.about)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu('Projeto')
        file_menu.addActions([self.act_open_workspace, self.act_open_file, self.act_save, self.act_save_all])
        design_menu = self.menuBar().addMenu('Workbench')
        design_menu.addActions([self.act_new_table, self.act_new_module, self.act_run, self.act_lint])
        help_menu = self.menuBar().addMenu('Ajuda')
        help_menu.addActions([self.act_settings, self.act_about])

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar('Workbench')
        toolbar.setObjectName('WorkbenchToolbar')
        for action in [self.act_open_workspace, self.act_new_table, self.act_new_module, self.act_save, self.act_run, self.act_lint]:
            toolbar.addAction(action)

    def _wire_business_actions(self) -> None:
        self.table_panel.save_requested.connect(self._save_table_definition)
        self.table_panel.generate_requested.connect(self._generate_table_definition)
        self.table_panel.delete_requested.connect(self._delete_table_definition)
        self.module_panel.open_file_requested.connect(self.open_file)
        self.module_panel.create_module_requested.connect(self._create_module)
        self.module_panel.create_file_requested.connect(self._create_module_file)
        self.module_panel.rename_requested.connect(self._rename_path)
        self.module_panel.delete_requested.connect(self._delete_path)
        self.execution_panel.execute_requested.connect(self._execute_request)

    def _wire_runner(self) -> None:
        self.runner.started.connect(lambda p: self._append_log(f'[run] {p}'))
        self.runner.output.connect(self._handle_runner_output)
        self.runner.error.connect(lambda t: self._handle_runner_output(f'[stderr] {t}'))
        self.runner.finished.connect(self._handle_runner_finished)

    def _wire_realtime_validator(self) -> None:
        self.realtime_validator.diagnostics_ready.connect(self._on_realtime_diagnostics)

    def _restore_last_workspace(self) -> None:
        self._open_workspace(str(self.workbench.workspace))

    def _open_workspace(self, path: str) -> None:
        ws = self.workspace.open_workspace(path)
        self.status.set_workspace(str(ws))
        self.project.set_last_workspace(str(ws))
        self.workbench = WorkbenchService(ws)
        self.table_service = TableService(self.workbench)
        self.module_service = ModuleService(self.workbench)
        self.execution_service = ExecutionService(self.workbench)
        self.module_service.ensure_examples()
        self.table_service.ensure_example_table()
        self._ensure_example_programs()
        self.module_panel.set_root_path(str(self.workbench.modules_dir))
        self._refresh_table_catalog()
        self._refresh_dashboard()
        self._refresh_execution_history()

    def open_workspace_dialog(self) -> None:
        path = QFileDialog.getExistingDirectory(self, 'Abrir projeto', str(Path.cwd()))
        if path:
            self._open_workspace(path)

    def open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir arquivo Mint', str(self.workbench.workspace), 'Mint files (*.mint);;All files (*.*)')
        if path:
            self.open_file(path)

    def open_file(self, file_path: str) -> None:
        existing = self.editor_tabs.index_of_path(file_path)
        self.detail_tabs.setCurrentWidget(self.editor_tabs)
        if existing >= 0:
            self.editor_tabs.setCurrentIndex(existing)
            self.status.set_file(file_path)
            return
        try:
            content = self.files.read_text(file_path)
        except Exception as exc:
            QMessageBox.critical(self, 'Erro', f'Falha ao abrir arquivo: {exc}')
            return
        self.editor_tabs.open_file(file_path, content)
        editor = self.editor_tabs.current_editor()
        if editor:
            editor.textChanged.connect(self._queue_realtime_validation)
        self.project.add_recent_file(file_path)
        self.status.set_file(file_path)
        self.execution_panel.target_path.setText(file_path)
        self._queue_realtime_validation()

    def save_current(self) -> None:
        editor = self.editor_tabs.current_editor()
        if editor is None:
            return
        path = self.editor_tabs.current_path()
        if not path:
            folder = self.workbench.modules_dir
            path, _ = QFileDialog.getSaveFileName(self, 'Salvar arquivo', str(folder), 'Mint files (*.mint);;All files (*.*)')
            if not path:
                return
            self.editor_tabs.set_current_path(path)
        self.files.write_text(path, editor.toPlainText())
        editor.document().setModified(False)
        self.editor_tabs.mark_modified(path, False)
        self.status.set_file(path)
        if self.config.get('auto_lint_on_save'):
            self.lint_current()

    def save_all(self) -> None:
        current_idx = self.editor_tabs.currentIndex()
        for i in range(self.editor_tabs.count()):
            self.editor_tabs.setCurrentIndex(i)
            self.save_current()
        self.editor_tabs.setCurrentIndex(current_idx)

    def run_current(self) -> None:
        path = self.editor_tabs.current_path() or self.execution_panel.target_path.text().strip()
        if not path:
            QMessageBox.information(self, 'Execução', 'Abra ou informe um arquivo .mint para executar.')
            return
        request = ExecutionRequest(target_path=path, parameters=[p.strip() for p in self.execution_panel.parameters.text().split(',') if p.strip()], workspace=str(self.workbench.workspace))
        self._execute_request(request)

    def lint_current(self) -> None:
        path = self.editor_tabs.current_path()
        if not path:
            return
        diagnostics = self.linter.lint_file(path)
        self._set_diagnostics(diagnostics)
        self._apply_editor_diagnostics(diagnostics)
        self.bottom_tabs.setCurrentWidget(self.problems_table)

    def _execute_request(self, request: ExecutionRequest) -> None:
        if not request.target_path:
            QMessageBox.warning(self, 'Execução', 'Informe um arquivo/programa Mint.')
            return
        path = Path(request.target_path)
        if not path.exists():
            QMessageBox.warning(self, 'Execução', f'Objeto não encontrado: {path}')
            return
        self.execution_panel.target_path.setText(str(path))
        self.detail_tabs.setCurrentWidget(self.execution_panel)
        record = self.execution_service.add_record(request)
        self._active_execution_record = record
        self._execution_output_buffer = [f'Execução iniciada para {path.name}', f'Parâmetros: {request.parameters or ["<nenhum>"]}']
        self.execution_panel.output.clear()
        for chunk in self._execution_output_buffer:
            self.execution_panel.append_output(chunk)
        self._refresh_execution_history()
        if self.editor_tabs.current_editor() and self.editor_tabs.current_path() == str(path) and self.editor_tabs.current_editor().document().isModified():
            self.save_current()
        self.runner.run_file(str(path), str(self.workbench.workspace))

    def _handle_runner_output(self, text: str) -> None:
        self._execution_output_buffer.append(text.rstrip())
        self.execution_panel.append_output(text)
        self._append_log(text)

    def _handle_runner_finished(self, exit_code: int) -> None:
        self.status.showMessage(f'Execução finalizada (código {exit_code})', 5000)
        if self._active_execution_record is not None:
            self._active_execution_record.exit_code = exit_code
            self._active_execution_record.status = 'success' if exit_code == 0 else 'error'
            self._active_execution_record.output = '\n'.join(self._execution_output_buffer)
            self.execution_service.update_record(self._active_execution_record)
            self.execution_service.log_output(self._active_execution_record.target_path, self._active_execution_record.output)
            self._refresh_execution_history()
            self._active_execution_record = None

    def _save_table_definition(self, definition: TableDefinition) -> None:
        self.table_service.save_table(definition)
        self._refresh_table_catalog()
        self._refresh_dashboard()
        self._append_log(f'Tabela salva: {definition.name}')
        QMessageBox.information(self, 'Tabelas', f'Tabela {definition.name} salva com sucesso.')

    def _generate_table_definition(self, definition: TableDefinition) -> None:
        generated = self.table_service.generate_mint_definition(definition)
        self.table_panel.generated_path.setText(str(generated))
        self._refresh_table_catalog()
        self._append_log(f'Definição Mint gerada: {generated}')
        self.open_file(str(generated))

    def _delete_table_definition(self, name: str) -> None:
        if QMessageBox.question(self, 'Excluir tabela', f'Confirma exclusão da tabela {name}?') != QMessageBox.Yes:
            return
        self.table_service.delete_table(name)
        self.table_panel.clear_form()
        self._refresh_table_catalog()
        self._refresh_dashboard()

    def _refresh_table_catalog(self) -> None:
        tables = self.table_service.list_tables()
        self.table_list.setRowCount(0)
        for definition in tables:
            row = self.table_list.rowCount()
            self.table_list.insertRow(row)
            for col, value in enumerate([definition.name, definition.description, definition.module, str(len(definition.fields))]):
                self.table_list.setItem(row, col, QTableWidgetItem(value))

    def _refresh_dashboard(self) -> None:
        tables = len(self.table_service.list_tables())
        modules = len(list(self.workbench.modules_dir.rglob('*.mint')))
        generated = len(list((self.workbench.generated_dir / 'tables').glob('*.mint'))) if (self.workbench.generated_dir / 'tables').exists() else 0
        runs = len(self.execution_service.list_history())
        self.dashboard_panel.set_rows([
            ('Tabelas internas', str(tables), 'Modelagem visual e geração Mint'),
            ('Módulos Mint', str(modules), 'Árvore técnica reutilizável'),
            ('Artefatos gerados', str(generated), 'Definições sincronizadas do modelador'),
            ('Execuções', str(runs), 'Histórico operacional do workbench'),
        ])

    def _refresh_execution_history(self) -> None:
        self.execution_panel.set_history(self.execution_service.list_history())

    def _open_selected_table(self, row: int, _col: int) -> None:
        table_name = self.table_list.item(row, 0).text()
        definition = self.table_service.get_table(table_name)
        if definition:
            self.table_panel.load_definition(definition)
            self.detail_tabs.setCurrentWidget(self.table_panel)

    def _create_module(self, base_path: str) -> None:
        name, ok = QInputDialog.getText(self, 'Novo módulo', 'Nome técnico do módulo/pasta')
        if ok and name:
            target = Path(base_path)
            if target.is_file():
                target = target.parent
            self.module_service.create_module(name, str(target))
            self._refresh_dashboard()

    def _create_module_file(self, base_path: str) -> None:
        name, ok = QInputDialog.getText(self, 'Novo arquivo Mint', 'Nome do arquivo .mint')
        if ok and name:
            folder = Path(base_path)
            if folder.is_file():
                folder = folder.parent
            file_path = self.module_service.create_mint_file(str(folder), name)
            self.open_file(str(file_path))
            self._refresh_dashboard()

    def _rename_path(self, path: str) -> None:
        if not path:
            return
        current = Path(path)
        name, ok = QInputDialog.getText(self, 'Renomear', 'Novo nome', text=current.name)
        if ok and name:
            self.files.rename(str(current), str(current.with_name(name)))
            self._refresh_dashboard()

    def _delete_path(self, path: str) -> None:
        if not path:
            return
        if QMessageBox.question(self, 'Excluir', f'Excluir {path}?') == QMessageBox.Yes:
            self.files.delete(path)
            self._refresh_dashboard()

    def _handle_navigation(self, kind: str, key: str) -> None:
        if kind != 'section':
            return
        if key == 'tables':
            self.detail_tabs.setCurrentWidget(self.table_list)
        elif key == 'modules':
            self.detail_tabs.setCurrentWidget(self.module_panel)
        elif key == 'programs':
            program = next(self.workbench.programs_dir.glob('*.mint'), None)
            if program:
                self.open_file(str(program))
        elif key == 'executions':
            self.detail_tabs.setCurrentWidget(self.execution_panel)
        elif key in HELP_TOPICS:
            title, html = HELP_TOPICS[key]
            self.help_panel.set_topic(title, html)
            self.detail_tabs.setCurrentWidget(self.help_panel)
        elif key == 'logs':
            self.bottom_tabs.setCurrentWidget(self.log_view)
        elif key == 'settings':
            self.open_settings()
        elif key == 'environment':
            self.help_panel.set_topic('Ambiente', f'<p>Workspace atual: <code>{self.workbench.workspace}</code></p><p>Módulos: <code>{self.workbench.modules_dir}</code></p><p>Metadata: <code>{self.workbench.workbench_dir}</code></p>')
            self.detail_tabs.setCurrentWidget(self.help_panel)
        else:
            self.help_panel.set_topic('Workbench', '<p>Área preparada para expansão futura do ERP Mint.</p>')
            self.detail_tabs.setCurrentWidget(self.help_panel)

    def _append_log(self, text: str) -> None:
        self.log_view.append(text.rstrip())

    def _queue_realtime_validation(self) -> None:
        editor = self.editor_tabs.current_editor()
        if not editor:
            return
        self.realtime_validator.queue_validation(editor.toPlainText(), self.editor_tabs.current_path())

    def _on_realtime_diagnostics(self, request_id: int, diagnostics: list[Diagnostic]) -> None:
        if request_id < self._latest_validation_request:
            return
        self._latest_validation_request = request_id
        self._set_diagnostics(diagnostics)
        self._apply_editor_diagnostics(diagnostics)

    def _apply_editor_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        editor = self.editor_tabs.current_editor()
        if editor:
            editor.set_diagnostics(diagnostics)

    def _set_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        self.problems_table.setRowCount(0)
        for diag in diagnostics:
            row = self.problems_table.rowCount()
            self.problems_table.insertRow(row)
            values = [diag.severity, diag.message, diag.file_path, str(diag.line), str(diag.column), diag.suggestion]
            for col, value in enumerate(values):
                self.problems_table.setItem(row, col, QTableWidgetItem(value))

    def _go_to_problem(self, row: int, _col: int) -> None:
        file_path = self.problems_table.item(row, 2).text()
        line = int(self.problems_table.item(row, 3).text() or 0)
        col = int(self.problems_table.item(row, 4).text() or 0)
        if file_path:
            self.open_file(file_path)
        ed = self.editor_tabs.current_editor()
        if ed and line > 0:
            cursor = ed.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.MoveAnchor, line - 1)
            if col > 0:
                cursor.movePosition(cursor.Right, cursor.MoveAnchor, col - 1)
            ed.setTextCursor(cursor)

    def _on_file_modified(self, file_path: str, modified: bool) -> None:
        if file_path:
            self.editor_tabs.mark_modified(file_path, modified)

    def _on_cursor_changed(self, line: int, col: int) -> None:
        self.status.set_cursor(line, col)

    def _on_tab_changed(self, _idx: int) -> None:
        self.status.set_file(self.editor_tabs.current_path())
        self._queue_realtime_validation()

    def _close_tab(self, index: int) -> None:
        editor = self.editor_tabs.widget(index)
        if editor and editor.document().isModified():
            ans = QMessageBox.question(self, 'Alterações pendentes', 'Salvar alterações antes de fechar?')
            if ans == QMessageBox.Yes:
                self.editor_tabs.setCurrentIndex(index)
                self.save_current()
        self.editor_tabs.removeTab(index)

    def _apply_editor_font(self) -> None:
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            font = editor.font()
            font.setPointSize(int(self.config['font_size']))
            editor.setFont(font)

    def open_settings(self) -> None:
        dlg = SettingsDialog(self.config, self)
        if dlg.exec_() != dlg.Accepted:
            return
        vals = dlg.values()
        for key, value in vals.items():
            setting_key = {
                'theme': 'editor/theme',
                'font_size': 'editor/font_size',
                'tab_size': 'editor/tab_size',
                'use_spaces': 'editor/use_spaces',
                'auto_lint_on_save': 'lint/auto_on_save',
                'runtime_path': 'mint/runtime_path',
                'linter_path': 'mint/linter_path',
            }[key]
            self.settings.set(setting_key, value)
        self.settings.sync()
        self.config = self.settings.load_all()
        ThemeManager().apply(QApplication.instance(), self.config.get('theme', 'light'))

    def about(self) -> None:
        QMessageBox.information(self, 'Sobre', 'Mint ERP Studio\nWorkbench visual para modelagem de tabelas, módulos Mint e execução operacional.')

    def closeEvent(self, event) -> None:
        unsaved = []
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            if editor.document().isModified():
                unsaved.append(self.editor_tabs.tabText(i))
        if unsaved:
            ans = QMessageBox.question(self, 'Sair', 'Existem arquivos não salvos. Deseja sair mesmo?')
            if ans != QMessageBox.Yes:
                event.ignore()
                return
        self.settings.sync()
        super().closeEvent(event)
