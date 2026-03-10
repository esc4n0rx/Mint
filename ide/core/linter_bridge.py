from __future__ import annotations

import re
from pathlib import Path
from typing import List

from mintlang.errors import MintError
from mintlang.linter import Linter
from mintlang.module_loader import ModuleLoader
from ide.models.diagnostics import Diagnostic


ISSUE_POS_RE = re.compile(r"(?:em|at)\s+(\d+):(\d+)")


class LinterBridge:
    def lint_file(self, file_path: str) -> List[Diagnostic]:
        p = Path(file_path)
        diagnostics: List[Diagnostic] = []
        if p.suffix.lower() != ".mint":
            return diagnostics
        try:
            program, issues = ModuleLoader(p).load()
            issues.extend(Linter().lint(program))
            for issue in issues:
                line, col = self._extract_position(issue.message)
                diagnostics.append(Diagnostic("warning", issue.message, str(p), line, col))
        except MintError as exc:
            line, col = self._extract_position(str(exc))
            diagnostics.append(Diagnostic("error", str(exc), str(p), line, col))
        except Exception as exc:  # pylint: disable=broad-except
            diagnostics.append(Diagnostic("error", f"Falha no linter: {exc}", str(p), 0, 0))
        return diagnostics

    @staticmethod
    def _extract_position(message: str) -> tuple[int, int]:
        match = ISSUE_POS_RE.search(message)
        if not match:
            return 0, 0
        return int(match.group(1)), int(match.group(2))
