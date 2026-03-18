from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WorkbenchService:
    """Gerencia a estrutura persistida do ERP Workbench dentro do workspace."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()
        self.workbench_dir = self.workspace / ".mint_workbench"
        self.tables_dir = self.workbench_dir / "tables"
        self.metadata_dir = self.workbench_dir / "metadata"
        self.logs_dir = self.workbench_dir / "logs"
        self.modules_dir = self.workspace / "modules"
        self.programs_dir = self.workspace / "programs"
        self.generated_dir = self.workspace / "generated"
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        for path in [
            self.workbench_dir,
            self.tables_dir,
            self.metadata_dir,
            self.logs_dir,
            self.modules_dir,
            self.programs_dir,
            self.generated_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
