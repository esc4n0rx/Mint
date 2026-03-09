from dataclasses import dataclass
from typing import List, Optional

MintType = str

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
class FieldAccessExpr(Expr):
    base: Expr
    field: str


@dataclass
class IndexAccessExpr(Expr):
    base: Expr
    index: Expr


@dataclass
class SizeCall(Expr):
    collection: Expr

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


@dataclass
class StructField:
    name: str
    field_type: MintType


@dataclass
class StructDecl:
    name: str
    fields: List[StructField]


@dataclass
class ListType:
    inner_type: MintType


@dataclass
class TableType:
    inner_type: MintType

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
class AddStmt(Stmt):
    collection: Expr
    value: Expr


@dataclass
class InsertStmt(Stmt):
    table: Expr
    value: Expr

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
    target: Expr
    expr: Expr

@dataclass
class InputStmt(Stmt):
    target: Expr

@dataclass
class MoveStmt(Stmt):
    source: Expr
    target: str

@dataclass
class QueryStmt(Stmt):
    source: str
    condition: Expr
    destination: str

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
    structs: List[StructDecl]
    decls: List[VarDeclStmt]
    body: List[Stmt]
    funcs: List[FuncDecl]
