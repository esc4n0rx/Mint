from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from .ast_nodes import (
    Program, VarDeclStmt, WriteStmt, IfStmt, AssignStmt, InputStmt, MoveStmt, WhileStmt, ReturnStmt, CallStmt, FuncDecl, Stmt,
    StructDecl, FieldAccessExpr,
    Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, Binary, Unary, CallExpr, MintType
)

BUILTIN_TYPES = {"int", "float", "string", "char", "bool"}


@dataclass
class LintIssue:
    message: str


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
            if func.name in funcs:
                issues.append(LintIssue(f"Função '{func.name}' já declarada."))
                continue
            for param in func.params:
                if not self._is_valid_value_type(param.param_type, structs):
                    issues.append(LintIssue(f"Tipo inválido no parâmetro '{param.name}' da função '{func.name}': {param.param_type}."))
            if func.return_type is not None and not self._is_valid_value_type(func.return_type, structs):
                issues.append(LintIssue(f"Tipo de retorno inválido na função '{func.name}': {func.return_type}."))
            funcs[func.name] = FuncSignature(
                params=[p.param_type for p in func.params],
                return_type=func.return_type,
            )

        for d in program.decls:
            if d.name in global_sym:
                issues.append(LintIssue(f"Variável '{d.name}' declarada mais de uma vez."))
                continue
            if not self._is_valid_value_type(d.vartype, structs):
                issues.append(LintIssue(f"Tipo inválido para variável '{d.name}': {d.vartype}."))
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

        return issues

    def _collect_structs(self, struct_decls: List[StructDecl], issues: List[LintIssue]) -> Dict[str, Dict[str, MintType]]:
        structs: Dict[str, Dict[str, MintType]] = {}
        for decl in struct_decls:
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
            if stmt.name in sym:
                issues.append(LintIssue(f"Variável '{stmt.name}' declarada mais de uma vez."))
                return
            if not self._is_valid_value_type(stmt.vartype, structs):
                issues.append(LintIssue(f"Tipo inválido para variável '{stmt.name}': {stmt.vartype}."))
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
            t = sym.get(expr.name)
            if t is None:
                issues.append(LintIssue(f"Uso de variável não declarada: '{expr.name}'."))
            return t
        if isinstance(expr, FieldAccessExpr):
            return self._resolve_field_type(expr, sym, structs, issues)
        if isinstance(expr, CallExpr):
            return self._lint_call(expr, sym, funcs, structs, issues, require_value=True)

        if isinstance(expr, Unary):
            t = self._infer_type(expr.expr, sym, funcs, structs, issues)
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
            lt = self._infer_type(expr.left, sym, funcs, structs, issues)
            rt = self._infer_type(expr.right, sym, funcs, structs, issues)
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

    def _is_assignment_compatible(self, target: MintType, source: MintType) -> bool:
        if target == source:
            return True
        return target == "float" and source == "int"

    def _is_valid_value_type(self, value_type: MintType, structs: Dict[str, Dict[str, MintType]]) -> bool:
        return value_type in BUILTIN_TYPES or value_type in structs

    def _is_chained_comparison(self, expr: Binary) -> bool:
        if expr.op not in ("==", "!=", "<", ">", "<=", ">="):
            return False
        return (
            isinstance(expr.left, Binary)
            and expr.left.op in ("==", "!=", "<", ">", "<=", ">=")
        )
