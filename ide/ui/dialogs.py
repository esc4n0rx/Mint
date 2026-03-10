from __future__ import annotations

from PyQt5.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QSpinBox


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 32)
        self.font_size.setValue(settings.get("font_size", 12))
        self.tab_size = QSpinBox()
        self.tab_size.setRange(1, 8)
        self.tab_size.setValue(settings.get("tab_size", 2))
        self.use_spaces = QCheckBox("Usar espaços")
        self.use_spaces.setChecked(settings.get("use_spaces", True))
        self.auto_lint = QCheckBox("Lint automático ao salvar")
        self.auto_lint.setChecked(settings.get("auto_lint_on_save", False))
        self.runtime_path = QLineEdit(settings.get("runtime_path", ""))
        self.linter_path = QLineEdit(settings.get("linter_path", ""))

        form = QFormLayout(self)
        form.addRow("Tamanho da fonte", self.font_size)
        form.addRow("Tab size", self.tab_size)
        form.addRow(self.use_spaces)
        form.addRow(self.auto_lint)
        form.addRow("Runtime path", self.runtime_path)
        form.addRow("Linter path", self.linter_path)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addWidget(buttons)

    def values(self) -> dict:
        return {
            "font_size": self.font_size.value(),
            "tab_size": self.tab_size.value(),
            "use_spaces": self.use_spaces.isChecked(),
            "auto_lint_on_save": self.auto_lint.isChecked(),
            "runtime_path": self.runtime_path.text().strip(),
            "linter_path": self.linter_path.text().strip(),
        }
