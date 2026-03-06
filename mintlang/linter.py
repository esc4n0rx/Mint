from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from .ast_nodes import (
    Program, VarDeclStmt, WriteStmt, IfStmt, AssignStmt, WhileStmt, ReturnStmt, CallStmt, FuncDecl, FuncParam, Stmt,
    Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, Binary, Unary, CallExpr, MintType
)

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
        global_sym: Dict[str, MintType] = {}
        funcs: Dict[str, FuncSignature] = {}

        for func in program.funcs:
            if func.name in funcs:
                issues.append(LintIssue(f"Função '{func.name}' já declarada."))
                continue
            funcs[func.name] = FuncSignature(
                params=[p.param_type for p in func.params],
                return_type=func.return_type,
            )

        for d in program.decls:
            if d.name in global_sym:
                issues.append(LintIssue(f"Variável '{d.name}' declarada mais de uma vez."))
                continue
            global_sym[d.name] = d.vartype
            if d.initializer is not None:
                it = self._infer_type(d.initializer, global_sym, funcs, issues)
                if it is not None and not self._is_assignment_compatible(d.vartype, it):
                    issues.append(LintIssue(
                        f"Incompatibilidade: '{d.name}' é {d.vartype} mas inicializa com {it}."
                    ))

        for st in program.body:
            self._lint_stmt(st, global_sym, funcs, issues, current_return=None)

        for func in program.funcs:
            self._lint_function(func, global_sym, funcs, issues)

        return issues

    def _lint_function(
        self,
        func: FuncDecl,
        global_sym: Dict[str, MintType],
        funcs: Dict[str, FuncSignature],
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
            self._lint_stmt(st, local_sym, funcs, issues, current_return=func.return_type)

        if func.return_type is not None and not has_return_stmt:
            issues.append(LintIssue(f"Função '{func.name}' declara retorno {func.return_type}, mas não possui RETURN."))

    def _lint_stmt(
        self,
        stmt: Stmt,
        sym: Dict[str, MintType],
        funcs: Dict[str, FuncSignature],
        issues: List[LintIssue],
        current_return: Optional[MintType],
    ) -> None:
        if isinstance(stmt, VarDeclStmt):
            if stmt.name in sym:
                issues.append(LintIssue(f"Variável '{stmt.name}' declarada mais de uma vez."))
                return
            sym[stmt.name] = stmt.vartype
            if stmt.initializer is not None:
                it = self._infer_type(stmt.initializer, sym, funcs, issues)
                if it is not None and not self._is_assignment_compatible(stmt.vartype, it):
                    issues.append(LintIssue(
                        f"Incompatibilidade: '{stmt.name}' é {stmt.vartype} mas inicializa com {it}."
                    ))
            return

        if isinstance(stmt, WriteStmt):
            self._infer_type(stmt.expr, sym, funcs, issues)
            return

        if isinstance(stmt, CallStmt):
            sig = funcs.get(stmt.call.name)
            if sig is not None and sig.return_type is not None:
                issues.append(LintIssue(f"Função '{stmt.call.name}' retorna valor e deve ser usada em expressão."))
            self._lint_call(stmt.call, sym, funcs, issues, require_value=False)
            return

        if isinstance(stmt, IfStmt):
            for branch in stmt.branches:
                cond_type = self._infer_type(branch.condition, sym, funcs, issues)
                if cond_type is not None and cond_type != "bool":
                    issues.append(LintIssue("Condição do if deve ser bool."))
                branch_sym = dict(sym)
                for inner in branch.body:
                    self._lint_stmt(inner, branch_sym, funcs, issues, current_return)
            if stmt.else_body is not None:
                else_sym = dict(sym)
                for inner in stmt.else_body:
                    self._lint_stmt(inner, else_sym, funcs, issues, current_return)
            return

        if isinstance(stmt, AssignStmt):
            var_type = sym.get(stmt.name)
            if var_type is None:
                issues.append(LintIssue(f"Atribuição para variável não declarada: '{stmt.name}'."))
                self._infer_type(stmt.expr, sym, funcs, issues)
                return
            expr_type = self._infer_type(stmt.expr, sym, funcs, issues)
            if expr_type is not None and not self._is_assignment_compatible(var_type, expr_type):
                issues.append(LintIssue(
                    f"Incompatibilidade na atribuição: '{stmt.name}' é {var_type} mas recebeu {expr_type}."
                ))
            return

        if isinstance(stmt, WhileStmt):
            cond_type = self._infer_type(stmt.condition, sym, funcs, issues)
            if cond_type is not None and cond_type != "bool":
                issues.append(LintIssue("Condição do while deve ser bool."))
            loop_sym = dict(sym)
            for inner in stmt.body:
                self._lint_stmt(inner, loop_sym, funcs, issues, current_return)
            return

        if isinstance(stmt, ReturnStmt):
            if current_return is None:
                issues.append(LintIssue("RETURN fora de função."))
                self._infer_type(stmt.expr, sym, funcs, issues)
                return
            expr_type = self._infer_type(stmt.expr, sym, funcs, issues)
            if expr_type is not None and not self._is_assignment_compatible(current_return, expr_type):
                issues.append(LintIssue(
                    f"RETURN incompatível: função retorna {current_return}, mas expressão é {expr_type}."
                ))
            return

        issues.append(LintIssue(f"Statement não suportado no linter: {type(stmt).__name__}"))

    def _infer_type(
        self,
        expr: Expr,
        sym: Dict[str, MintType],
        funcs: Dict[str, FuncSignature],
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
        if isinstance(expr, CallExpr):
            return self._lint_call(expr, sym, funcs, issues, require_value=True)

        if isinstance(expr, Unary):
            t = self._infer_type(expr.expr, sym, funcs, issues)
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
            lt = self._infer_type(expr.left, sym, funcs, issues)
            rt = self._infer_type(expr.right, sym, funcs, issues)
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
        issues: List[LintIssue],
        require_value: bool,
    ) -> Optional[MintType]:
        sig = funcs.get(call.name)
        if sig is None:
            issues.append(LintIssue(f"Função '{call.name}' não declarada."))
            for arg in call.args:
                self._infer_type(arg, sym, funcs, issues)
            return None

        if len(call.args) != len(sig.params):
            issues.append(LintIssue(
                f"Função '{call.name}' espera {len(sig.params)} argumentos, mas recebeu {len(call.args)}."
            ))

        for i, arg in enumerate(call.args):
            arg_type = self._infer_type(arg, sym, funcs, issues)
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

    def _is_chained_comparison(self, expr: Binary) -> bool:
        if expr.op not in ("==", "!=", "<", ">", "<=", ">="):
            return False
        return (
            isinstance(expr.left, Binary)
            and expr.left.op in ("==", "!=", "<", ">", "<=", ">=")
        )
