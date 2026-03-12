from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import csv
from typing import Dict, Any, Optional, List
from pathlib import Path
from .ast_nodes import (
    Program, Stmt, WriteStmt, AddStmt, InsertStmt, VarDeclStmt, IfStmt, AssignStmt, InputStmt, MoveStmt, QueryStmt, LoadStmt, SaveStmt, ExportStmt, WhileStmt, ForStmt, TryCatchStmt, ReturnStmt, CallStmt,
    DbCreateStmt, DbOpenStmt, DbCompactStmt, ShowTablesStmt, DescribeStmt, IndexCreateStmt, SelectCountStmt, TableCreateStmt, AppendValuesStmt, AppendStructStmt, SelectStmt, UpdateStmt, DeleteStmt,
    FuncDecl, StructDecl, FieldAccessExpr, IndexAccessExpr, SizeCall, CountExpr, SumExpr, AvgExpr,
    Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, Binary, Unary, CallExpr, MintType
)
from .errors import RuntimeMintError
from .mintdb import MintDB
from .utils import extract_collection_inner, convert_string_to_type, serialize_value

DEFAULTS: Dict[MintType, Any] = {
    "int": 0,
    "string": "",
    "bool": False,
    "float": 0.0,
    "char": "\0",
}

SYSTEM_NAMESPACE = "system"

class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


@dataclass
class Scope:
    types: Dict[str, MintType]
    env: Dict[str, Any]


class Interpreter:
    def __init__(self):
        self.globals = Scope(types={}, env={})
        self.scopes: List[Scope] = [self.globals]
        self.funcs: Dict[str, FuncDecl] = {}
        self.structs: Dict[str, Dict[str, MintType]] = {}
        self.db = MintDB()

    def run(self, program: Program) -> None:
        try:
            for struct in program.structs:
                self._register_struct(struct)

            for func in program.funcs:
                self.funcs[func.name] = func

            for decl in program.decls:
                self._exec_decl(decl)

            for stmt in program.body:
                self._exec_stmt(stmt)
        finally:
            self.db.close()

    def _register_struct(self, decl: StructDecl) -> None:
        fields: Dict[str, MintType] = {}
        for field in decl.fields:
            fields[field.name] = field.field_type
        self.structs[decl.name] = fields

    def _current_scope(self) -> Scope:
        return self.scopes[-1]

    def _push_scope(self, scope: Scope) -> None:
        self.scopes.append(scope)

    def _pop_scope(self) -> None:
        self.scopes.pop()

    def _resolve_type(self, name: str) -> Optional[MintType]:
        for scope in reversed(self.scopes):
            if name in scope.types:
                return scope.types[name]
        return None

    def _resolve_value(self, name: str) -> Any:
        for scope in reversed(self.scopes):
            if name in scope.env:
                return scope.env[name]
        raise RuntimeMintError(f"Variável '{name}' não declarada.")

    def _assign_value(self, name: str, value: Any) -> None:
        for scope in reversed(self.scopes):
            if name in scope.types:
                coerced = self._ensure_type(name, scope.types[name], value)
                scope.env[name] = coerced
                return
        raise RuntimeMintError(f"Variável '{name}' não declarada.")

    def _exec_decl(self, decl: VarDeclStmt) -> None:
        scope = self._current_scope()
        if decl.name in scope.types:
            raise RuntimeMintError(f"Variável '{decl.name}' já declarada.")

        scope.types[decl.name] = decl.vartype

        if decl.initializer is None:
            scope.env[decl.name] = self._default_value_for_type(decl.vartype)
            return

        val = self._eval(decl.initializer)
        scope.env[decl.name] = self._ensure_type(decl.name, decl.vartype, val)

    def _exec_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDeclStmt):
            self._exec_decl(stmt)
            return
        if isinstance(stmt, WriteStmt):
            val = self._eval(stmt.expr)
            print(self._format_value(val))
            return
        if isinstance(stmt, AddStmt):
            self._append_to_collection(stmt.collection, stmt.value, expected="list")
            return
        if isinstance(stmt, InsertStmt):
            self._append_to_collection(stmt.table, stmt.value, expected="table")
            return
        if isinstance(stmt, CallStmt):
            self._call_function(stmt.call, require_value=False)
            return
        if isinstance(stmt, IfStmt):
            self._exec_if(stmt)
            return
        if isinstance(stmt, AssignStmt):
            value = self._eval(stmt.expr)
            if isinstance(stmt.target, VarRef):
                self._assign_value(stmt.target.name, value)
            elif isinstance(stmt.target, FieldAccessExpr):
                self._assign_field_value(stmt.target, value)
            else:
                raise RuntimeMintError("Destino de atribuição inválido.")
            return
        if isinstance(stmt, InputStmt):
            target_name, var_type = self._resolve_input_target(stmt.target)
            raw = input()
            parsed = self._parse_input_value(target_name, var_type, raw)
            if isinstance(stmt.target, VarRef):
                self._assign_value(stmt.target.name, parsed)
            else:
                self._assign_field_value(stmt.target, parsed)
            return
        if isinstance(stmt, MoveStmt):
            self._assign_value(stmt.target, self._eval(stmt.source))
            return
        if isinstance(stmt, DbCreateStmt):
            self.db.create(stmt.path)
            return
        if isinstance(stmt, DbOpenStmt):
            self.db.open(stmt.path)
            return
        if isinstance(stmt, DbCompactStmt):
            self.db.compact()
            return
        if isinstance(stmt, TableCreateStmt):
            cols = [{"name": c.name, "type": c.col_type, "primary_key": c.primary_key, "auto_increment": c.auto_increment} for c in stmt.columns]
            self.db.create_table(stmt.table_name, cols)
            return
        if isinstance(stmt, IndexCreateStmt):
            self.db.create_index(stmt.index_name, stmt.table_name, stmt.column_name)
            return
        if isinstance(stmt, AppendValuesStmt):
            rec = {k: self._eval(v) for k, v in stmt.assignments}
            self.db.append_record(stmt.table_name, rec, operation="APPEND")
            return
        if isinstance(stmt, AppendStructStmt):
            v = self._resolve_value(stmt.struct_var)
            if not isinstance(v, dict) or "fields" not in v:
                raise RuntimeMintError("APPEND STRUCT exige variável struct válida.")
            self.db.append_record(stmt.table_name, dict(v["fields"]), operation="APPEND STRUCT")
            return
        if isinstance(stmt, ShowTablesStmt):
            rows = self.db.show_tables()
            if stmt.destination:
                self._assign_value(stmt.destination, rows)
            else:
                for row in rows:
                    print(f"- {row['table']} (active={row['active_records']}, removed={row['removed_records']})")
            return
        if isinstance(stmt, DescribeStmt):
            data = self.db.describe_table(stmt.table_name)
            if stmt.destination:
                self._assign_value(stmt.destination, data)
            else:
                print(f"TABLE {data['table']} (id={data['table_id']})")
                for c in data['columns']:
                    flags = []
                    if c.get('primary_key'):
                        flags.append('PRIMARY KEY')
                    if c.get('auto_increment'):
                        flags.append('AUTO_INCREMENT')
                    print(f"  - {c['name']} {c['type']} {' '.join(flags)}")
                for idx in data['indexes']:
                    print(f"  INDEX {idx['name']} ON {idx['column']}")
            return
        if isinstance(stmt, SelectCountStmt):
            if stmt.condition is None:
                total = self.db.count_records(stmt.table_name)
                self._assign_value(stmt.destination, total)
                return
            rows = self.db.select(stmt.table_name)
            count = 0
            for r in rows:
                scope = Scope(types={k: self._infer_runtime_type(v) for k, v in r.items()}, env=dict(r))
                self._push_scope(scope)
                try:
                    ok = self._eval(stmt.condition)
                finally:
                    self._pop_scope()
                if not isinstance(ok, bool):
                    raise RuntimeMintError("WHERE do SELECT COUNT deve resultar em bool.")
                if ok:
                    count += 1
            self._assign_value(stmt.destination, count)
            return
        if isinstance(stmt, SelectStmt):
            rows = self.db.select(stmt.table_name)
            if stmt.condition is not None:
                filtered = []
                for r in rows:
                    scope = Scope(types={k: self._infer_runtime_type(v) for k, v in r.items()}, env=dict(r))
                    self._push_scope(scope)
                    try:
                        ok = self._eval(stmt.condition)
                    finally:
                        self._pop_scope()
                    if not isinstance(ok, bool):
                        raise RuntimeMintError("WHERE do SELECT deve resultar em bool.")
                    if ok:
                        filtered.append(r)
                rows = filtered
            if stmt.columns != ["*"]:
                rows = [{c: row.get(c) for c in stmt.columns} for row in rows]
            self._assign_value(stmt.destination, rows)
            return
        if isinstance(stmt, UpdateStmt):
            def pred(r):
                scope = Scope(types={k: self._infer_runtime_type(v) for k, v in r.items()}, env=dict(r))
                self._push_scope(scope)
                try:
                    res = self._eval(stmt.condition)
                finally:
                    self._pop_scope()
                if not isinstance(res, bool):
                    raise RuntimeMintError("WHERE do UPDATE deve resultar em bool.")
                return res
            def upd(r):
                scope = Scope(types={k: self._infer_runtime_type(v) for k, v in r.items()}, env=dict(r))
                self._push_scope(scope)
                try:
                    for k, expr in stmt.assignments:
                        r[k] = self._eval(expr)
                finally:
                    self._pop_scope()
            self.db.update(stmt.table_name, upd, pred)
            return
        if isinstance(stmt, DeleteStmt):
            def pred(r):
                scope = Scope(types={k: self._infer_runtime_type(v) for k, v in r.items()}, env=dict(r))
                self._push_scope(scope)
                try:
                    res = self._eval(stmt.condition)
                finally:
                    self._pop_scope()
                if not isinstance(res, bool):
                    raise RuntimeMintError("WHERE do DELETE deve resultar em bool.")
                return res
            self.db.delete(stmt.table_name, pred)
            return
        if isinstance(stmt, QueryStmt):
            self._exec_query(stmt)
            return
        if isinstance(stmt, LoadStmt):
            self._exec_load(stmt)
            return
        if isinstance(stmt, SaveStmt):
            self._exec_save(stmt.source, stmt.path)
            return
        if isinstance(stmt, ExportStmt):
            self._exec_save(stmt.source, stmt.path)
            return
        if isinstance(stmt, WhileStmt):
            self._exec_while(stmt)
            return
        if isinstance(stmt, ForStmt):
            self._exec_for(stmt)
            return
        if isinstance(stmt, TryCatchStmt):
            self._exec_try_catch(stmt)
            return
        if isinstance(stmt, ReturnStmt):
            raise ReturnSignal(self._eval(stmt.expr))

        raise RuntimeMintError(f"Stmt não suportado: {type(stmt).__name__}")

    def _infer_runtime_type(self, value: Any) -> MintType:
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "string"
        return "string"

    def _exec_query(self, stmt: QueryStmt) -> None:
        source_type = self._resolve_type(stmt.source)
        if source_type is None:
            raise RuntimeMintError(f"Coleção '{stmt.source}' não declarada.")

        source_struct = self._extract_collection_inner(source_type, "list")
        if source_struct is None:
            source_struct = self._extract_collection_inner(source_type, "table")
        if source_struct is None or source_struct not in self.structs:
            raise RuntimeMintError("QUERY exige list<Struct> ou table<Struct> como origem.")

        dest_type = self._resolve_type(stmt.destination)
        if dest_type is None:
            raise RuntimeMintError(f"Coleção '{stmt.destination}' não declarada.")
        if dest_type != source_type:
            raise RuntimeMintError(f"Destino '{stmt.destination}' é incompatível com origem '{stmt.source}'.")

        source_val = self._resolve_value(stmt.source)
        dest_val = self._resolve_value(stmt.destination)
        if not isinstance(source_val, list) or not isinstance(dest_val, list):
            raise RuntimeMintError("QUERY exige coleções válidas em memória.")

        fields = self.structs[source_struct]
        for item in source_val:
            if not isinstance(item, dict) or item.get("__struct__") != source_struct or "fields" not in item:
                raise RuntimeMintError("QUERY recebeu item inválido para a struct de origem.")
            local_scope = Scope(types={}, env={})
            for field_name, field_type in fields.items():
                local_scope.types[field_name] = field_type
                local_scope.env[field_name] = item["fields"].get(field_name, self._default_value_for_type(field_type))
            self._push_scope(local_scope)
            try:
                cond_val = self._eval(stmt.condition)
            finally:
                self._pop_scope()
            if not isinstance(cond_val, bool):
                raise RuntimeMintError("WHERE da QUERY deve resultar em bool.")
            if cond_val:
                dest_val.append(item)

    def _exec_load(self, stmt: LoadStmt) -> None:
        collection_type = self._resolve_type(stmt.destination)
        if collection_type is None:
            raise RuntimeMintError(f"Coleção '{stmt.destination}' não declarada.")

        struct_name = self._extract_collection_inner(collection_type, "table")
        if struct_name is None:
            struct_name = self._extract_collection_inner(collection_type, "list")
        if struct_name is None or struct_name not in self.structs:
            raise RuntimeMintError("LOAD exige variável do tipo table<Struct> ou list<Struct>.")

        delimiter = self._delimiter_for_path(stmt.path)
        rows = self._read_delimited_file(self._safe_file_path(stmt.path), delimiter)
        header = rows[0] if rows else []
        self._validate_header(struct_name, header)

        loaded: List[Any] = []
        for row in rows[1:]:
            loaded.append(self._row_to_struct(struct_name, header, row))

        self._assign_value(stmt.destination, loaded)

    def _exec_save(self, source: str, path: str) -> None:
        collection_type = self._resolve_type(source)
        if collection_type is None:
            raise RuntimeMintError(f"Coleção '{source}' não declarada.")

        struct_name = self._extract_collection_inner(collection_type, "table")
        if struct_name is None:
            struct_name = self._extract_collection_inner(collection_type, "list")
        if struct_name is None or struct_name not in self.structs:
            raise RuntimeMintError("SAVE/EXPORT exige variável do tipo table<Struct> ou list<Struct>.")

        collection = self._resolve_value(source)
        if not isinstance(collection, list):
            raise RuntimeMintError("Coleção inválida para SAVE/EXPORT.")

        fields = list(self.structs[struct_name].keys())
        delimiter = self._delimiter_for_path(path)
        output_path = self._safe_file_path(path)
        if output_path.parent != Path('.'):
            output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(fields)
            for item in collection:
                if not isinstance(item, dict) or item.get('__struct__') != struct_name or 'fields' not in item:
                    raise RuntimeMintError("Coleção contém item inválido para serialização.")
                writer.writerow([self._serialize_field(item['fields'][name]) for name in fields])


    def _safe_file_path(self, path: str) -> Path:
        base = Path.cwd().resolve()
        candidate = (base / path).resolve()
        if candidate != base and base not in candidate.parents:
            raise RuntimeMintError("Path inválido: acesso fora do diretório atual não é permitido.")
        return candidate

    def _delimiter_for_path(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        if suffix == '.csv':
            return ','
        if suffix == '.txt':
            return ';'
        raise RuntimeMintError("Formato de arquivo não suportado. Use .csv ou .txt.")

    def _read_delimited_file(self, path: Path, delimiter: str) -> List[List[str]]:
        input_path = path
        if not input_path.exists():
            raise RuntimeMintError(f"Arquivo não encontrado: {path}")
        with input_path.open('r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter=delimiter)
            return [row for row in reader if row]

    def _validate_header(self, struct_name: str, header: List[str]) -> None:
        fields = self.structs[struct_name]
        expected = list(fields.keys())
        missing = [name for name in expected if name not in header]
        extra = [name for name in header if name not in fields]
        if missing or extra:
            parts: List[str] = []
            if missing:
                parts.append(f"faltando colunas: {', '.join(missing)}")
            if extra:
                parts.append(f"colunas desconhecidas: {', '.join(extra)}")
            raise RuntimeMintError(f"Cabeçalho incompatível para struct '{struct_name}': " + '; '.join(parts))

    def _row_to_struct(self, struct_name: str, header: List[str], row: List[str]) -> Dict[str, Any]:
        fields = self.structs[struct_name]
        data: Dict[str, Any] = {}
        for field_name, field_type in fields.items():
            idx = header.index(field_name)
            raw = row[idx] if idx < len(row) else ''
            data[field_name] = self._convert_loaded_value(raw, field_type, field_name)
        return {'__struct__': struct_name, 'fields': data}

    def _convert_loaded_value(self, raw: str, field_type: MintType, field_name: str) -> Any:
        try:
            return convert_string_to_type(raw, field_type, field_name)
        except ValueError as exc:
            raise RuntimeMintError(str(exc)) from exc


    def _serialize_field(self, val: Any) -> str:
        return serialize_value(val)


    def _resolve_input_target(self, target: Expr) -> tuple[str, MintType]:
        if isinstance(target, VarRef):
            var_type = self._resolve_type(target.name)
            if var_type is None:
                raise RuntimeMintError(f"Variável '{target.name}' não declarada.")
            return target.name, var_type
        if isinstance(target, FieldAccessExpr):
            field_type = self._resolve_field_type(target)
            return target.field, field_type
        raise RuntimeMintError("input aceita apenas referência de variável ou campo.")

    def _resolve_field_type(self, expr: FieldAccessExpr) -> MintType:
        if not isinstance(expr.base, VarRef):
            raise RuntimeMintError("Acesso de campo inválido.")
        base_type = self._resolve_type(expr.base.name)
        if base_type is None:
            raise RuntimeMintError(f"Variável '{expr.base.name}' não declarada.")
        fields = self.structs.get(base_type)
        if fields is None:
            raise RuntimeMintError(f"Tipo '{base_type}' não é struct.")
        field_type = fields.get(expr.field)
        if field_type is None:
            raise RuntimeMintError(f"Campo '{expr.field}' não existe na struct '{base_type}'.")
        return field_type

    def _resolve_field_ref(self, expr: FieldAccessExpr) -> tuple[Dict[str, Any], MintType, str]:
        if not isinstance(expr.base, VarRef):
            raise RuntimeMintError("Acesso de campo inválido.")
        base_name = expr.base.name
        base_value = self._resolve_value(base_name)
        base_type = self._resolve_type(base_name)
        if base_type is None:
            raise RuntimeMintError(f"Variável '{base_name}' não declarada.")
        fields = self.structs.get(base_type)
        if fields is None:
            raise RuntimeMintError(f"Tipo '{base_type}' não é struct.")
        if expr.field not in fields:
            raise RuntimeMintError(f"Campo '{expr.field}' não existe na struct '{base_type}'.")
        if not isinstance(base_value, dict) or "fields" not in base_value:
            raise RuntimeMintError(f"Valor de '{base_name}' não é uma instância de struct válida.")
        return base_value["fields"], fields[expr.field], expr.field

    def _assign_field_value(self, expr: FieldAccessExpr, value: Any) -> None:
        field_map, field_type, field_name = self._resolve_field_ref(expr)
        field_map[field_name] = self._ensure_type(field_name, field_type, value)

    def _exec_if(self, stmt: IfStmt) -> None:
        for branch in stmt.branches:
            cond = self._eval(branch.condition)
            if not isinstance(cond, bool):
                raise RuntimeMintError("Condição do if deve ser bool.")
            if cond:
                for inner in branch.body:
                    self._exec_stmt(inner)
                return
        if stmt.else_body is not None:
            for inner in stmt.else_body:
                self._exec_stmt(inner)

    def _exec_while(self, stmt: WhileStmt) -> None:
        while True:
            cond = self._eval(stmt.condition)
            if not isinstance(cond, bool):
                raise RuntimeMintError("Condição do while deve ser bool.")
            if not cond:
                return
            for inner in stmt.body:
                self._exec_stmt(inner)

    def _exec_for(self, stmt: ForStmt) -> None:
        collection_val = self._eval(stmt.collection)
        if not isinstance(collection_val, list):
            raise RuntimeMintError("FOR exige list<T> ou table<T>.")

        item_type = None
        if isinstance(stmt.collection, VarRef):
            collection_type = self._resolve_type(stmt.collection.name)
            if collection_type is not None:
                item_type = self._extract_collection_inner(collection_type, "list")
                if item_type is None:
                    item_type = self._extract_collection_inner(collection_type, "table")
        if item_type is None:
            item_type = "string"

        for item in collection_val:
            loop_scope = Scope(types={stmt.item_name: item_type}, env={stmt.item_name: self._ensure_type(stmt.item_name, item_type, item)})
            self._push_scope(loop_scope)
            try:
                for inner in stmt.body:
                    self._exec_stmt(inner)
            finally:
                self._pop_scope()

    def _exec_try_catch(self, stmt: TryCatchStmt) -> None:
        try:
            for inner in stmt.try_body:
                self._exec_stmt(inner)
        except RuntimeMintError:
            for inner in stmt.catch_body:
                self._exec_stmt(inner)

    def _call_function(self, expr: CallExpr, require_value: bool = True) -> Any:
        func = self.funcs.get(expr.name)
        if func is None:
            raise RuntimeMintError(f"Função '{expr.name}' não declarada.")

        if len(expr.args) != len(func.params):
            raise RuntimeMintError(
                f"Função '{expr.name}' espera {len(func.params)} argumentos, mas recebeu {len(expr.args)}."
            )

        arg_values = [self._eval(arg) for arg in expr.args]

        local_scope = Scope(types={}, env={})
        for i, param in enumerate(func.params):
            local_scope.types[param.name] = param.param_type
            local_scope.env[param.name] = self._ensure_type(param.name, param.param_type, arg_values[i])

        self._push_scope(local_scope)
        try:
            for st in func.body:
                self._exec_stmt(st)
            if func.return_type is not None:
                raise RuntimeMintError(f"Função '{func.name}' deveria retornar {func.return_type}, mas terminou sem RETURN.")
            return None
        except ReturnSignal as rs:
            if func.return_type is None:
                raise RuntimeMintError(f"Função '{func.name}' não declara retorno, mas executou RETURN.")
            return self._ensure_type(f"return({func.name})", func.return_type, rs.value)
        finally:
            self._pop_scope()

    def _default_value_for_type(self, mint_type: MintType) -> Any:
        if self._extract_collection_inner(mint_type, "list") is not None:
            return []
        if self._extract_collection_inner(mint_type, "table") is not None:
            return []
        if mint_type in DEFAULTS:
            return DEFAULTS[mint_type]
        struct_fields = self.structs.get(mint_type)
        if struct_fields is None:
            raise RuntimeMintError(f"Tipo não suportado: {mint_type}.")
        values: Dict[str, Any] = {}
        for field_name, field_type in struct_fields.items():
            values[field_name] = self._default_value_for_type(field_type)
        return {"__struct__": mint_type, "fields": values}

    @staticmethod
    def _is_numeric_value(value: Any) -> bool:
        return type(value) in (int, float)

    @staticmethod
    def _is_int_value(value: Any) -> bool:
        return type(value) is int

    def _eval(self, expr: Expr) -> Any:
        if isinstance(expr, IntLit):
            return expr.value
        if isinstance(expr, FloatLit):
            return expr.value
        if isinstance(expr, StringLit):
            return expr.value
        if isinstance(expr, CharLit):
            return expr.value
        if isinstance(expr, BoolLit):
            return expr.value
        if isinstance(expr, VarRef):
            return self._resolve_value(expr.name)
        if isinstance(expr, FieldAccessExpr):
            system_value = self._eval_system_field(expr)
            if system_value is not None:
                return system_value
            base_value = self._eval(expr.base)
            if not isinstance(base_value, dict) or "fields" not in base_value:
                raise RuntimeMintError("Acesso de campo inválido: base não é struct.")
            if expr.field not in base_value["fields"]:
                struct_name = base_value.get("__struct__", "desconhecida")
                raise RuntimeMintError(f"Campo '{expr.field}' não existe na struct '{struct_name}'.")
            return base_value["fields"][expr.field]
        if isinstance(expr, IndexAccessExpr):
            collection = self._eval(expr.base)
            index = self._eval(expr.index)
            if not isinstance(index, int):
                raise RuntimeMintError("Índice deve ser numérico (int).")
            if not isinstance(collection, list):
                raise RuntimeMintError("Acesso por índice requer list<T> ou table<T>.")
            if index < 0 or index >= len(collection):
                raise RuntimeMintError("Índice fora dos limites.")
            return collection[index]
        if isinstance(expr, SizeCall):
            collection = self._eval(expr.collection)
            if not isinstance(collection, list):
                raise RuntimeMintError("size() aceita apenas list<T> ou table<T>.")
            return len(collection)
        if isinstance(expr, CountExpr):
            collection = self._eval(expr.collection)
            if not isinstance(collection, list):
                raise RuntimeMintError("count() aceita apenas list<T> ou table<T>.")
            return len(collection)
        if isinstance(expr, SumExpr):
            return self._eval_aggregation(expr.target, mode="sum")
        if isinstance(expr, AvgExpr):
            return self._eval_aggregation(expr.target, mode="avg")
        if isinstance(expr, CallExpr):
            return self._call_function(expr, require_value=True)

        if isinstance(expr, Unary):
            v = self._eval(expr.expr)
            if expr.op == "not":
                if not isinstance(v, bool):
                    raise RuntimeMintError("Operador NOT requer bool.")
                return not v
            if not isinstance(v, (int, float)):
                raise RuntimeMintError(f"Operador unário '{expr.op}' requer int ou float.")
            if expr.op == "-":
                return -v
            if expr.op == "+":
                return +v
            raise RuntimeMintError(f"Operador unário inválido: {expr.op}")

        if isinstance(expr, Binary):
            left = self._eval(expr.left)
            if expr.op in ("and", "or"):
                return self._eval_logical(expr.op, left, expr.right)

            right = self._eval(expr.right)

            if expr.op in ("==", "!=", "<", ">", "<=", ">="):
                return self._eval_comparison(expr.op, left, right)

            if expr.op == "+":
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                if self._is_numeric_value(left) and self._is_numeric_value(right):
                    return left + right
                raise RuntimeMintError("Operação '+' requer números ou strings compatíveis.")
            if expr.op == "-":
                if self._is_numeric_value(left) and self._is_numeric_value(right):
                    return left - right
                raise RuntimeMintError("Operação '-' requer int ou float em ambos os lados.")
            if expr.op == "*":
                if self._is_numeric_value(left) and self._is_numeric_value(right):
                    return left * right
                raise RuntimeMintError("Operação '*' requer int ou float em ambos os lados.")
            if expr.op == "/":
                if right == 0:
                    raise RuntimeMintError("Divisão por zero.")
                if self._is_numeric_value(left) and self._is_numeric_value(right):
                    return float(left) / float(right)
                raise RuntimeMintError("Operação '/' requer int ou float em ambos os lados.")
            if expr.op == "%":
                if not self._is_int_value(left) or not self._is_int_value(right):
                    raise RuntimeMintError("Operação '%' requer int em ambos os lados.")
                if right == 0:
                    raise RuntimeMintError("Módulo por zero.")
                return left % right

            raise RuntimeMintError(f"Operador inválido: {expr.op}")

        raise RuntimeMintError(f"Expr não suportada: {type(expr).__name__}")

    def _eval_system_field(self, expr: FieldAccessExpr) -> Optional[Any]:
        if not isinstance(expr.base, VarRef) or expr.base.name != SYSTEM_NAMESPACE:
            return None
        now = datetime.now()
        system_values: Dict[str, Any] = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": int(now.timestamp()),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "weekday": now.isoweekday(),
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
        }
        if expr.field not in system_values:
            raise RuntimeMintError(f"Membro '{expr.field}' não existe no namespace system.")
        return system_values[expr.field]

    def _eval_aggregation(self, target: Expr, mode: str) -> Any:
        values: List[float | int] = []

        if isinstance(target, VarRef):
            collection = self._resolve_value(target.name)
            if not isinstance(collection, list):
                raise RuntimeMintError(f"{mode} exige list<T> ou table<T> como coleção.")
            for item in collection:
                if not isinstance(item, (int, float)):
                    raise RuntimeMintError(f"{mode} exige valores numéricos.")
                values.append(item)
        elif isinstance(target, FieldAccessExpr) and isinstance(target.base, VarRef):
            collection = self._resolve_value(target.base.name)
            if not isinstance(collection, list):
                raise RuntimeMintError(f"{mode} exige list<T> ou table<T> como coleção.")
            for item in collection:
                if not isinstance(item, dict) or "fields" not in item or target.field not in item["fields"]:
                    raise RuntimeMintError(f"Campo '{target.field}' não existe na coleção.")
                value = item["fields"][target.field]
                if not isinstance(value, (int, float)):
                    raise RuntimeMintError(f"{mode} exige campo numérico.")
                values.append(value)
        else:
            raise RuntimeMintError(f"{mode} exige coleção ou caminho no formato collection.field.")

        if mode == "sum":
            total: float | int = 0
            for value in values:
                total += value
            return total

        if len(values) == 0:
            raise RuntimeMintError("avg não pode ser calculado em coleção vazia.")
        total = 0.0
        for value in values:
            total += float(value)
        return total / len(values)

    def _eval_logical(self, op: str, left: Any, right_expr: Expr) -> bool:
        if not isinstance(left, bool):
            raise RuntimeMintError(f"Operador {op.upper()} requer bool em ambos os lados.")
        if op == "and":
            if not left:
                return False
            right_val = self._eval(right_expr)
            if not isinstance(right_val, bool):
                raise RuntimeMintError("Operador AND requer bool em ambos os lados.")
            return right_val
        if op == "or":
            if left:
                return True
            right_val = self._eval(right_expr)
            if not isinstance(right_val, bool):
                raise RuntimeMintError("Operador OR requer bool em ambos os lados.")
            return right_val
        raise RuntimeMintError(f"Operador lógico inválido: {op}")

    def _eval_comparison(self, op: str, left: Any, right: Any) -> bool:
        if isinstance(left, bool) or isinstance(right, bool):
            if not (isinstance(left, bool) and isinstance(right, bool)):
                raise RuntimeMintError(f"Comparação entre tipos incompatíveis: {type(left).__name__} {op} {type(right).__name__}.")
            if op not in ("==", "!="):
                raise RuntimeMintError(f"Comparação '{op}' não suportada para bool.")
            return left == right if op == "==" else left != right

        if isinstance(left, (int, float)) or isinstance(right, (int, float)):
            if not (isinstance(left, (int, float)) and isinstance(right, (int, float))):
                raise RuntimeMintError(f"Comparação entre tipos incompatíveis: {type(left).__name__} {op} {type(right).__name__}.")
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
            raise RuntimeMintError(f"Operador inválido: {op}")

        if isinstance(left, str) and isinstance(right, str):
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
            raise RuntimeMintError(f"Operador inválido: {op}")

        raise RuntimeMintError(f"Comparação entre tipos incompatíveis: {type(left).__name__} {op} {type(right).__name__}.")

    def _ensure_type(self, name: str, t: MintType, val: Any) -> Any:
        list_inner = self._extract_collection_inner(t, "list")
        if list_inner is not None:
            if not isinstance(val, list):
                raise RuntimeMintError(f"'{name}' é {t}, mas recebeu valor incompatível.")
            return val
        table_inner = self._extract_collection_inner(t, "table")
        if table_inner is not None:
            if not isinstance(val, list):
                raise RuntimeMintError(f"'{name}' é {t}, mas recebeu valor incompatível.")
            return val
        if t == "int" and not isinstance(val, int):
            raise RuntimeMintError(f"'{name}' é int, mas recebeu {type(val).__name__}.")
        if t == "string" and not isinstance(val, str):
            raise RuntimeMintError(f"'{name}' é string, mas recebeu {type(val).__name__}.")
        if t == "bool" and not isinstance(val, bool):
            raise RuntimeMintError(f"'{name}' é bool, mas recebeu {type(val).__name__}.")
        if t == "float":
            if isinstance(val, int):
                return float(val)
            if not isinstance(val, float):
                raise RuntimeMintError(f"'{name}' é float, mas recebeu {type(val).__name__}.")
        if t == "char":
            if not isinstance(val, str):
                raise RuntimeMintError(f"'{name}' é char, mas recebeu {type(val).__name__}.")
            if len(val) != 1:
                raise RuntimeMintError(f"'{name}' é char, mas recebeu string com {len(val)} caracteres.")
        if t in self.structs:
            if not isinstance(val, dict) or val.get("__struct__") != t:
                raise RuntimeMintError(f"'{name}' é {t}, mas recebeu valor incompatível.")
            return val
        return val

    def _parse_input_value(self, name: str, vartype: MintType, raw: str) -> Any:
        if vartype == "string":
            return raw
        if vartype == "int":
            try:
                return int(raw)
            except ValueError:
                raise RuntimeMintError(f"Input inválido para variável '{name}': esperado int.")
        if vartype == "float":
            try:
                return float(raw)
            except ValueError:
                raise RuntimeMintError(f"Input inválido para variável '{name}': esperado float.")
        if vartype == "bool":
            if raw == "true":
                return True
            if raw == "false":
                return False
            raise RuntimeMintError(f"Input inválido para variável '{name}': esperado bool (true/false).")
        if vartype == "char":
            if len(raw) != 1:
                raise RuntimeMintError(f"Input inválido para variável '{name}': esperado char.")
            return raw
        raise RuntimeMintError(f"Tipo de input não suportado para '{name}': {vartype}.")

    def _format_value(self, val: Any) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, dict) and "fields" in val:
            return str(val["fields"])
        return str(val)

    def _append_to_collection(self, collection_expr: Expr, value_expr: Expr, expected: str) -> None:
        if not isinstance(collection_expr, VarRef):
            raise RuntimeMintError("Coleção de destino deve ser uma variável.")
        collection_name = collection_expr.name
        collection_type = self._resolve_type(collection_name)
        if collection_type is None:
            raise RuntimeMintError(f"Variável '{collection_name}' não declarada.")
        inner_type = self._extract_collection_inner(collection_type, expected)
        if inner_type is None:
            raise RuntimeMintError(f"Operação inválida: esperado {expected}<T>.")
        collection_val = self._resolve_value(collection_name)
        if not isinstance(collection_val, list):
            raise RuntimeMintError(f"Valor de '{collection_name}' não é coleção válida.")
        value = self._eval(value_expr)
        collection_val.append(self._ensure_type(collection_name, inner_type, value))

    def _extract_collection_inner(self, value_type: MintType, collection_name: str) -> Optional[MintType]:
        return extract_collection_inner(value_type, collection_name)
