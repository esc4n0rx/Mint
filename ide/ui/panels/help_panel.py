from __future__ import annotations

from PyQt5.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget


class HelpPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.title = QLabel('Ajuda Mint')
        self.title.setObjectName('WorkbenchTitle')
        self.subtitle = QLabel('Referência rápida do ambiente Mint ERP Studio.')
        self.subtitle.setObjectName('WorkbenchSubtitle')
        self.content = QTextBrowser()
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.content)

    def set_topic(self, title: str, html: str) -> None:
        self.title.setText(title)
        self.content.setHtml(html)
