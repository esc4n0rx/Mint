from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ide.core.file_manager import FileManager
from ide.core.linter_bridge import LinterBridge
from ide.core.project_manager import ProjectManager
from ide.core.runner import MintRunner
from ide.core.settings_manager import SettingsManager
from ide.core.workspace_manager import WorkspaceManager
from ide.models.diagnostics import Diagnostic
from ide.ui.dialogs import SettingsDialog
from ide.ui.editor_tabs import EditorTabs
from ide.ui.file_explorer import FileExplorer
from ide.ui.status_bar import IdeStatusBar
from ide.ui.terminal_panel import TerminalPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Mint IDE")
        self.resize(1400, 900)

        self.settings = SettingsManager()
        self.config = self.settings.load_all()
        self.workspace = WorkspaceManager()
        self.project = ProjectManager(self.settings)
        self.files = FileManager()
        self.linter = LinterBridge()
        self.runner = MintRunner()

        self.editor_tabs = EditorTabs(self.config["tab_size"], self.config["use_spaces"])
        self.editor_tabs.file_changed.connect(self._on_file_modified)
        self.editor_tabs.cursor_changed.connect(self._on_cursor_changed)
        self.editor_tabs.currentChanged.connect(self._on_tab_changed)
        self.editor_tabs.tabCloseRequested.connect(self._close_tab)

        self.explorer = FileExplorer()
        self.explorer.open_file_requested.connect(self.open_file)
        self.explorer.create_file_requested.connect(self._create_file)
        self.explorer.create_folder_requested.connect(self._create_folder)
        self.explorer.rename_requested.connect(self._rename_path)
        self.explorer.delete_requested.connect(self._delete_path)

        self.terminal = TerminalPanel()

        self.problems_table = QTableWidget(0, 5)
        self.problems_table.setHorizontalHeaderLabels(["Tipo", "Mensagem", "Arquivo", "Linha", "Coluna"])
        self.problems_table.cellDoubleClicked.connect(self._go_to_problem)

        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.addTab(self.terminal, "Terminal")
        self.bottom_tabs.addTab(self.problems_table, "Problemas")

        vertical = QSplitter(Qt.Vertical)
        vertical.addWidget(self.editor_tabs)
        vertical.addWidget(self.bottom_tabs)
        vertical.setSizes([650, 250])

        root = QSplitter(Qt.Horizontal)
        root.addWidget(self.explorer)
        root.addWidget(vertical)
        root.setSizes([300, 1100])

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(root)
        self.setCentralWidget(container)

        self.status = IdeStatusBar()
        self.setStatusBar(self.status)

        self._build_actions()
        self._build_menus()
        self._wire_runner()
        self._apply_editor_font()
        self._restore_last_workspace()

    def _build_actions(self):
        self.act_new = QAction("Novo arquivo", self, shortcut="Ctrl+N", triggered=self.new_file)
        self.act_open = QAction("Abrir arquivo", self, shortcut="Ctrl+O", triggered=self.open_file_dialog)
        self.act_open_ws = QAction("Abrir workspace", self, shortcut="Ctrl+Shift+O", triggered=self.open_workspace_dialog)
        self.act_save = QAction("Salvar", self, shortcut="Ctrl+S", triggered=self.save_current)
        self.act_save_as = QAction("Salvar como", self, shortcut="Ctrl+Shift+S", triggered=self.save_as_current)
        self.act_save_all = QAction("Salvar todos", self, triggered=self.save_all)
        self.act_run = QAction("Executar", self, shortcut="F5", triggered=self.run_current)
        self.act_stop = QAction("Parar execução", self, triggered=self.runner.stop)
        self.act_lint = QAction("Lint atual", self, shortcut="F8", triggered=self.lint_current)
        self.act_settings = QAction("Configurações", self, triggered=self.open_settings)
        self.act_about = QAction("Sobre", self, triggered=self.about)

        tb = self.addToolBar("Main")
        for act in [self.act_new, self.act_open, self.act_open_ws, self.act_save, self.act_run, self.act_lint]:
            tb.addAction(act)

    def _build_menus(self):
        m_file = self.menuBar().addMenu("Arquivo")
        m_file.addActions([self.act_new, self.act_open, self.act_open_ws, self.act_save, self.act_save_as, self.act_save_all])

        m_run = self.menuBar().addMenu("Executar")
        m_run.addActions([self.act_run, self.act_stop, self.act_lint])

        m_help = self.menuBar().addMenu("Ajuda")
        m_help.addActions([self.act_settings, self.act_about])

    def _wire_runner(self):
        self.runner.started.connect(lambda p: self.terminal.append_text(f"[run] {p}"))
        self.runner.output.connect(self.terminal.append_text)
        self.runner.error.connect(lambda t: self.terminal.append_text(f"[stderr] {t}"))
        self.runner.finished.connect(lambda code: self.status.showMessage(f"Execução finalizada (código {code})", 4000))

    def _restore_last_workspace(self):
        last = self.config.get("last_workspace")
        if last and Path(last).exists():
            self._open_workspace(last)

    def _apply_editor_font(self):
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            font = editor.font()
            font.setPointSize(int(self.config["font_size"]))
            editor.setFont(font)

    def new_file(self):
        self.editor_tabs.new_unsaved()

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo", str(Path.cwd()), "Mint files (*.mint);;All files (*.*)")
        if path:
            self.open_file(path)

    def open_workspace_dialog(self):
        path = QFileDialog.getExistingDirectory(self, "Abrir workspace", str(Path.cwd()))
        if path:
            self._open_workspace(path)

    def _open_workspace(self, path: str):
        self.workspace.open_workspace(path)
        self.explorer.set_root_path(path)
        self.project.set_last_workspace(path)
        self.status.set_workspace(path)

    def open_file(self, file_path: str):
        try:
            content = self.files.read_text(file_path)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Erro", f"Falha ao abrir arquivo: {exc}")
            return
        self.editor_tabs.open_file(file_path, content)
        self.project.add_recent_file(file_path)
        self.status.set_file(file_path)

    def save_current(self):
        editor = self.editor_tabs.current_editor()
        if editor is None:
            return
        path = self.editor_tabs.current_path()
        if not path:
            return self.save_as_current()
        self.files.write_text(path, editor.toPlainText())
        editor.document().setModified(False)
        self.editor_tabs.mark_modified(path, False)
        if self.config.get("auto_lint_on_save"):
            self.lint_current()

    def save_as_current(self):
        editor = self.editor_tabs.current_editor()
        if editor is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar arquivo", str(Path.cwd()), "Mint files (*.mint);;All files (*.*)")
        if not path:
            return
        self.files.write_text(path, editor.toPlainText())
        self.editor_tabs.set_current_path(path)
        editor.document().setModified(False)
        self.status.set_file(path)

    def save_all(self):
        current_idx = self.editor_tabs.currentIndex()
        for i in range(self.editor_tabs.count()):
            self.editor_tabs.setCurrentIndex(i)
            self.save_current()
        self.editor_tabs.setCurrentIndex(current_idx)

    def run_current(self):
        path = self.editor_tabs.current_path()
        if not path:
            QMessageBox.information(self, "Executar", "Salve o arquivo antes de executar.")
            return
        if self.editor_tabs.current_editor().document().isModified():
            self.save_current()
        self.bottom_tabs.setCurrentIndex(0)
        base = str(self.workspace.base_dir_for(path))
        self.runner.run_file(path, base)

    def lint_current(self):
        path = self.editor_tabs.current_path()
        if not path:
            return
        diagnostics = self.linter.lint_file(path)
        self._set_diagnostics(diagnostics)
        self.bottom_tabs.setCurrentIndex(1)

    def _set_diagnostics(self, diagnostics: list[Diagnostic]):
        self.problems_table.setRowCount(0)
        for diag in diagnostics:
            row = self.problems_table.rowCount()
            self.problems_table.insertRow(row)
            values = [diag.severity, diag.message, diag.file_path, str(diag.line), str(diag.column)]
            for col, value in enumerate(values):
                self.problems_table.setItem(row, col, QTableWidgetItem(value))

    def _go_to_problem(self, row: int, _col: int):
        file_path = self.problems_table.item(row, 2).text()
        line = int(self.problems_table.item(row, 3).text() or 0)
        if file_path:
            self.open_file(file_path)
        ed = self.editor_tabs.current_editor()
        if ed and line > 0:
            cursor = ed.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.MoveAnchor, line - 1)
            ed.setTextCursor(cursor)

    def _on_file_modified(self, file_path: str, modified: bool):
        if file_path:
            self.editor_tabs.mark_modified(file_path, modified)

    def _on_cursor_changed(self, line: int, col: int):
        self.status.set_cursor(line, col)

    def _on_tab_changed(self, _idx: int):
        self.status.set_file(self.editor_tabs.current_path())

    def _close_tab(self, index: int):
        editor = self.editor_tabs.widget(index)
        if editor and editor.document().isModified():
            ans = QMessageBox.question(self, "Alterações pendentes", "Salvar alterações antes de fechar?")
            if ans == QMessageBox.Yes:
                self.editor_tabs.setCurrentIndex(index)
                self.save_current()
        self.editor_tabs.removeTab(index)

    def _create_file(self, base_path: str):
        name, ok = QInputDialog.getText(self, "Novo arquivo", "Nome do arquivo")
        if not ok or not name:
            return
        target = Path(base_path)
        if target.is_file():
            target = target.parent
        self.files.write_text(str(target / name), "")

    def _create_folder(self, base_path: str):
        name, ok = QInputDialog.getText(self, "Nova pasta", "Nome da pasta")
        if not ok or not name:
            return
        target = Path(base_path)
        if target.is_file():
            target = target.parent
        self.files.create_folder(str(target / name))

    def _rename_path(self, path: str):
        if not path:
            return
        name, ok = QInputDialog.getText(self, "Renomear", "Novo nome")
        if not ok or not name:
            return
        p = Path(path)
        self.files.rename(str(p), str(p.with_name(name)))

    def _delete_path(self, path: str):
        if not path:
            return
        ans = QMessageBox.question(self, "Excluir", f"Excluir {path}?")
        if ans == QMessageBox.Yes:
            self.files.delete(path)

    def open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec_() != dlg.Accepted:
            return
        vals = dlg.values()
        for k, v in vals.items():
            setting_key = {
                "font_size": "editor/font_size",
                "tab_size": "editor/tab_size",
                "use_spaces": "editor/use_spaces",
                "auto_lint_on_save": "lint/auto_on_save",
                "runtime_path": "mint/runtime_path",
                "linter_path": "mint/linter_path",
            }[k]
            self.settings.set(setting_key, v)
        self.settings.sync()
        self.config = self.settings.load_all()

    def about(self):
        QMessageBox.information(self, "Sobre", "Mint IDE\nIDE oficial para desenvolvimento em Mint.")

    def closeEvent(self, event):
        unsaved = []
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            if editor.document().isModified():
                unsaved.append(self.editor_tabs.tabText(i))
        if unsaved:
            ans = QMessageBox.question(self, "Sair", "Existem arquivos não salvos. Deseja sair mesmo?")
            if ans != QMessageBox.Yes:
                event.ignore()
                return
        self.settings.sync()
        super().closeEvent(event)
