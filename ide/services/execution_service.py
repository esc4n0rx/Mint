from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ide.models.execution_request import ExecutionRecord, ExecutionRequest, FunctionParameter
from ide.services.workbench_service import WorkbenchService
from mintlang.module_loader import ModuleLoader


class ExecutionService:
    def __init__(self, workbench: WorkbenchService) -> None:
        self.workbench = workbench
        self.history_file = self.workbench.metadata_dir / 'execution_history.json'
        self.runtime_dir = self.workbench.metadata_dir / 'runtime'
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

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
            metadata={'function_name': request.function_name} if request.function_name else {},
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

    def list_functions(self, target_path: str) -> list[tuple[str, list[FunctionParameter], str | None]]:
        path = Path(target_path)
        if not path.exists() or path.suffix.lower() != '.mint':
            return []
        program, _issues = ModuleLoader(path).load()
        return [
            (func.name, [FunctionParameter(name=param.name, param_type=str(param.param_type)) for param in func.params], func.return_type)
            for func in program.funcs
        ]

    def build_function_launcher(self, source_path: str, function_name: str, parameters: list[str]) -> Path:
        function_specs = {name: (params, return_type) for name, params, return_type in self.list_functions(source_path)}
        params, _return_type = function_specs.get(function_name, (None, None))
        if params is None:
            raise ValueError(f'Função não encontrada: {function_name}')
        if len(params) != len(parameters):
            raise ValueError(f'Função {function_name} espera {len(params)} parâmetro(s).')

        script_path = self.runtime_dir / f'call_{Path(source_path).stem}_{function_name}.py'
        script_path.write_text(self._python_launcher_source(source_path, function_name, params, parameters), encoding='utf-8')
        return script_path

    def _python_launcher_source(self, source_path: str, function_name: str, params: list[FunctionParameter], values: list[str]) -> str:
        serialized_values = repr(values)
        serialized_types = repr([(param.name, param.param_type) for param in params])
        source = repr(str(Path(source_path).resolve()))
        workspace = repr(str(self.workbench.workspace))
        return f"""
from pathlib import Path
import sys

SOURCE_PATH = {source}
WORKSPACE = {workspace}
FUNCTION_NAME = {function_name!r}
PARAM_TYPES = {serialized_types}
RAW_VALUES = {serialized_values}

sys.path.insert(0, WORKSPACE)

from mintlang.module_loader import ModuleLoader
from mintlang.interpreter import Interpreter
from mintlang.ast_nodes import CallExpr, StringLit, IntLit, FloatLit, BoolLit, CharLit


def build_expr(raw, mint_type):
    if mint_type in ('int', 'long'):
        return IntLit(int(raw or '0'))
    if mint_type in ('float', 'double'):
        return FloatLit(float(raw or '0'))
    if mint_type == 'bool':
        return BoolLit(raw.strip().lower() == 'true')
    if mint_type == 'char':
        return CharLit((raw or ' ')[:1])
    if mint_type == 'decimal':
        return StringLit(raw or '0')
    if mint_type == 'json':
        return StringLit(raw or '{{}}')
    return StringLit(raw)

path = Path(SOURCE_PATH)
program, issues = ModuleLoader(path).load()
if issues:
    for issue in issues:
        print(issue.message)
    raise SystemExit(1)

interpreter = Interpreter()
for struct in program.structs:
    interpreter._register_struct(struct)
for func in program.funcs:
    interpreter.funcs[func.name] = func
for decl in program.decls:
    interpreter._exec_decl(decl)

args = []
for (_, mint_type), raw in zip(PARAM_TYPES, RAW_VALUES):
    args.append(build_expr(raw, mint_type))
result = interpreter._call_function(CallExpr(name=FUNCTION_NAME, args=args), require_value=False)
if result is not None:
    print(interpreter._format_value(result))
else:
    print('Function executed')
"""
