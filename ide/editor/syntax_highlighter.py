from __future__ import annotations

from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter


class MintSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.rules = []

        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#56b6c2"))
        keyword_fmt.setFontWeight(QFont.Bold)

        type_fmt = QTextCharFormat()
        type_fmt.setForeground(QColor("#e5c07b"))

        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("#98c379"))

        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#d19a66"))

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#7f848e"))
        comment_fmt.setFontItalic(True)

        system_fmt = QTextCharFormat()
        system_fmt.setForeground(QColor("#c678dd"))

        keywords = [
            "program", "init", "initialization", "endprogram", "var", "type", "write",
            "if", "elseif", "else", "endif", "while", "endwhile", "func", "endfunc",
            "returns", "return", "input", "move", "to", "query", "from", "where", "into",
            "load", "save", "export", "struct", "endstruct", "add", "insert", "size",
            "for", "in", "endfor", "try", "catch", "endtry", "import", "and", "or", "not",
            "count", "sum", "avg", "true", "false",
            "db", "create", "open", "compact", "append", "values", "select", "update", "set", "delete",
            "show", "tables", "describe", "index", "on", "primary", "key", "auto_increment",
        ]
        for word in keywords:
            pattern = QRegExp(fr"\b{word}\b")
            pattern.setCaseSensitivity(Qt.CaseInsensitive)
            self.rules.append((pattern, keyword_fmt))

        for t in ["int", "float", "string", "char", "bool", "list", "table"]:
            self.rules.append((QRegExp(fr"\b{t}\b"), type_fmt))

        self.rules.extend([
            (QRegExp(r'"[^"\\]*(\\[ntr"\\]|[^"\\])*"'), string_fmt),
            (QRegExp(r"'[^'\\]*(\\[ntr'\\]|[^'\\])*'"), string_fmt),
            (QRegExp(r"\b\d+(\.\d+)?\b"), number_fmt),
            (QRegExp(r"//[^\n]*"), comment_fmt),
            (QRegExp(r"^\s*\"[^\n]*"), comment_fmt),
            (QRegExp(r"\bsystem\.[A-Za-z_][A-Za-z0-9_]*\b"), system_fmt),
            (QRegExp(r"[+\-*/%=]|==|!=|<=|>=|<|>|="), keyword_fmt),
        ])

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self.rules:
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)
