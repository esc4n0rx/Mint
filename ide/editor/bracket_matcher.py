from __future__ import annotations

from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt5.QtWidgets import QTextEdit


PAIRS = {')': '(', ']': '[', '}': '{'}


def bracket_selections(editor) -> list:
    text = editor.toPlainText()
    pos = editor.textCursor().position()
    if pos == 0 or pos > len(text):
        return []
    ch = text[pos - 1]
    if ch not in PAIRS:
        return []

    target = PAIRS[ch]
    depth = 0
    for i in range(pos - 2, -1, -1):
        c = text[i]
        if c == ch:
            depth += 1
        elif c == target:
            if depth == 0:
                fmt = QTextCharFormat()
                fmt.setBackground(QColor("#3e4451"))
                sels = []
                for p in (i, pos - 1):
                    sel = QTextEdit.ExtraSelection()
                    cur = editor.textCursor()
                    cur.setPosition(p)
                    cur.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                    sel.cursor = cur
                    sel.format = fmt
                    sels.append(sel)
                return sels
            depth -= 1
    return []
