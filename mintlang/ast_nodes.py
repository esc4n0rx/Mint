from dataclasses import dataclass
from typing import List, Optional, Literal

MintType = Literal["int", "string", "bool", "float", "char"]

# -------------------------
# Expressions
# -------------------------
@dataclass
class Expr:
    pass

@dataclass
class IntLit(Expr):
    value: int

@dataclass
class FloatLit(Expr):
    value: float

@dataclass
class StringLit(Expr):
    value: str

@dataclass
class CharLit(Expr):
    value: str

@dataclass
class BoolLit(Expr):
    value: bool

@dataclass
class VarRef(Expr):
    name: str

@dataclass
class Binary(Expr):
    left: Expr
    op: str
    right: Expr

@dataclass
class Unary(Expr):
    op: str
    expr: Expr

@dataclass
class CallExpr(Expr):
    name: str
    args: List[Expr]

# -------------------------
# Statements
# -------------------------
@dataclass
class Stmt:
    pass

@dataclass
class WriteStmt(Stmt):
    expr: Expr

@dataclass
class VarDeclStmt(Stmt):
    name: str
    vartype: MintType
    initializer: Optional[Expr] = None

@dataclass
class IfBranch:
    condition: Expr
    body: List[Stmt]

@dataclass
class IfStmt(Stmt):
    branches: List[IfBranch]
    else_body: Optional[List[Stmt]] = None

@dataclass
class AssignStmt(Stmt):
    name: str
    expr: Expr

@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: List[Stmt]

@dataclass
class ReturnStmt(Stmt):
    expr: Expr


@dataclass
class CallStmt(Stmt):
    call: CallExpr


@dataclass
class FuncParam:
    name: str
    param_type: MintType


@dataclass
class FuncDecl:
    name: str
    params: List[FuncParam]
    return_type: Optional[MintType]
    body: List[Stmt]

# -------------------------
# Program structure
# -------------------------
@dataclass
class Program:
    decls: List[VarDeclStmt]
    body: List[Stmt]
    funcs: List[FuncDecl]
