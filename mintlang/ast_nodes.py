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
class CountExpr(Expr):
    collection: Expr


@dataclass
class SumExpr(Expr):
    target: Expr


@dataclass
class AvgExpr(Expr):
    target: Expr

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
class ImportDecl:
    module_path: str


@dataclass
class StructField:
    name: str
    field_type: MintType


@dataclass
class StructDecl:
    name: str
    fields: List[StructField]


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
class DbCreateStmt(Stmt):
    path: str


@dataclass
class DbOpenStmt(Stmt):
    path: str


@dataclass
class DbCompactStmt(Stmt):
    pass


@dataclass
class ColumnDef:
    name: str
    col_type: MintType
    primary_key: bool = False
    auto_increment: bool = False


@dataclass
class TableCreateStmt(Stmt):
    table_name: str
    columns: List[ColumnDef]


@dataclass
class AppendValuesStmt(Stmt):
    table_name: str
    assignments: List[tuple[str, Expr]]


@dataclass
class AppendStructStmt(Stmt):
    struct_var: str
    table_name: str


@dataclass
class SelectStmt(Stmt):
    table_name: str
    columns: List[str]
    condition: Optional[Expr]
    destination: str


@dataclass
class UpdateStmt(Stmt):
    table_name: str
    assignments: List[tuple[str, Expr]]
    condition: Expr


@dataclass
class DeleteStmt(Stmt):
    table_name: str
    condition: Expr


@dataclass
class ShowTablesStmt(Stmt):
    destination: Optional[str] = None


@dataclass
class DescribeStmt(Stmt):
    table_name: str
    destination: Optional[str] = None


@dataclass
class IndexCreateStmt(Stmt):
    index_name: str
    table_name: str
    column_name: str


@dataclass
class SelectCountStmt(Stmt):
    table_name: str
    condition: Optional[Expr]
    destination: str

@dataclass
class LoadStmt(Stmt):
    path: str
    destination: str

@dataclass
class SaveStmt(Stmt):
    source: str
    path: str

@dataclass
class ExportStmt(Stmt):
    source: str
    path: str

@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: List[Stmt]


@dataclass
class ForStmt(Stmt):
    item_name: str
    collection: Expr
    body: List[Stmt]


@dataclass
class TryCatchStmt(Stmt):
    try_body: List[Stmt]
    catch_body: List[Stmt]

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
    imports: List[ImportDecl]
    structs: List[StructDecl]
    decls: List[VarDeclStmt]
    body: List[Stmt]
    funcs: List[FuncDecl]
