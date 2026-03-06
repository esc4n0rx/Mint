from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Tuple
from .ast_nodes import (
    Program, VarDeclStmt, WriteStmt, IfStmt, AssignStmt, WhileStmt, Stmt,
    Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, Binary, Unary, MintType
)
from .errors import LintError

@dataclass
class LintIssue:
    message: str

class Linter:
    """
    Validações (MVP):
    - variáveis não duplicadas
    - uso de variável declarada
    - tipo válido e coerência de inicialização
    - operações aritméticas com int/float (com promoção para float)
    """
    def lint(self, program: Program) -> List[LintIssue]:
        issues: List[LintIssue] = []
        sym: Dict[str, MintType] = {}

        # decls
        for d in program.decls:
            if d.name in sym:
                issues.append(LintIssue(f"Variável '{d.name}' declarada mais de uma vez."))
                continue
            sym[d.name] = d.vartype

            if d.initializer is not None:
                it = self._infer_type(d.initializer, sym, issues)
                if it is not None and not self._is_assignment_compatible(d.vartype, it):
                    issues.append(LintIssue(
                        f"Incompatibilidade: '{d.name}' é {d.vartype} mas inicializa com {it}."
                    ))

        # body
        for st in program.body:
            self._lint_stmt(st, sym, issues)

        return issues

    def _lint_stmt(self, stmt: Stmt, sym: Dict[str, MintType], issues: List[LintIssue]) -> None:
        if isinstance(stmt, WriteStmt):
            self._infer_type(stmt.expr, sym, issues)
            return
        if isinstance(stmt, IfStmt):
            for branch in stmt.branches:
                cond_type = self._infer_type(branch.condition, sym, issues)
                if cond_type is not None and cond_type != "bool":
                    issues.append(LintIssue("Condição do if deve ser bool."))
                for inner in branch.body:
                    self._lint_stmt(inner, sym, issues)
            if stmt.else_body is not None:
                for inner in stmt.else_body:
                    self._lint_stmt(inner, sym, issues)
            return
        if isinstance(stmt, AssignStmt):
            var_type = sym.get(stmt.name)
            if var_type is None:
                issues.append(LintIssue(f"Atribuição para variável não declarada: '{stmt.name}'."))
                self._infer_type(stmt.expr, sym, issues)
                return
            expr_type = self._infer_type(stmt.expr, sym, issues)
            if expr_type is not None and not self._is_assignment_compatible(var_type, expr_type):
                issues.append(LintIssue(
                    f"Incompatibilidade na atribuição: '{stmt.name}' é {var_type} mas recebeu {expr_type}."
                ))
            return
        if isinstance(stmt, WhileStmt):
            cond_type = self._infer_type(stmt.condition, sym, issues)
            if cond_type is not None and cond_type != "bool":
                issues.append(LintIssue("Condição do while deve ser bool."))
            for inner in stmt.body:
                self._lint_stmt(inner, sym, issues)
            return

        issues.append(LintIssue(f"Statement não suportado no linter: {type(stmt).__name__}"))

    def _infer_type(self, expr: Expr, sym: Dict[str, MintType], issues: List[LintIssue]) -> Optional[MintType]:
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
        if isinstance(expr, Unary):
            t = self._infer_type(expr.expr, sym, issues)
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
            lt = self._infer_type(expr.left, sym, issues)
            rt = self._infer_type(expr.right, sym, issues)
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
