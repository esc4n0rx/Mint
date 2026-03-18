from __future__ import annotations

from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QTextCharFormat, QTextFormat
from PyQt5.QtWidgets import QPlainTextEdit, QTextEdit, QToolTip

from ide.models.diagnostics import Diagnostic

from .auto_indent import next_line_indent
from .bracket_matcher import bracket_selections
from .line_number_area import LineNumberArea
from .syntax_highlighter import MintSyntaxHighlighter


class MintEditor(QPlainTextEdit):
    def __init__(self, tab_size: int = 2, use_spaces: bool = True, parent=None):
        super().__init__(parent)
        self._tab_size = tab_size
        self._use_spaces = use_spaces
        self._line_number_area = LineNumberArea(self)
        self._highlighter = MintSyntaxHighlighter(self.document())
        self._diagnostics: list[Diagnostic] = []

        self.setMouseTracking(True)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._update_highlights)

        self._update_line_number_area_width(0)
        self._update_highlights()

    def set_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        self._diagnostics = diagnostics
        self._update_highlights()

    def line_number_area_size(self) -> QSize:
        return QSize(self._line_number_area_width(), 0)

    def _line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().width("9") * digits

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor('#eef3f8'))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor('#6a7a8c'))
                painter.drawText(0, top, self._line_number_area.width() - 4, self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def _update_highlights(self):
        selections = []

        line_sel = QTextEdit.ExtraSelection()
        line_sel.format.setBackground(QColor('#e8f1fb'))
        line_sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        line_sel.cursor = self.textCursor()
        line_sel.cursor.clearSelection()
        selections.append(line_sel)

        for diag in self._diagnostics:
            if diag.line <= 0:
                continue
            sel = QTextEdit.ExtraSelection()
            cur = self.textCursor()
            block = self.document().findBlockByNumber(diag.line - 1)
            if not block.isValid():
                continue
            offset = max(0, diag.column - 1)
            cur.setPosition(block.position() + offset)
            cur.movePosition(cur.NextCharacter, cur.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setUnderlineStyle(QTextCharFormat.WaveUnderline)
            fmt.setUnderlineColor(QColor("#ff6b6b") if diag.severity == "error" else QColor("#f5c542"))
            sel.cursor = cur
            sel.format = fmt
            selections.append(sel)

        selections.extend(bracket_selections(self))
        self.setExtraSelections(selections)

    def mouseMoveEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        for diag in self._diagnostics:
            if diag.line == line and (diag.column == 0 or diag.column == col):
                QToolTip.showText(event.globalPos(), diag.full_message, self)
                break
        else:
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        cursor = self.textCursor()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            prev_line = cursor.block().text()
            super().keyPressEvent(event)
            tab_unit = (" " * self._tab_size) if self._use_spaces else "\t"
            self.insertPlainText(next_line_indent(prev_line, tab_unit))
            return

        if key == Qt.Key_Tab:
            if cursor.hasSelection():
                self._indent_selection()
            else:
                self.insertPlainText((" " * self._tab_size) if self._use_spaces else "\t")
            return

        if key == Qt.Key_Backtab:
            self._outdent_selection()
            return

        super().keyPressEvent(event)

    def _indent_selection(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.beginEditBlock()
        unit = (" " * self._tab_size) if self._use_spaces else "\t"
        while cursor.position() <= end:
            cursor.movePosition(cursor.StartOfLine)
            cursor.insertText(unit)
            if not cursor.movePosition(cursor.Down):
                break
            end += len(unit)
        cursor.endEditBlock()

    def _outdent_selection(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.beginEditBlock()
        while cursor.position() <= end:
            cursor.movePosition(cursor.StartOfLine)
            line = cursor.block().text()
            remove_len = 0
            if line.startswith("\t"):
                remove_len = 1
            elif line.startswith(" " * self._tab_size):
                remove_len = self._tab_size
            if remove_len:
                for _ in range(remove_len):
                    cursor.deleteChar()
                end -= remove_len
            if not cursor.movePosition(cursor.Down):
                break
        cursor.endEditBlock()
