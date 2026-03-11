from __future__ import annotations

import difflib
import re
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal

from ide.models.diagnostics import Diagnostic
from mintlang.errors import MintError
from mintlang.lexer import KEYWORDS, Lexer
from mintlang.linter import Linter
from mintlang.parser import Parser


IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)\s*\.\s*$", re.IGNORECASE)
LINE_TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

BLOCK_STARTERS = {
    "if": "endif",
    "while": "endwhile",
    "for": "endfor",
    "try": "endtry",
    "func": "endfunc",
    "struct": "endstruct",
}
BLOCK_ENDERS = {v: k for k, v in BLOCK_STARTERS.items()}


class _ValidationWorker(QObject):
    finished = pyqtSignal(int, list)

    def run(self, request_id: int, source: str, file_path: str) -> None:
        diagnostics = _validate_source(source, file_path)
        self.finished.emit(request_id, diagnostics)


class RealtimeValidator(QObject):
    diagnostics_ready = pyqtSignal(int, list)

    def __init__(self, parent=None, debounce_ms: int = 350) -> None:
        super().__init__(parent)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(debounce_ms)
        self._debounce.timeout.connect(self._validate_async)
        self._pending_source = ""
        self._pending_file = ""
        self._request_id = 0

    def queue_validation(self, source: str, file_path: str) -> None:
        self._pending_source = source
        self._pending_file = file_path
        self._debounce.start()

    def _validate_async(self) -> None:
        self._request_id += 1
        request_id = self._request_id

        thread = QThread(self)
        worker = _ValidationWorker()
        worker.moveToThread(thread)
        thread.started.connect(lambda: worker.run(request_id, self._pending_source, self._pending_file))
        worker.finished.connect(self.diagnostics_ready.emit)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()


def _validate_source(source: str, file_path: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    lines = source.splitlines()

    diagnostics.extend(_detect_typos(lines, file_path))
    diagnostics.extend(_detect_import_issues(lines, file_path))
    diagnostics.extend(_detect_block_issues(lines, file_path))

    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        for issue in Linter().lint(program):
            diagnostics.append(Diagnostic("warning", issue.message, file_path, 0, 0))
    except MintError as exc:
        line, col = _extract_position(str(exc))
        diagnostics.append(Diagnostic("error", str(exc), file_path, line, col))
    except Exception as exc:  # pylint: disable=broad-except
        diagnostics.append(Diagnostic("error", f"Falha na validação: {exc}", file_path, 0, 0))

    return diagnostics


def _detect_typos(lines: list[str], file_path: str) -> list[Diagnostic]:
    valid_words = sorted(set(KEYWORDS.keys()) | {"program", "initialization", "endprogram"})
    diagnostics: list[Diagnostic] = []

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith('"'):
            continue
        first = LINE_TOKEN_RE.search(stripped)
        if not first:
            continue
        token = first.group(0)
        lower = token.lower()
        if lower in KEYWORDS:
            continue
        suggestion = difflib.get_close_matches(lower, valid_words, n=1, cutoff=0.75)
        if suggestion:
            col = line.find(token) + 1
            diagnostics.append(
                Diagnostic(
                    "warning",
                    f"Comando/keyword desconhecido: '{token}'.",
                    file_path,
                    line_no,
                    col,
                    f"Você quis dizer '{suggestion[0]}'?",
                )
            )
    return diagnostics


def _detect_import_issues(lines: list[str], file_path: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for line_no, line in enumerate(lines, start=1):
        if "import" not in line.lower():
            continue
        stripped = line.strip()
        if stripped.lower().startswith("import") and not IMPORT_RE.match(stripped):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "Sintaxe de import inválida.",
                    file_path,
                    line_no,
                    1,
                    "Use: import modulo.caminho.",
                )
            )
    return diagnostics


def _detect_block_issues(lines: list[str], file_path: str) -> list[Diagnostic]:
    stack: list[tuple[str, int]] = []
    diagnostics: list[Diagnostic] = []

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip().lower().rstrip(".")
        if not stripped:
            continue
        first = stripped.split()[0]
        if first in BLOCK_STARTERS:
            stack.append((first, line_no))
        elif first in BLOCK_ENDERS:
            if not stack or stack[-1][0] != BLOCK_ENDERS[first]:
                diagnostics.append(
                    Diagnostic("warning", f"Fechamento de bloco inesperado: {first}.", file_path, line_no, 1)
                )
            else:
                stack.pop()

    for opener, line_no in stack:
        diagnostics.append(
            Diagnostic(
                "warning",
                f"Bloco '{opener}' não foi fechado.",
                file_path,
                line_no,
                1,
                f"Adicione '{BLOCK_STARTERS[opener]}.'",
            )
        )
    return diagnostics


def _extract_position(message: str) -> tuple[int, int]:
    match = re.search(r"(?:linha|line)\s+(\d+)[,:]\s*(?:coluna|column)?\s*(\d+)", message, re.IGNORECASE)
    if not match:
        match = re.search(r"(?:em|at)\s+(\d+):(\d+)", message, re.IGNORECASE)
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))
