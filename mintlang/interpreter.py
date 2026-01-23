from __future__ import annotations
from typing import Dict, Any, Optional
from .ast_nodes import (
    Program, Stmt, WriteStmt, VarDeclStmt,
    Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, Binary, Unary, MintType
)
from .errors import RuntimeMintError

DEFAULTS: Dict[MintType, Any] = {
    "int": 0,
    "string": "",
    "bool": False,
    "float": 0.0,
    "char": "\0",
}

class Interpreter:
    def __init__(self):
        self.types: Dict[str, MintType] = {}
        self.env: Dict[str, Any] = {}

    def run(self, program: Program) -> None:
        # init: declarações
        for decl in program.decls:
            self._exec_decl(decl)

        # initialization: lógica
        for stmt in program.body:
            self._exec_stmt(stmt)

    def _exec_decl(self, decl: VarDeclStmt) -> None:
        if decl.name in self.types:
            raise RuntimeMintError(f"Variável '{decl.name}' já declarada.")

        self.types[decl.name] = decl.vartype

        if decl.initializer is None:
            self.env[decl.name] = DEFAULTS[decl.vartype]
            return

        val = self._eval(decl.initializer)
        self._ensure_type(decl.name, decl.vartype, val)
        self.env[decl.name] = val

    def _exec_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, WriteStmt):
            val = self._eval(stmt.expr)
            print(self._format_value(val))
            return

        raise RuntimeMintError(f"Stmt não suportado: {type(stmt).__name__}")

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
            if expr.name not in self.env:
                raise RuntimeMintError(f"Variável '{expr.name}' não declarada.")
            return self.env[expr.name]

        if isinstance(expr, Unary):
            v = self._eval(expr.expr)
            if not isinstance(v, (int, float)):
                raise RuntimeMintError(f"Operador unário '{expr.op}' requer int ou float.")
            if expr.op == "-":
                return -v
            if expr.op == "+":
                return +v
            raise RuntimeMintError(f"Operador unário inválido: {expr.op}")

        if isinstance(expr, Binary):
            left = self._eval(expr.left)
            right = self._eval(expr.right)

            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                raise RuntimeMintError(f"Operação '{expr.op}' requer int ou float em ambos os lados.")

            if expr.op == "+":
                return left + right
            if expr.op == "-":
                return left - right
            if expr.op == "*":
                return left * right
            if expr.op == "/":
                if right == 0:
                    raise RuntimeMintError("Divisão por zero.")
                if isinstance(left, float) or isinstance(right, float):
                    return float(left) / float(right)
                return left // right

            raise RuntimeMintError(f"Operador inválido: {expr.op}")

        raise RuntimeMintError(f"Expr não suportada: {type(expr).__name__}")

    def _ensure_type(self, name: str, t: MintType, val: Any) -> None:
        if t == "int" and not isinstance(val, int):
            raise RuntimeMintError(f"'{name}' é int, mas recebeu {type(val).__name__}.")
        if t == "string" and not isinstance(val, str):
            raise RuntimeMintError(f"'{name}' é string, mas recebeu {type(val).__name__}.")
        if t == "bool" and not isinstance(val, bool):
            raise RuntimeMintError(f"'{name}' é bool, mas recebeu {type(val).__name__}.")
        if t == "float" and not isinstance(val, float):
            raise RuntimeMintError(f"'{name}' é float, mas recebeu {type(val).__name__}.")
        if t == "char":
            if not isinstance(val, str):
                raise RuntimeMintError(f"'{name}' é char, mas recebeu {type(val).__name__}.")
            if len(val) != 1:
                raise RuntimeMintError(f"'{name}' é char, mas recebeu string com {len(val)} caracteres.")

    def _format_value(self, val: Any) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        return str(val)
