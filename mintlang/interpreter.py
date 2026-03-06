from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .ast_nodes import (
    Program, Stmt, WriteStmt, VarDeclStmt, IfStmt, AssignStmt, InputStmt, MoveStmt, WhileStmt, ReturnStmt, CallStmt,
    FuncDecl, Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, Binary, Unary, CallExpr, MintType
)
from .errors import RuntimeMintError

DEFAULTS: Dict[MintType, Any] = {
    "int": 0,
    "string": "",
    "bool": False,
    "float": 0.0,
    "char": "\0",
}


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

    def run(self, program: Program) -> None:
        for func in program.funcs:
            self.funcs[func.name] = func

        for decl in program.decls:
            self._exec_decl(decl)

        for stmt in program.body:
            self._exec_stmt(stmt)

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
            scope.env[decl.name] = DEFAULTS[decl.vartype]
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
        if isinstance(stmt, CallStmt):
            self._call_function(stmt.call, require_value=False)
            return
        if isinstance(stmt, IfStmt):
            self._exec_if(stmt)
            return
        if isinstance(stmt, AssignStmt):
            self._assign_value(stmt.name, self._eval(stmt.expr))
            return
        if isinstance(stmt, InputStmt):
            if not isinstance(stmt.target, VarRef):
                raise RuntimeMintError("input aceita apenas referência de variável.")
            name = stmt.target.name
            var_type = self._resolve_type(name)
            if var_type is None:
                raise RuntimeMintError(f"Variável '{name}' não declarada.")
            raw = input()
            parsed = self._parse_input_value(name, var_type, raw)
            self._assign_value(name, parsed)
            return
        if isinstance(stmt, MoveStmt):
            self._assign_value(stmt.target, self._eval(stmt.source))
            return
        if isinstance(stmt, WhileStmt):
            self._exec_while(stmt)
            return
        if isinstance(stmt, ReturnStmt):
            raise ReturnSignal(self._eval(stmt.expr))

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

    def _exec_while(self, stmt: WhileStmt) -> None:
        while True:
            cond = self._eval(stmt.condition)
            if not isinstance(cond, bool):
                raise RuntimeMintError("Condição do while deve ser bool.")
            if not cond:
                return
            for inner in stmt.body:
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
        except ReturnSignal as signal:
            if func.return_type is None:
                raise RuntimeMintError(f"Função '{func.name}' não declara RETURNS e não pode retornar valor.")
            return self._ensure_type(func.name, func.return_type, signal.value)
        finally:
            self._pop_scope()

        if func.return_type is not None:
            raise RuntimeMintError(f"Função '{func.name}' deveria retornar {func.return_type}.")

        if require_value:
            raise RuntimeMintError(f"Função '{func.name}' não retorna valor e não pode ser usada em expressão.")
        return None

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
        return str(val)
