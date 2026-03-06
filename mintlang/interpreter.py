from __future__ import annotations
from typing import Dict, Any, Optional
from .ast_nodes import (
    Program, Stmt, WriteStmt, VarDeclStmt, IfStmt, AssignStmt, WhileStmt, InputStmt, MoveStmt,
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
        coerced_val = self._ensure_type(decl.name, decl.vartype, val)
        self.env[decl.name] = coerced_val

    def _exec_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, WriteStmt):
            val = self._eval(stmt.expr)
            print(self._format_value(val))
            return
        if isinstance(stmt, IfStmt):
            self._exec_if(stmt)
            return
        if isinstance(stmt, AssignStmt):
            self._exec_assign(stmt)
            return
        if isinstance(stmt, InputStmt):
            self._exec_input(stmt)
            return
        if isinstance(stmt, MoveStmt):
            self._exec_move(stmt)
            return
        if isinstance(stmt, WhileStmt):
            self._exec_while(stmt)
            return

        raise RuntimeMintError(f"Stmt não suportado: {type(stmt).__name__}")

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

    def _exec_assign(self, stmt: AssignStmt) -> None:
        if stmt.name not in self.types:
            raise RuntimeMintError(f"Variável '{stmt.name}' não declarada.")
        val = self._eval(stmt.expr)
        coerced_val = self._ensure_type(stmt.name, self.types[stmt.name], val)
        self.env[stmt.name] = coerced_val

    def _exec_input(self, stmt: InputStmt) -> None:
        if not isinstance(stmt.target, VarRef):
            raise RuntimeMintError("input só aceita variável como alvo.")

        name = stmt.target.name
        if name not in self.types:
            raise RuntimeMintError(f"Variável '{name}' não declarada.")

        raw = input()
        value = self._parse_input_value(name, self.types[name], raw)
        self.env[name] = value

    def _exec_move(self, stmt: MoveStmt) -> None:
        if stmt.target not in self.types:
            raise RuntimeMintError(f"Variável '{stmt.target}' não declarada.")

        value = self._eval(stmt.source)
        coerced_value = self._ensure_type(stmt.target, self.types[stmt.target], value)
        self.env[stmt.target] = coerced_value

    def _exec_while(self, stmt: WhileStmt) -> None:
        while True:
            cond = self._eval(stmt.condition)
            if not isinstance(cond, bool):
                raise RuntimeMintError("Condição do while deve ser bool.")
            if not cond:
                return
            for inner in stmt.body:
                self._exec_stmt(inner)

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

    def _eval_logical(self, op: str, left: Any, right_expr: Expr) -> bool:
        if not isinstance(left, bool):
            raise RuntimeMintError(f"Operador {op.upper()} requer bool em ambos os lados.")
        if op == "and":
            if not left:
                return False
            right_val = self._eval(right_expr)
            if not isinstance(right_val, bool):
                raise RuntimeMintError(f"Operador AND requer bool em ambos os lados.")
            return right_val
        if op == "or":
            if left:
                return True
            right_val = self._eval(right_expr)
            if not isinstance(right_val, bool):
                raise RuntimeMintError(f"Operador OR requer bool em ambos os lados.")
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
        return val

    def _parse_input_value(self, name: str, t: MintType, raw: str) -> Any:
        if t == "string":
            return raw
        if t == "int":
            try:
                return int(raw)
            except ValueError as e:
                raise RuntimeMintError(f"Input inválido para variável '{name}': esperado int.") from e
        if t == "float":
            try:
                return float(raw)
            except ValueError as e:
                raise RuntimeMintError(f"Input inválido para variável '{name}': esperado float.") from e
        if t == "bool":
            if raw == "true":
                return True
            if raw == "false":
                return False
            raise RuntimeMintError(f"Input inválido para variável '{name}': esperado bool (true/false).")
        if t == "char":
            if len(raw) != 1:
                raise RuntimeMintError(f"Input inválido para variável '{name}': esperado char (1 caractere).")
            return raw
        raise RuntimeMintError(f"Tipo inválido para input em '{name}': {t}.")

    def _format_value(self, val: Any) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        return str(val)
