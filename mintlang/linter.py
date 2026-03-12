from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from .ast_nodes import (
    Program, VarDeclStmt, WriteStmt, AddStmt, InsertStmt, IfStmt, AssignStmt, InputStmt, MoveStmt, QueryStmt, LoadStmt, SaveStmt, ExportStmt, WhileStmt, ForStmt, TryCatchStmt, ReturnStmt, CallStmt,
    DbCreateStmt, DbOpenStmt, DbCompactStmt, ShowTablesStmt, DescribeStmt, IndexCreateStmt, SelectCountStmt, TableCreateStmt, AppendValuesStmt, AppendStructStmt, SelectStmt, UpdateStmt, DeleteStmt, FuncDecl, Stmt,
    StructDecl, FieldAccessExpr, IndexAccessExpr, SizeCall, CountExpr, SumExpr, AvgExpr,
    Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, Binary, Unary, CallExpr, MintType
)
from .utils import extract_collection_inner, is_struct_collection, SYSTEM_MEMBERS

BUILTIN_TYPES = {"int", "float", "string", "char", "bool"}
RESERVED_NAMESPACE = "system"

@dataclass
class LintIssue:
    message: str
    severity: str = "error"


@dataclass
class FuncSignature:
    params: List[MintType]
    return_type: Optional[MintType]


class Linter:
    def lint(self, program: Program) -> List[LintIssue]:
        issues: List[LintIssue] = []
        structs = self._collect_structs(program.structs, issues)

        global_sym: Dict[str, MintType] = {}
        funcs: Dict[str, FuncSignature] = {}

        for func in program.funcs:
            if func.name == RESERVED_NAMESPACE:
                issues.append(LintIssue("system é um namespace reservado da linguagem."))
            if func.name in funcs:
                issues.append(LintIssue(f"Função '{func.name}' já declarada."))
                continue
            for param in func.params:
                if param.name == RESERVED_NAMESPACE:
                    issues.append(LintIssue("system é um namespace reservado da linguagem."))
                err = self._validate_declared_type(param.param_type, structs)
                if err is not None:
                    issues.append(LintIssue(f"Tipo inválido no parâmetro '{param.name}' da função '{func.name}': {err}"))
            if func.return_type is not None and not self._is_valid_value_type(func.return_type, structs):
                issues.append(LintIssue(f"Tipo de retorno inválido na função '{func.name}': {func.return_type}."))
            funcs[func.name] = FuncSignature(
                params=[p.param_type for p in func.params],
                return_type=func.return_type,
            )

        for d in program.decls:
            if d.name == RESERVED_NAMESPACE:
                issues.append(LintIssue("system é um namespace reservado da linguagem."))
                continue
            if d.name in global_sym:
                issues.append(LintIssue(f"Variável '{d.name}' declarada mais de uma vez."))
                continue
            err = self._validate_declared_type(d.vartype, structs)
            if err is not None:
                issues.append(LintIssue(f"Tipo inválido para variável '{d.name}': {err}"))
                continue
            global_sym[d.name] = d.vartype
            if d.initializer is not None:
                it = self._infer_type(d.initializer, global_sym, funcs, structs, issues)
                if it is not None and not self._is_assignment_compatible(d.vartype, it):
                    issues.append(LintIssue(
                        f"Incompatibilidade: '{d.name}' é {d.vartype} mas inicializa com {it}."
                    ))

        for st in program.body:
            self._lint_stmt(st, global_sym, funcs, structs, issues, current_return=None)

        for func in program.funcs:
            self._lint_function(func, global_sym, funcs, structs, issues)

        self._lint_mintdb_persistence(program.body, issues)
        return issues

    def _collect_structs(self, struct_decls: List[StructDecl], issues: List[LintIssue]) -> Dict[str, Dict[str, MintType]]:
        structs: Dict[str, Dict[str, MintType]] = {}
        for decl in struct_decls:
            if decl.name == RESERVED_NAMESPACE:
                issues.append(LintIssue("system é um namespace reservado da linguagem."))
                continue
            if decl.name in structs:
                issues.append(LintIssue(f"Struct '{decl.name}' já declarada."))
                continue
            fields: Dict[str, MintType] = {}
            for field in decl.fields:
                if field.name in fields:
                    issues.append(LintIssue(f"Campo '{field.name}' duplicado na struct '{decl.name}'."))
                    continue
                if field.field_type not in BUILTIN_TYPES:
                    issues.append(LintIssue(
                        f"Tipo inválido no campo '{field.name}' da struct '{decl.name}': {field.field_type}."
                    ))
                    continue
                fields[field.name] = field.field_type
            structs[decl.name] = fields
        return structs

    def _lint_function(
        self,
        func: FuncDecl,
        global_sym: Dict[str, MintType],
        funcs: Dict[str, FuncSignature],
        structs: Dict[str, Dict[str, MintType]],
        issues: List[LintIssue],
    ) -> None:
        local_sym = dict(global_sym)
        param_names = set()
        for param in func.params:
            if param.name in param_names:
                issues.append(LintIssue(f"Parâmetro '{param.name}' duplicado na função '{func.name}'."))
                continue
            param_names.add(param.name)
            local_sym[param.name] = param.param_type

        has_return_stmt = False
        for st in func.body:
            if isinstance(st, ReturnStmt):
                has_return_stmt = True
            self._lint_stmt(st, local_sym, funcs, structs, issues, current_return=func.return_type)

        if func.return_type is not None and not has_return_stmt:
            issues.append(LintIssue(f"Função '{func.name}' declara retorno {func.return_type}, mas não possui RETURN."))

    def _lint_stmt(
        self,
        stmt: Stmt,
        sym: Dict[str, MintType],
        funcs: Dict[str, FuncSignature],
        structs: Dict[str, Dict[str, MintType]],
        issues: List[LintIssue],
        current_return: Optional[MintType],
    ) -> None:
        if isinstance(stmt, VarDeclStmt):
            if stmt.name == RESERVED_NAMESPACE:
                issues.append(LintIssue("system é um namespace reservado da linguagem."))
                return
            if stmt.name in sym:
                issues.append(LintIssue(f"Variável '{stmt.name}' declarada mais de uma vez."))
                return
            err = self._validate_declared_type(stmt.vartype, structs)
            if err is not None:
                issues.append(LintIssue(f"Tipo inválido para variável '{stmt.name}': {err}"))
                return
            sym[stmt.name] = stmt.vartype
            if stmt.initializer is not None:
                it = self._infer_type(stmt.initializer, sym, funcs, structs, issues)
                if it is not None and not self._is_assignment_compatible(stmt.vartype, it):
                    issues.append(LintIssue(
                        f"Incompatibilidade: '{stmt.name}' é {stmt.vartype} mas inicializa com {it}."
                    ))
            return

        if isinstance(stmt, WriteStmt):
            self._infer_type(stmt.expr, sym, funcs, structs, issues)
            return

        if isinstance(stmt, AddStmt):
            collection_type = self._infer_type(stmt.collection, sym, funcs, structs, issues)
            value_type = self._infer_type(stmt.value, sym, funcs, structs, issues)
            inner_type = self._extract_collection_inner(collection_type, "list")
            if inner_type is None:
                issues.append(LintIssue("add requer uma coleção do tipo list<T>."))
                return
            if value_type is not None and not self._is_assignment_compatible(inner_type, value_type):
                issues.append(LintIssue(f"Tipo incompatível ao inserir em {collection_type}."))
            return

        if isinstance(stmt, InsertStmt):
            if not isinstance(stmt.table, VarRef):
                issues.append(LintIssue("insert exige coleção destino como variável (VarRef)."))
            table_type = self._infer_type(stmt.table, sym, funcs, structs, issues)
            value_type = self._infer_type(stmt.value, sym, funcs, structs, issues)
            inner_type = self._extract_collection_inner(table_type, "table")
            if inner_type is None:
                issues.append(LintIssue("insert requer uma coleção do tipo table<Struct>."))
                return
            if value_type is not None and value_type != inner_type:
                issues.append(LintIssue(f"Tipo incompatível ao inserir em {table_type}."))
            return

        if isinstance(stmt, CallStmt):
            sig = funcs.get(stmt.call.name)
            if sig is not None and sig.return_type is not None:
                issues.append(LintIssue(f"Função '{stmt.call.name}' retorna valor e deve ser usada em expressão."))
            self._lint_call(stmt.call, sym, funcs, structs, issues, require_value=False)
            return

        if isinstance(stmt, InputStmt):
            target_type = self._infer_input_target_type(stmt.target, sym, structs, issues)
            if target_type is None:
                self._infer_type(stmt.target, sym, funcs, structs, issues)
            return

        if isinstance(stmt, MoveStmt):
            var_type = sym.get(stmt.target)
            if var_type is None:
                issues.append(LintIssue(f"Move para variável não declarada: '{stmt.target}'."))
                self._infer_type(stmt.source, sym, funcs, structs, issues)
                return
            source_type = self._infer_type(stmt.source, sym, funcs, structs, issues)
            if source_type is not None and not self._is_assignment_compatible(var_type, source_type):
                issues.append(LintIssue(
                    f"Incompatibilidade no move: '{stmt.target}' é {var_type} mas recebeu {source_type}."
                ))
            return


        if isinstance(stmt, LoadStmt):
            dest_type = sym.get(stmt.destination)
            if dest_type is None:
                issues.append(LintIssue(f"Coleção '{stmt.destination}' não declarada."))
                return
            if not self._is_struct_collection(dest_type, structs):
                issues.append(LintIssue("LOAD exige variável do tipo table<Struct> ou list<Struct>."))
            return

        if isinstance(stmt, SaveStmt):
            source_type = sym.get(stmt.source)
            if source_type is None:
                issues.append(LintIssue(f"Coleção '{stmt.source}' não declarada."))
                return
            if not self._is_struct_collection(source_type, structs):
                issues.append(LintIssue("SAVE exige variável do tipo table<Struct> ou list<Struct>."))
            return

        if isinstance(stmt, ExportStmt):
            source_type = sym.get(stmt.source)
            if source_type is None:
                issues.append(LintIssue(f"Coleção '{stmt.source}' não declarada."))
                return
            if not self._is_struct_collection(source_type, structs):
                issues.append(LintIssue("EXPORT exige variável do tipo table<Struct> ou list<Struct>."))
            return
        if isinstance(stmt, DbCreateStmt):
            return

        if isinstance(stmt, DbOpenStmt):
            return

        if isinstance(stmt, DbCompactStmt):
            return

        if isinstance(stmt, ShowTablesStmt):
            if stmt.destination is not None:
                dt = sym.get(stmt.destination)
                if dt is None:
                    issues.append(LintIssue(f"Variável de destino não declarada: '{stmt.destination}'."))
            return

        if isinstance(stmt, DescribeStmt):
            if stmt.destination is not None:
                dt = sym.get(stmt.destination)
                if dt is None:
                    issues.append(LintIssue(f"Variável de destino não declarada: '{stmt.destination}'."))
            return

        if isinstance(stmt, IndexCreateStmt):
            return

        if isinstance(stmt, TableCreateStmt):
            if not stmt.columns:
                issues.append(LintIssue("TABLE CREATE exige ao menos uma coluna."))
            names = set()
            for c in stmt.columns:
                if c.name in names:
                    issues.append(LintIssue(f"Coluna duplicada em TABLE CREATE: {c.name}."))
                names.add(c.name)
                if c.col_type not in BUILTIN_TYPES:
                    issues.append(LintIssue(f"Tipo de coluna inválido: {c.col_type}."))
            return

        if isinstance(stmt, AppendValuesStmt):
            if not stmt.assignments:
                issues.append(LintIssue("APPEND VALUES exige pelo menos um campo."))
            for _, expr in stmt.assignments:
                self._infer_type(expr, sym, funcs, structs, issues)
            return

        if isinstance(stmt, AppendStructStmt):
            t = sym.get(stmt.struct_var)
            if t is None or t not in structs:
                issues.append(LintIssue("APPEND STRUCT exige variável de struct válida."))
            return

        if isinstance(stmt, SelectCountStmt):
            dest_type = sym.get(stmt.destination)
            if dest_type is None:
                issues.append(LintIssue(f"Destino '{stmt.destination}' não declarado."))
            elif dest_type != "int":
                issues.append(LintIssue("INTO do SELECT COUNT(*) deve ser int."))
            if stmt.condition is not None:
                ctype = self._infer_type(stmt.condition, sym, funcs, structs, issues)
                if ctype is not None and ctype != "bool":
                    issues.append(LintIssue("WHERE do SELECT COUNT deve resultar em bool."))
            return

        if isinstance(stmt, SelectStmt):
            dest_type = sym.get(stmt.destination)
            if dest_type is None:
                issues.append(LintIssue(f"Destino '{stmt.destination}' não declarado."))
            elif not dest_type.startswith("list<") and not dest_type.startswith("table<"):
                issues.append(LintIssue("INTO do SELECT deve ser list<Struct> ou table<Struct>."))
            return

        if isinstance(stmt, UpdateStmt):
            for _, expr in stmt.assignments:
                self._infer_type(expr, sym, funcs, structs, issues)
            return

        if isinstance(stmt, DeleteStmt):
            return

        if isinstance(stmt, QueryStmt):
            source_type = sym.get(stmt.source)
            if source_type is None:
                issues.append(LintIssue(f"Coleção '{stmt.source}' não declarada."))
                return

            source_struct = self._extract_collection_inner(source_type, "list")
            if source_struct is None:
                source_struct = self._extract_collection_inner(source_type, "table")
            if source_struct is None or source_struct not in structs:
                issues.append(LintIssue("QUERY exige list<Struct> ou table<Struct> como origem."))
                return

            dest_type = sym.get(stmt.destination)
            if dest_type is None:
                issues.append(LintIssue(f"Coleção '{stmt.destination}' não declarada."))
                return
            if dest_type != source_type:
                issues.append(LintIssue(f"Destino '{stmt.destination}' é incompatível com origem '{stmt.source}'."))

            condition_type = self._infer_type(
                stmt.condition,
                sym,
                funcs,
                structs,
                issues,
                query_struct_fields=structs[source_struct],
                query_struct_name=source_struct,
            )
            if condition_type is not None and condition_type != "bool":
                issues.append(LintIssue("WHERE da QUERY deve resultar em bool."))
            return

        if isinstance(stmt, IfStmt):
            for branch in stmt.branches:
                cond_type = self._infer_type(branch.condition, sym, funcs, structs, issues)
                if cond_type is not None and cond_type != "bool":
                    issues.append(LintIssue("Condição do if deve ser bool."))
                branch_sym = dict(sym)
                for inner in branch.body:
                    self._lint_stmt(inner, branch_sym, funcs, structs, issues, current_return)
            if stmt.else_body is not None:
                else_sym = dict(sym)
                for inner in stmt.else_body:
                    self._lint_stmt(inner, else_sym, funcs, structs, issues, current_return)
            return

        if isinstance(stmt, AssignStmt):
            target_type = self._infer_assign_target_type(stmt.target, sym, structs, issues)
            expr_type = self._infer_type(stmt.expr, sym, funcs, structs, issues)
            if target_type is not None and expr_type is not None and not self._is_assignment_compatible(target_type, expr_type):
                if isinstance(stmt.target, FieldAccessExpr):
                    issues.append(LintIssue(
                        f"Atribuição incompatível: campo '{stmt.target.field}' é {target_type}, mas recebeu {expr_type}."
                    ))
                else:
                    issues.append(LintIssue(
                        f"Incompatibilidade na atribuição: variável é {target_type} mas recebeu {expr_type}."
                    ))
            return

        if isinstance(stmt, WhileStmt):
            cond_type = self._infer_type(stmt.condition, sym, funcs, structs, issues)
            if cond_type is not None and cond_type != "bool":
                issues.append(LintIssue("Condição do while deve ser bool."))
            loop_sym = dict(sym)
            for inner in stmt.body:
                self._lint_stmt(inner, loop_sym, funcs, structs, issues, current_return)
            return

        if isinstance(stmt, ForStmt):
            if stmt.item_name == RESERVED_NAMESPACE:
                issues.append(LintIssue("system é um namespace reservado da linguagem."))
                return
            collection_type = self._infer_type(stmt.collection, sym, funcs, structs, issues)
            item_type = self._extract_collection_inner(collection_type, "list")
            if item_type is None:
                item_type = self._extract_collection_inner(collection_type, "table")
            if item_type is None:
                if collection_type is not None:
                    issues.append(LintIssue(f"FOR exige list<T> ou table<T>, mas recebeu {collection_type}."))
                return
            for_sym = dict(sym)
            for_sym[stmt.item_name] = item_type
            for inner in stmt.body:
                self._lint_stmt(inner, for_sym, funcs, structs, issues, current_return)
            return

        if isinstance(stmt, TryCatchStmt):
            try_sym = dict(sym)
            for inner in stmt.try_body:
                self._lint_stmt(inner, try_sym, funcs, structs, issues, current_return)
            catch_sym = dict(sym)
            for inner in stmt.catch_body:
                self._lint_stmt(inner, catch_sym, funcs, structs, issues, current_return)
            return

        if isinstance(stmt, ReturnStmt):
            if current_return is None:
                issues.append(LintIssue("RETURN fora de função."))
                self._infer_type(stmt.expr, sym, funcs, structs, issues)
                return
            expr_type = self._infer_type(stmt.expr, sym, funcs, structs, issues)
            if expr_type is not None and not self._is_assignment_compatible(current_return, expr_type):
                issues.append(LintIssue(
                    f"RETURN incompatível: função retorna {current_return}, mas expressão é {expr_type}."
                ))
            return

        issues.append(LintIssue(f"Statement não suportado no linter: {type(stmt).__name__}"))

    def _infer_input_target_type(
        self,
        expr: Expr,
        sym: Dict[str, MintType],
        structs: Dict[str, Dict[str, MintType]],
        issues: List[LintIssue],
    ) -> Optional[MintType]:
        if isinstance(expr, VarRef):
            var_type = sym.get(expr.name)
            if var_type is None:
                issues.append(LintIssue(f"Input para variável não declarada: '{expr.name}'."))
            return var_type
        if isinstance(expr, FieldAccessExpr):
            return self._resolve_field_type(expr, sym, structs, issues)
        issues.append(LintIssue("input aceita apenas variável ou acesso de campo (ex.: input(cliente.nome))."))
        return None

    def _infer_assign_target_type(
        self,
        expr: Expr,
        sym: Dict[str, MintType],
        structs: Dict[str, Dict[str, MintType]],
        issues: List[LintIssue],
    ) -> Optional[MintType]:
        if isinstance(expr, FieldAccessExpr) and self._is_system_access(expr):
            issues.append(LintIssue("Namespace system é somente leitura."))
            return None
        if isinstance(expr, VarRef):
            var_type = sym.get(expr.name)
            if var_type is None:
                issues.append(LintIssue(f"Atribuição para variável não declarada: '{expr.name}'."))
            return var_type
        if isinstance(expr, FieldAccessExpr):
            return self._resolve_field_type(expr, sym, structs, issues)
        issues.append(LintIssue("Destino de atribuição inválido."))
        return None

    def _resolve_field_type(
        self,
        expr: FieldAccessExpr,
        sym: Dict[str, MintType],
        structs: Dict[str, Dict[str, MintType]],
        issues: List[LintIssue],
    ) -> Optional[MintType]:
        base_type = self._infer_type(expr.base, sym, {}, structs, issues)
        if base_type is None:
            return None
        struct_fields = structs.get(base_type)
        if struct_fields is None:
            issues.append(LintIssue(f"Acesso de campo inválido: tipo '{base_type}' não é struct."))
            return None
        field_type = struct_fields.get(expr.field)
        if field_type is None:
            issues.append(LintIssue(f"Campo '{expr.field}' não existe na struct '{base_type}'."))
            return None
        return field_type

    def _infer_type(
        self,
        expr: Expr,
        sym: Dict[str, MintType],
        funcs: Dict[str, FuncSignature],
        structs: Dict[str, Dict[str, MintType]],
        issues: List[LintIssue],
        query_struct_fields: Optional[Dict[str, MintType]] = None,
        query_struct_name: Optional[str] = None,
    ) -> Optional[MintType]:
        if isinstance(expr, IntLit):
            return "int"
        if isinstance(expr, FloatLit):
            return "float"
        if isinstance(expr, StringLit):
            return "string"
        if isinstance(expr, CharLit):
            if len(expr.value) != 1:
                issues.append(LintIssue("Char deve conter exatamente 1 caractere."))
            return "char"
        if isinstance(expr, BoolLit):
            return "bool"
        if isinstance(expr, VarRef):
            if expr.name == RESERVED_NAMESPACE:
                issues.append(LintIssue("system é um namespace reservado da linguagem."))
                return None
            if query_struct_fields is not None:
                field_type = query_struct_fields.get(expr.name)
                if field_type is None:
                    issues.append(LintIssue(f"Campo '{expr.name}' não existe na struct '{query_struct_name}'."))
                    return None
                return field_type
            t = sym.get(expr.name)
            if t is None:
                issues.append(LintIssue(f"Uso de variável não declarada: '{expr.name}'."))
            return t
        if isinstance(expr, FieldAccessExpr):
            if self._is_system_access(expr):
                return self._infer_system_type(expr, issues)
            return self._resolve_field_type(expr, sym, structs, issues)
        if isinstance(expr, IndexAccessExpr):
            base_type = self._infer_type(expr.base, sym, funcs, structs, issues, query_struct_fields, query_struct_name)
            index_type = self._infer_type(expr.index, sym, funcs, structs, issues, query_struct_fields, query_struct_name)
            if index_type is not None and index_type != "int":
                issues.append(LintIssue("Índice deve ser numérico (int)."))
            if isinstance(expr.index, IntLit) and expr.index.value < 0:
                issues.append(LintIssue("Índice negativo pode causar erro em runtime.", severity="warning"))
            list_inner = self._extract_collection_inner(base_type, "list")
            if list_inner is not None:
                return list_inner
            table_inner = self._extract_collection_inner(base_type, "table")
            if table_inner is not None:
                return table_inner
            if base_type is not None:
                issues.append(LintIssue("Acesso por índice requer list<T> ou table<T>."))
            return None
        if isinstance(expr, SizeCall):
            collection_type = self._infer_type(expr.collection, sym, funcs, structs, issues, query_struct_fields, query_struct_name)
            if self._extract_collection_inner(collection_type, "list") is None and self._extract_collection_inner(collection_type, "table") is None:
                issues.append(LintIssue("size() aceita apenas list<T> ou table<T>."))
            return "int"
        if isinstance(expr, CountExpr):
            collection_type = self._infer_type(expr.collection, sym, funcs, structs, issues, query_struct_fields, query_struct_name)
            if self._extract_collection_inner(collection_type, "list") is None and self._extract_collection_inner(collection_type, "table") is None:
                issues.append(LintIssue("count() aceita apenas list<T> ou table<T>."))
            return "int"
        if isinstance(expr, SumExpr):
            return self._infer_aggregation_type(expr.target, sym, funcs, structs, issues, "sum")
        if isinstance(expr, AvgExpr):
            self._infer_aggregation_type(expr.target, sym, funcs, structs, issues, "avg")
            return "float"
        if isinstance(expr, CallExpr):
            return self._lint_call(expr, sym, funcs, structs, issues, require_value=True)

        if isinstance(expr, Unary):
            t = self._infer_type(expr.expr, sym, funcs, structs, issues, query_struct_fields, query_struct_name)
            if expr.op == "not":
                if t is not None and t != "bool":
                    issues.append(LintIssue(
                        f"Operador NOT requer bool, mas recebeu {t}."
                    ))
                return "bool" if t is not None else None
            if t is not None and t not in ("int", "float"):
                issues.append(LintIssue(
                    f"Operador unário '{expr.op}' usado em tipo {t} (esperado int ou float)."
                ))
            return t if t is not None else None

        if isinstance(expr, Binary):
            lt = self._infer_type(expr.left, sym, funcs, structs, issues, query_struct_fields, query_struct_name)
            rt = self._infer_type(expr.right, sym, funcs, structs, issues, query_struct_fields, query_struct_name)
            if expr.op in ("and", "or"):
                if lt is None or rt is None:
                    return None
                if lt != "bool" or rt != "bool":
                    issues.append(LintIssue(
                        f"Operador {expr.op.upper()} requer bool em ambos os lados, mas recebeu {lt} e {rt}."
                    ))
                    return None
                return "bool"

            if expr.op in ("==", "!=", "<", ">", "<=", ">="):
                if self._is_chained_comparison(expr):
                    issues.append(LintIssue(
                        "Comparação encadeada não suportada. Use parênteses e AND/OR."
                    ))
                    return None
                if lt is None or rt is None:
                    return None
                if lt in ("int", "float") and rt in ("int", "float"):
                    return "bool"
                if lt == "bool" and rt == "bool":
                    if expr.op not in ("==", "!="):
                        issues.append(LintIssue(
                            f"Comparação '{expr.op}' não suportada para bool."
                        ))
                        return None
                    return "bool"
                if lt in ("string", "char") and rt in ("string", "char"):
                    return "bool"
                issues.append(LintIssue(
                    f"Comparação entre tipos incompatíveis: {lt} {expr.op} {rt}."
                ))
                return None

            if expr.op == "+" and lt == "string" and rt == "string":
                return "string"

            if expr.op == "%":
                if lt is not None and lt != "int":
                    issues.append(LintIssue(
                        f"Operação '%' com lado esquerdo {lt} (esperado int)."
                    ))
                if rt is not None and rt != "int":
                    issues.append(LintIssue(
                        f"Operação '%' com lado direito {rt} (esperado int)."
                    ))
                if lt == "int" and rt == "int":
                    return "int"
                return None

            if lt is not None and lt not in ("int", "float"):
                issues.append(LintIssue(
                    f"Operação '{expr.op}' com lado esquerdo {lt} (esperado int ou float)."
                ))
            if rt is not None and rt not in ("int", "float"):
                issues.append(LintIssue(
                    f"Operação '{expr.op}' com lado direito {rt} (esperado int ou float)."
                ))
            if lt is None or rt is None:
                return None
            if lt == "float" or rt == "float":
                return "float"
            if lt == "int" and rt == "int":
                return "int"
            return None

        issues.append(LintIssue(f"Expressão desconhecida no linter: {type(expr).__name__}"))
        return None

    def _infer_aggregation_type(
        self,
        target: Expr,
        sym: Dict[str, MintType],
        funcs: Dict[str, FuncSignature],
        structs: Dict[str, Dict[str, MintType]],
        issues: List[LintIssue],
        op_name: str,
    ) -> Optional[MintType]:
        if isinstance(target, VarRef):
            collection_type = sym.get(target.name)
            if collection_type is None:
                issues.append(LintIssue(f"Coleção '{target.name}' não declarada."))
                return None
            inner = self._extract_collection_inner(collection_type, "list")
            if inner is None:
                inner = self._extract_collection_inner(collection_type, "table")
            if inner is None:
                issues.append(LintIssue(f"{op_name} exige list<T> ou table<T> como coleção."))
                return None
            if inner not in ("int", "float"):
                issues.append(LintIssue(f"{op_name} exige campo numérico, mas recebeu {inner}."))
                return None
            return inner if op_name == "sum" else "float"

        if isinstance(target, FieldAccessExpr) and isinstance(target.base, VarRef):
            collection_name = target.base.name
            collection_type = sym.get(collection_name)
            if collection_type is None:
                issues.append(LintIssue(f"Coleção '{collection_name}' não declarada."))
                return None
            inner = self._extract_collection_inner(collection_type, "list")
            if inner is None:
                inner = self._extract_collection_inner(collection_type, "table")
            if inner is None:
                issues.append(LintIssue(f"{op_name} exige list<T> ou table<T> como coleção."))
                return None
            struct_fields = structs.get(inner)
            if struct_fields is None:
                issues.append(LintIssue(f"{op_name} exige coleção de structs com campo numérico."))
                return None
            field_type = struct_fields.get(target.field)
            if field_type is None:
                issues.append(LintIssue(f"Campo '{target.field}' não existe na struct '{inner}'."))
                return None
            if field_type not in ("int", "float"):
                issues.append(LintIssue(f"sum exige campo numérico, mas '{target.field}' é {field_type}."))
                return None
            return field_type if op_name == "sum" else "float"

        issues.append(LintIssue(f"{op_name} exige coleção ou caminho no formato collection.field."))
        return None

    def _lint_call(
        self,
        call: CallExpr,
        sym: Dict[str, MintType],
        funcs: Dict[str, FuncSignature],
        structs: Dict[str, Dict[str, MintType]],
        issues: List[LintIssue],
        require_value: bool,
    ) -> Optional[MintType]:
        sig = funcs.get(call.name)
        if sig is None:
            issues.append(LintIssue(f"Função '{call.name}' não declarada."))
            for arg in call.args:
                self._infer_type(arg, sym, funcs, structs, issues)
            return None

        if len(call.args) != len(sig.params):
            issues.append(LintIssue(
                f"Função '{call.name}' espera {len(sig.params)} argumentos, mas recebeu {len(call.args)}."
            ))

        for i, arg in enumerate(call.args):
            arg_type = self._infer_type(arg, sym, funcs, structs, issues)
            if i < len(sig.params) and arg_type is not None:
                expected = sig.params[i]
                if not self._is_assignment_compatible(expected, arg_type):
                    issues.append(LintIssue(
                        f"Argumento {i+1} de '{call.name}' incompatível: esperado {expected}, recebeu {arg_type}."
                    ))

        if sig.return_type is None:
            if require_value:
                issues.append(LintIssue(f"Função '{call.name}' não retorna valor e não pode ser usada em expressão."))
            return None
        return sig.return_type

    def _lint_mintdb_persistence(self, body: List[Stmt], issues: List[LintIssue]) -> None:
        persistent_paths = set()
        table_primary_keys: Dict[str, List[str]] = {}
        fixed_seed_events: List[Tuple[str, Tuple[Any, ...], str]] = []

        for stmt in body:
            if isinstance(stmt, DbOpenStmt):
                persistent_paths.add(self._normalize_db_path(stmt.path))
            elif isinstance(stmt, TableCreateStmt):
                primary_keys = [c.name for c in stmt.columns if c.primary_key]
                if primary_keys:
                    table_primary_keys[stmt.table_name] = primary_keys
            elif isinstance(stmt, AppendValuesStmt):
                pks = table_primary_keys.get(stmt.table_name)
                if not pks:
                    continue
                assignments = {name: expr for name, expr in stmt.assignments}
                literal_key: List[Any] = []
                is_fixed = True
                for pk in pks:
                    lit = self._literal_value(assignments.get(pk))
                    if lit is None:
                        is_fixed = False
                        break
                    literal_key.append(lit)
                if is_fixed:
                    fixed_seed_events.append((stmt.table_name, tuple(literal_key), "APPEND"))
            elif isinstance(stmt, AppendStructStmt):
                pks = table_primary_keys.get(stmt.table_name)
                if pks:
                    fixed_seed_events.append((stmt.table_name, tuple(["<struct>"] * len(pks)), "APPEND STRUCT"))

        if not persistent_paths:
            return

        if fixed_seed_events:
            first_table, first_key, first_op = fixed_seed_events[0]
            issues.append(LintIssue(
                (
                    "Fluxo MintDB potencialmente não idempotente: script abre banco persistente e insere seed fixa "
                    f"na tabela '{first_table}' via {first_op} com chave primária {first_key}. "
                    "Reexecução pode falhar por violação de chave primária em runtime."
                ),
                severity="warning",
            ))
            issues.append(LintIssue(
                "Recomendação MintDB: proteja criação/seed (ex.: validar existência antes de APPEND ou usar fluxo idempotente dedicado).",
                severity="info",
            ))

    def _normalize_db_path(self, path: str) -> str:
        return path.strip().lower()

    def _literal_value(self, expr: Optional[Expr]) -> Optional[Any]:
        if expr is None:
            return None
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
        return None

    def _is_system_access(self, expr: FieldAccessExpr) -> bool:
        return isinstance(expr.base, VarRef) and expr.base.name == RESERVED_NAMESPACE

    def _infer_system_type(self, expr: FieldAccessExpr, issues: List[LintIssue]) -> Optional[MintType]:
        if not self._is_system_access(expr):
            return None
        member_type = SYSTEM_MEMBERS.get(expr.field)
        if member_type is None:
            issues.append(LintIssue(f"Membro '{expr.field}' não existe no namespace system."))
            return None
        return member_type

    def _is_assignment_compatible(self, target: MintType, source: MintType) -> bool:
        if target == source:
            return True
        return target == "float" and source == "int"

    def _is_valid_value_type(self, value_type: MintType, structs: Dict[str, Dict[str, MintType]]) -> bool:
        if value_type in BUILTIN_TYPES or value_type in structs:
            return True
        list_inner = self._extract_collection_inner(value_type, "list")
        if list_inner is not None:
            return self._is_valid_value_type(list_inner, structs)
        table_inner = self._extract_collection_inner(value_type, "table")
        if table_inner is not None:
            return table_inner in structs
        return False

    def _validate_declared_type(self, value_type: MintType, structs: Dict[str, Dict[str, MintType]]) -> Optional[str]:
        if value_type in BUILTIN_TYPES or value_type in structs:
            return None
        list_inner = self._extract_collection_inner(value_type, "list")
        if list_inner is not None:
            if not self._is_valid_value_type(list_inner, structs):
                return f"Tipo '{list_inner}' não existe."
            return None
        table_inner = self._extract_collection_inner(value_type, "table")
        if table_inner is not None:
            if table_inner not in structs:
                if table_inner in BUILTIN_TYPES:
                    return "TABLE exige tipo STRUCT."
                return f"Tipo '{table_inner}' não existe."
            return None
        return value_type

    def _is_struct_collection(self, value_type: Optional[MintType], structs: Dict[str, Dict[str, MintType]]) -> bool:
        return is_struct_collection(value_type, structs)

    def _extract_collection_inner(self, value_type: Optional[MintType], collection_name: str) -> Optional[MintType]:
        return extract_collection_inner(value_type, collection_name)

    def _is_chained_comparison(self, expr: Binary) -> bool:
        if expr.op not in ("==", "!=", "<", ">", "<=", ">="):
            return False
        return (
            isinstance(expr.left, Binary)
            and expr.left.op in ("==", "!=", "<", ">", "<=", ">=")
        )
