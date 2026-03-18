from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ide.models.execution_request import ExecutionRecord, ExecutionRequest
from ide.services.workbench_service import WorkbenchService


class ExecutionService:
    def __init__(self, workbench: WorkbenchService) -> None:
        self.workbench = workbench
        self.history_file = self.workbench.metadata_dir / 'execution_history.json'

    def list_history(self) -> list[ExecutionRecord]:
        raw = self.workbench.read_json(self.history_file, [])
        return [ExecutionRecord(**item) for item in raw]

    def add_record(self, request: ExecutionRequest) -> ExecutionRecord:
        record = ExecutionRecord(
            timestamp=datetime.utcnow().isoformat(timespec='seconds') + 'Z',
            target_path=request.target_path,
            mode=request.mode,
            parameters=list(request.parameters),
            status='queued',
        )
        raw = self.workbench.read_json(self.history_file, [])
        raw.insert(0, record.__dict__)
        self.workbench.write_json(self.history_file, raw[:30])
        return record

    def update_record(self, record: ExecutionRecord) -> None:
        raw = self.workbench.read_json(self.history_file, [])
        for item in raw:
            if item.get('timestamp') == record.timestamp and item.get('target_path') == record.target_path:
                item.update(record.__dict__)
                break
        self.workbench.write_json(self.history_file, raw)

    def log_output(self, name: str, content: str) -> Path:
        safe_name = Path(name).stem.replace(' ', '_').lower() or 'execution'
        file_path = self.workbench.logs_dir / f'{safe_name}.log'
        file_path.write_text(content, encoding='utf-8')
        return file_path
