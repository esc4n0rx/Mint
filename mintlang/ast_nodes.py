from dataclasses import dataclass
from typing import List, Optional, Literal, Union

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

# -------------------------
# Program structure
# -------------------------
@dataclass
class Program:
    decls: List[VarDeclStmt]
    body: List[Stmt]
