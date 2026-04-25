from __future__ import annotations

import io
import shlex
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from mintlang.errors import MintError
from mintlang.interpreter import Interpreter
from mintlang.linter import Linter
from mintlang.module_loader import ModuleLoader


class ClipperIDE(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.cwd = Path.cwd()
        self.current_file: Path | None = None

        self.setWindowTitle("Mint Clipper IDE")
        self.resize(1320, 860)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        splitter = QSplitter(Qt.Vertical)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "Editor Mint (.mint). Use o terminal abaixo para new/open/save/run/lint/compile."
        )

        terminal_panel = QWidget()
        terminal_layout = QVBoxLayout(terminal_panel)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(6)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)

        cmd_row = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Digite um comando (help)")
        run_button = QPushButton("EXEC")
        cmd_row.addWidget(self.command_input)
        cmd_row.addWidget(run_button)

        terminal_layout.addWidget(self.output)
        terminal_layout.addLayout(cmd_row)

        splitter.addWidget(self.editor)
        splitter.addWidget(terminal_panel)
        splitter.setSizes([520, 300])

        layout.addWidget(self.status_label)
        layout.addWidget(splitter)

        self.setCentralWidget(root)

        self._apply_clipper_theme()

        run_button.clicked.connect(self.execute_command)
        self.command_input.returnPressed.connect(self.execute_command)

        self.commands: dict[str, Callable[[list[str]], None]] = {
            "help": self.cmd_help,
            "new": self.cmd_new,
            "open": self.cmd_open,
            "save": self.cmd_save,
            "run": self.cmd_run,
            "lint": self.cmd_lint,
            "compile": self.cmd_compile,
            "check": self.cmd_check,
            "pwd": self.cmd_pwd,
            "cd": self.cmd_cd,
            "ls": self.cmd_ls,
            "clear": self.cmd_clear,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
        }

        self._log_boot_sequence()

    def _apply_clipper_theme(self) -> None:
        font = QFont("Courier New")
        font.setPointSize(13)

        app_style = (
            "QWidget { background-color: #000000; color: #FFFFFF; }"
            "QPlainTextEdit, QLineEdit {"
            "  background-color: #000000;"
            "  color: #FFFFFF;"
            "  border: 1px solid #FFFFFF;"
            "  selection-background-color: #FFFFFF;"
            "  selection-color: #000000;"
            "}"
            "QPushButton {"
            "  background-color: #000000;"
            "  color: #FFFFFF;"
            "  border: 1px solid #FFFFFF;"
            "  padding: 6px 12px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #111111; }"
            "QLabel { color: #FFFFFF; font-weight: bold; }"
        )

        self.setStyleSheet(app_style)
        self.editor.setFont(font)
        self.output.setFont(font)
        self.command_input.setFont(font)
        self.status_label.setFont(font)

    def _log_boot_sequence(self) -> None:
        self.write_output("MINT CLIPPER IDE - BOOT")
        self.write_output("----------------------------------------")
        self.cmd_check([])
        self.write_output("Digite 'help' para ver comandos disponíveis.")
        self._refresh_status()

    def _refresh_status(self) -> None:
        file_desc = str(self.current_file) if self.current_file else "(sem arquivo)"
        self.status_label.setText(f"cwd={self.cwd}  |  arquivo={file_desc}")

    def write_output(self, text: str = "") -> None:
        self.output.appendPlainText(text)
        self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())

    def execute_command(self) -> None:
        raw = self.command_input.text().strip()
        if not raw:
            return

        self.write_output(f"> {raw}")
        self.command_input.clear()

        if raw.startswith("!"):
            self.write_output("Comandos shell externos não são permitidos nesta IDE.")
            return

        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            self.write_output(f"Erro ao parsear comando: {exc}")
            return

        if not parts:
            return

        cmd, args = parts[0].lower(), parts[1:]
        action = self.commands.get(cmd)
        if not action:
            self.write_output(f"Comando desconhecido: {cmd}")
            self.write_output("Use: help")
            return

        try:
            action(args)
        except Exception as exc:  # noqa: BLE001
            self.write_output(f"Erro interno: {exc}")

        self._refresh_status()

    def resolve_path(self, path_str: str) -> Path:
        p = Path(path_str)
        if not p.is_absolute():
            p = self.cwd / p
        return p.resolve()

    def target_file(self, args: list[str]) -> Path | None:
        if args:
            return self.resolve_path(args[0])
        return self.current_file

    def cmd_help(self, _: list[str]) -> None:
        self.write_output("Comandos:")
        self.write_output("  new <arquivo.mint>      cria arquivo novo e abre no editor")
        self.write_output("  open <arquivo.mint>     abre arquivo existente")
        self.write_output("  save [arquivo.mint]     salva conteúdo do editor")
        self.write_output("  run [arquivo.mint]      valida + executa programa Mint")
        self.write_output("  lint [arquivo.mint]     valida semanticamente")
        self.write_output("  compile [arquivo.mint]  alias para lint")
        self.write_output("  check                   valida ambiente e core Mint")
        self.write_output("  pwd | cd <dir> | ls [dir]")
        self.write_output("  clear | exit")

    def cmd_new(self, args: list[str]) -> None:
        if not args:
            self.write_output("Uso: new <arquivo.mint>")
            return

        path = self.resolve_path(args[0])
        if path.suffix.lower() != ".mint":
            self.write_output("Erro: use extensão .mint")
            return
        if path.exists():
            self.write_output(f"Erro: arquivo já existe: {path}")
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        template = (
            "program init.\n"
            "  var message type string = \"Hello, Mint!\".\n"
            "initialization.\n"
            "  write(message).\n"
            "endprogram.\n"
        )
        path.write_text(template, encoding="utf-8")

        self.current_file = path
        self.editor.setPlainText(template)
        self.write_output(f"Arquivo criado e aberto: {path}")

    def cmd_open(self, args: list[str]) -> None:
        if not args:
            self.write_output("Uso: open <arquivo.mint>")
            return

        path = self.resolve_path(args[0])
        if not path.exists() or not path.is_file():
            self.write_output(f"Erro: arquivo não encontrado: {path}")
            return

        content = path.read_text(encoding="utf-8")
        self.current_file = path
        self.editor.setPlainText(content)
        self.write_output(f"Arquivo aberto: {path}")

    def cmd_save(self, args: list[str]) -> None:
        target = self.target_file(args)
        if target is None:
            self.write_output("Uso: save <arquivo.mint> (ou abra/crie um arquivo antes)")
            return

        if target.suffix.lower() != ".mint":
            self.write_output("Erro: o arquivo salvo precisa ser .mint")
            return

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.editor.toPlainText(), encoding="utf-8")
        self.current_file = target
        self.write_output(f"Arquivo salvo: {target}")

    def _load_program(self, file_path: Path):
        program, issues = ModuleLoader(file_path).load()
        issues.extend(Linter().lint(program))
        return program, issues

    def cmd_run(self, args: list[str]) -> None:
        target = self.target_file(args)
        if target is None:
            self.write_output("Erro: nenhum arquivo selecionado.")
            return

        self.cmd_save([str(target)])
        self.write_output(f"Executando: {target}")

        capture = io.StringIO()
        try:
            with redirect_stdout(capture), redirect_stderr(capture):
                program, issues = self._load_program(target)
                if issues:
                    print("LintError: encontrei problemas antes de executar:")
                    for i, issue in enumerate(issues, 1):
                        print(f"  {i}. {issue.message}")
                else:
                    Interpreter().run(program)

        except MintError as exc:
            self.write_output(f"MintError: {exc}")
            return
        except Exception as exc:  # noqa: BLE001
            self.write_output(f"Erro inesperado: {exc}")
            return

        out = capture.getvalue().rstrip()
        if out:
            self.write_output(out)
        self.write_output("[run finalizado]")

    def cmd_lint(self, args: list[str]) -> None:
        target = self.target_file(args)
        if target is None:
            self.write_output("Erro: nenhum arquivo selecionado.")
            return

        self.cmd_save([str(target)])
        self.write_output(f"Validando: {target}")

        try:
            _, issues = self._load_program(target)
        except MintError as exc:
            self.write_output(f"MintError: {exc}")
            return
        except Exception as exc:  # noqa: BLE001
            self.write_output(f"Erro inesperado: {exc}")
            return

        if issues:
            self.write_output("LintError: problemas encontrados:")
            for i, issue in enumerate(issues, 1):
                self.write_output(f"  {i}. {issue.message}")
            return

        self.write_output("OK: sem erros de lint.")

    def cmd_compile(self, args: list[str]) -> None:
        self.write_output("'compile' em Mint equivale à validação estática (lint).")
        self.cmd_lint(args)

    def cmd_check(self, _: list[str]) -> None:
        self.write_output(f"Python: {sys.version.split()[0]}")
        self.write_output("PyQt5: OK")
        try:
            import mintlang  # noqa: F401

            self.write_output("Core Mint: OK")
        except Exception as exc:  # noqa: BLE001
            self.write_output(f"Core Mint: FALHA ({exc})")

    def cmd_pwd(self, _: list[str]) -> None:
        self.write_output(str(self.cwd))

    def cmd_cd(self, args: list[str]) -> None:
        if not args:
            self.write_output("Uso: cd <diretório>")
            return

        target = self.resolve_path(args[0])
        if not target.exists() or not target.is_dir():
            self.write_output(f"Erro: diretório inválido: {target}")
            return

        self.cwd = target
        self.write_output(f"cwd alterado para: {self.cwd}")

    def cmd_ls(self, args: list[str]) -> None:
        target = self.resolve_path(args[0]) if args else self.cwd
        if not target.exists() or not target.is_dir():
            self.write_output(f"Erro: diretório inválido: {target}")
            return

        entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        if not entries:
            self.write_output("(vazio)")
            return

        for item in entries:
            suffix = "/" if item.is_dir() else ""
            self.write_output(f"{item.name}{suffix}")

    def cmd_clear(self, _: list[str]) -> None:
        self.output.clear()

    def cmd_exit(self, _: list[str]) -> None:
        self.close()


def main() -> None:
    app = QApplication(sys.argv)
    window = ClipperIDE()
    window.show()
    raise SystemExit(app.exec_())


if __name__ == "__main__":
    main()
