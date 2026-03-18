from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTabWidget

from ide.editor.mint_editor import MintEditor


class EditorTabs(QTabWidget):
    file_changed = pyqtSignal(str, bool)
    cursor_changed = pyqtSignal(int, int)

    def __init__(self, tab_size: int, use_spaces: bool, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self._tab_size = tab_size
        self._use_spaces = use_spaces

    def open_file(self, file_path: str, content: str) -> None:
        existing = self.index_of_path(file_path)
        if existing >= 0:
            self.setCurrentIndex(existing)
            return
        editor = MintEditor(self._tab_size, self._use_spaces)
        editor.setPlainText(content)
        editor.document().modificationChanged.connect(lambda modified, p=file_path: self.file_changed.emit(p, modified))
        editor.cursorPositionChanged.connect(lambda e=editor: self._emit_cursor(e))
        idx = self.addTab(editor, Path(file_path).name)
        self.setTabToolTip(idx, file_path)
        self.setCurrentIndex(idx)

    def new_unsaved(self, title: str = "untitled") -> None:
        editor = MintEditor(self._tab_size, self._use_spaces)
        editor.document().modificationChanged.connect(lambda modified, p=title: self.file_changed.emit(p, modified))
        editor.cursorPositionChanged.connect(lambda e=editor: self._emit_cursor(e))
        idx = self.addTab(editor, title)
        self.setTabToolTip(idx, "")
        self.setCurrentIndex(idx)

    def current_editor(self) -> Optional[MintEditor]:
        w = self.currentWidget()
        return w if isinstance(w, MintEditor) else None

    def current_path(self) -> str:
        idx = self.currentIndex()
        if idx < 0:
            return ""
        return self.tabToolTip(idx)

    def set_current_path(self, path: str):
        idx = self.currentIndex()
        if idx < 0:
            return
        self.setTabToolTip(idx, path)
        self.setTabText(idx, Path(path).name)

    def index_of_path(self, file_path: str) -> int:
        for i in range(self.count()):
            if self.tabToolTip(i) == file_path:
                return i
        return -1

    def mark_modified(self, file_path: str, modified: bool) -> None:
        idx = self.index_of_path(file_path)
        if idx < 0:
            return
        base = Path(file_path).name
        self.setTabText(idx, f"*{base}" if modified else base)

    def _emit_cursor(self, editor: MintEditor) -> None:
        cur = editor.textCursor()
        self.cursor_changed.emit(cur.blockNumber() + 1, cur.columnNumber() + 1)
