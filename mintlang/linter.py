from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Tuple
from .ast_nodes import (
    Program, VarDeclStmt, WriteStmt, Stmt,
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
    - operações aritméticas só com int (por enquanto)
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
                if it is not None and it != d.vartype:
                    issues.append(LintIssue(
                        f"Incompatibilidade: '{d.name}' é {d.vartype} mas inicializa com {it}."
                    ))

        # body
        for st in program.body:
            if isinstance(st, WriteStmt):
                self._infer_type(st.expr, sym, issues)
            else:
                issues.append(LintIssue(f"Statement não suportado no linter: {type(st).__name__}"))

        return issues

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
            if t is not None and t not in ("int", "float"):
                issues.append(LintIssue(
                    f"Operador unário '{expr.op}' usado em tipo {t} (esperado int ou float)."
                ))
            return t if t is not None else None
        if isinstance(expr, Binary):
            lt = self._infer_type(expr.left, sym, issues)
            rt = self._infer_type(expr.right, sym, issues)
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
