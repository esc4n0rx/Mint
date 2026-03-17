from __future__ import annotations
from typing import List, Optional
from .tokens import Token, TokenType
from .errors import ParserError
from .ast_nodes import (
    Program, Stmt, WriteStmt, AddStmt, InsertStmt, VarDeclStmt, IfStmt, IfBranch, SwitchStmt, SwitchCase, AssignStmt, InputStmt, MoveStmt, QueryStmt, LoadStmt, SaveStmt, ExportStmt, WhileStmt, ForStmt, BreakStmt, ContinueStmt, TryCatchStmt, ReturnStmt, CallStmt,
    DbCreateStmt, DbOpenStmt, DbCompactStmt, DbBeginStmt, DbCommitStmt, DbRollbackStmt, ShowTablesStmt, DescribeStmt, IndexCreateStmt, SelectCountStmt, ColumnDef, TableCreateStmt, AppendValuesStmt, AppendStructStmt, UpsertStmt, SelectStmt, JoinClause, UpdateStmt, DeleteStmt, AlterTableAddColumnStmt, AlterTableDropColumnStmt, AlterTableRenameColumnStmt, AlterTableRenameStmt,
    FuncDecl, FuncParam, StructDecl, StructField, ImportDecl,
    Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, FieldAccessExpr, IndexAccessExpr, SizeCall, CountExpr, SumExpr, AvgExpr, Binary, Unary, CallExpr, MintType
)

class Parser:
    """
    Gramática (MVP):
      program      -> "program" "init" "." decls "initialization" "." stmts "endprogram" "." func_decls*
      decls        -> ( "var" IDENT "type" TYPE ( "=" expr )? "." )*
      stmts        -> ( write_stmt | if_stmt | assign_stmt | while_stmt | return_stmt | var_decl_stmt )*
      func_decls   -> "func" IDENT "(" params? ")" ("returns" TYPE)? "." stmts "endfunc" "."
      params       -> param ("," param)*
      param        -> IDENT "type" TYPE
      write_stmt   -> "write" "(" expr ")" "."
      if_stmt      -> "if" expr "." stmts ( "elseif" expr "." stmts )* ( "else" "." stmts )? "endif" "."
      assign_stmt  -> IDENT "=" expr "."
      while_stmt   -> "while" expr "." stmts "endwhile" "."
      return_stmt  -> "return" expr "."
      expr         -> or_expr
      or_expr      -> and_expr ( "or" and_expr )*
      and_expr     -> not_expr ( "and" not_expr )*
      not_expr     -> "not" not_expr | comparison
      comparison   -> term (("==" | "!=" | "<" | ">" | "<=" | ">=") term)*
      term         -> factor (("+" | "-") factor)*
      factor       -> unary (("*" | "/") unary)*
      unary        -> (("+" | "-") unary) | primary
      primary      -> NUMBER | FLOAT | STRING | CHAR | TRUE | FALSE | IDENT ("(" args? ")")? | "(" expr ")"
      args         -> expr ("," expr)*
      TYPE         -> "int" | "string" | "bool" | "float" | "char"
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def parse(self) -> Program:
        imports: List[ImportDecl] = []
        while self._check(TokenType.IMPORT):
            imports.append(self._import_decl())

        structs: List[StructDecl] = []
        while self._check(TokenType.STRUCT):
            structs.append(self._struct_decl())

        funcs: List[FuncDecl] = []
        while self._check(TokenType.FUNC):
            funcs.append(self._func_decl())

        decls: List[VarDeclStmt] = []
        body: List[Stmt] = []
        if self._check(TokenType.PROGRAM):
            self._consume(TokenType.PROGRAM, "Esperado 'program'.")
            self._consume(TokenType.INIT, "Esperado 'init' após 'program'.")
            self._consume(TokenType.DOT, "Esperado '.' após 'program init'.")

            while self._check(TokenType.STRUCT) or self._check(TokenType.VAR):
                if self._check(TokenType.STRUCT):
                    structs.append(self._struct_decl())
                else:
                    decls.append(self._vardecl())

            self._consume(TokenType.INITIALIZATION, "Esperado 'initialization'.")
            self._consume(TokenType.DOT, "Esperado '.' após 'initialization'.")

            body = self._block_until({TokenType.ENDPROGRAM})

            self._consume(TokenType.ENDPROGRAM, "Esperado 'endprogram'.")
            self._consume(TokenType.DOT, "Esperado '.' após 'endprogram'.")

            while self._check(TokenType.FUNC):
                funcs.append(self._func_decl())

        if not self._check(TokenType.EOF):
            t = self._peek()
            raise ParserError(f"Texto extra após fim do arquivo em {t.line}:{t.col}")

        return Program(imports=imports, structs=structs, decls=decls, body=body, funcs=funcs)

    def _import_decl(self) -> ImportDecl:
        self._consume(TokenType.IMPORT, "Esperado 'IMPORT'.")
        parts = [self._consume(TokenType.IDENT, "Esperado caminho do módulo após IMPORT.").lexeme]
        while self._check(TokenType.DOT) and self._check_next(TokenType.IDENT):
            self._advance()
            parts.append(self._consume(TokenType.IDENT, "Esperado segmento do caminho do módulo.").lexeme)
        self._consume(TokenType.DOT, "Faltou '.' no fim do IMPORT.")
        return ImportDecl(module_path=".".join(parts))

    def _struct_decl(self) -> StructDecl:
        self._consume(TokenType.STRUCT, "Esperado 'STRUCT'.")
        name = self._consume(TokenType.IDENT, "Esperado nome da struct.").lexeme
        self._consume(TokenType.DOT, "Faltou '.' após cabeçalho da struct.")

        fields: List[StructField] = []
        while not self._check(TokenType.ENDSTRUCT):
            field_name = self._consume(TokenType.IDENT, "Esperado nome do campo.").lexeme
            self._consume(TokenType.TYPE, "Esperado 'type' após nome do campo.")
            field_type = self._parse_primitive_type()
            self._consume(TokenType.DOT, "Faltou '.' após campo da struct.")
            fields.append(StructField(name=field_name, field_type=field_type))

        self._consume(TokenType.ENDSTRUCT, "Esperado 'ENDSTRUCT'.")
        self._consume(TokenType.DOT, "Faltou '.' após ENDSTRUCT.")
        return StructDecl(name=name, fields=fields)

    def _func_decl(self) -> FuncDecl:
        self._consume(TokenType.FUNC, "Esperado 'FUNC'.")
        name = self._consume(TokenType.IDENT, "Esperado nome da função.").lexeme
        self._consume(TokenType.LPAREN, "Esperado '(' após nome da função.")

        params: List[FuncParam] = []
        if not self._check(TokenType.RPAREN):
            params.append(self._func_param())
            while self._match(TokenType.COMMA):
                params.append(self._func_param())

        self._consume(TokenType.RPAREN, "Esperado ')' após parâmetros.")

        return_type: Optional[MintType] = None
        if self._match(TokenType.RETURNS):
            return_type = self._parse_type()

        self._consume(TokenType.DOT, "Faltou '.' após cabeçalho da função.")
        body = self._block_until({TokenType.ENDFUNC})
        self._consume(TokenType.ENDFUNC, "Esperado 'ENDFUNC'.")
        self._consume(TokenType.DOT, "Faltou '.' após ENDFUNC.")
        return FuncDecl(name=name, params=params, return_type=return_type, body=body)

    def _func_param(self) -> FuncParam:
        name = self._consume(TokenType.IDENT, "Esperado nome do parâmetro.").lexeme
        self._consume(TokenType.TYPE, "Esperado 'type' após nome do parâmetro.")
        param_type = self._parse_type()
        return FuncParam(name=name, param_type=param_type)

    def _vardecl(self) -> VarDeclStmt:
        self._consume(TokenType.VAR, "Esperado 'var'.")
        name = self._consume(TokenType.IDENT, "Esperado nome da variável.").lexeme
        self._consume(TokenType.TYPE, "Esperado 'type' após nome da variável.")
        vartype = self._parse_type()

        initializer: Optional[Expr] = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()

        self._consume(TokenType.DOT, "Faltou '.' no fim da declaração var.")
        return VarDeclStmt(name=name, vartype=vartype, initializer=initializer)

    def _parse_type(self) -> MintType:
        if self._match(TokenType.LIST):
            self._consume(TokenType.LT, "Esperado '<' após list.")
            inner = self._parse_type()
            self._consume(TokenType.GT, "Esperado '>' após tipo de list.")
            return f"list<{inner}>"
        if self._match(TokenType.TABLE):
            self._consume(TokenType.LT, "Esperado '<' após table.")
            inner = self._parse_type()
            self._consume(TokenType.GT, "Esperado '>' após tipo de table.")
            return f"table<{inner}>"
        if self._check(TokenType.IDENT):
            return self._advance().lexeme
        return self._parse_primitive_type()

    def _parse_primitive_type(self) -> MintType:
        if self._match(TokenType.INT_T):
            return "int"
        if self._match(TokenType.STRING_T):
            return "string"
        if self._match(TokenType.BOOL_T):
            return "bool"
        if self._match(TokenType.FLOAT_T):
            return "float"
        if self._match(TokenType.CHAR_T):
            return "char"
        if self._match(TokenType.DECIMAL_T):
            return "decimal"
        if self._match(TokenType.DATE_T):
            return "date"
        if self._match(TokenType.DATETIME_T):
            return "datetime"
        if self._match(TokenType.TIME_T):
            return "time"
        if self._match(TokenType.TEXT_T):
            return "text"
        if self._match(TokenType.LONG_T):
            return "long"
        if self._match(TokenType.DOUBLE_T):
            return "double"
        if self._match(TokenType.BYTES_T):
            return "bytes"
        if self._match(TokenType.UUID_T):
            return "uuid"
        if self._match(TokenType.JSON_T):
            return "json"
        t = self._peek()
        raise ParserError(f"Tipo inválido '{t.lexeme}' em {t.line}:{t.col}")

    def _statement(self) -> Stmt:
        if self._check(TokenType.VAR):
            return self._vardecl()

        if self._match(TokenType.WRITE):
            self._consume(TokenType.LPAREN, "Esperado '(' após write.")
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após expressão do write.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do write.")
            return WriteStmt(expr)

        if self._match(TokenType.ADD):
            self._consume(TokenType.LPAREN, "Esperado '(' após add.")
            collection = self._expression()
            self._consume(TokenType.COMMA, "Esperado ',' em add(collection, valor).")
            value = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após add.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do add.")
            return AddStmt(collection=collection, value=value)

        if self._match(TokenType.INSERT):
            self._consume(TokenType.LPAREN, "Esperado '(' após insert.")
            table = self._expression()
            self._consume(TokenType.COMMA, "Esperado ',' em insert(table, registro).")
            value = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após insert.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do insert.")
            return InsertStmt(table=table, value=value)

        if self._match(TokenType.INPUT):
            self._consume(TokenType.LPAREN, "Esperado '(' após input.")
            target = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após alvo do input.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do input.")
            return InputStmt(target=target)

        if self._match(TokenType.MOVE):
            source = self._expression()
            self._consume(TokenType.TO, "Esperado 'to' no comando move.")
            target = self._consume(TokenType.IDENT, "Destino do move deve ser variável.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim do move.")
            return MoveStmt(source=source, target=target)


        if self._match(TokenType.LOAD):
            path = self._consume(TokenType.STRING, "LOAD exige caminho em string literal.").lexeme
            self._consume(TokenType.INTO, "Esperado 'INTO' no comando LOAD.")
            destination = self._consume(TokenType.IDENT, "Esperado coleção de destino no LOAD.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim do LOAD.")
            return LoadStmt(path=path, destination=destination)

        if self._match(TokenType.SAVE):
            source = self._consume(TokenType.IDENT, "Esperado coleção de origem no SAVE.").lexeme
            self._consume(TokenType.TO, "Esperado 'TO' no comando SAVE.")
            path = self._consume(TokenType.STRING, "SAVE exige caminho em string literal.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim do SAVE.")
            return SaveStmt(source=source, path=path)

        if self._match(TokenType.EXPORT):
            source = self._consume(TokenType.IDENT, "Esperado coleção de origem no EXPORT.").lexeme
            self._consume(TokenType.TO, "Esperado 'TO' no comando EXPORT.")
            path = self._consume(TokenType.STRING, "EXPORT exige caminho em string literal.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim do EXPORT.")
            return ExportStmt(source=source, path=path)
        if self._match(TokenType.QUERY):
            self._consume(TokenType.FROM, "Esperado 'FROM' após QUERY.")
            source = self._consume(TokenType.IDENT, "Esperado nome da coleção de origem.").lexeme
            self._consume(TokenType.WHERE, "Esperado 'WHERE' na QUERY.")
            condition = self._expression()
            self._consume(TokenType.INTO, "Esperado 'INTO' na QUERY.")
            destination = self._consume(TokenType.IDENT, "Esperado nome da coleção de destino.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim da QUERY.")
            return QueryStmt(source=source, condition=condition, destination=destination)

        if self._match(TokenType.DB):
            if self._match(TokenType.CREATE):
                path = self._consume(TokenType.STRING, "DB CREATE exige caminho string.").lexeme
                self._consume(TokenType.DOT, "Faltou '.' no fim do DB CREATE.")
                return DbCreateStmt(path=path)
            if self._match(TokenType.OPEN):
                path = self._consume(TokenType.STRING, "DB OPEN exige caminho string.").lexeme
                self._consume(TokenType.DOT, "Faltou '.' no fim do DB OPEN.")
                return DbOpenStmt(path=path)
            if self._match(TokenType.BEGIN):
                self._consume(TokenType.DOT, "Faltou '.' no fim do DB BEGIN.")
                return DbBeginStmt()
            if self._match(TokenType.COMMIT):
                self._consume(TokenType.DOT, "Faltou '.' no fim do DB COMMIT.")
                return DbCommitStmt()
            if self._match(TokenType.ROLLBACK):
                self._consume(TokenType.DOT, "Faltou '.' no fim do DB ROLLBACK.")
                return DbRollbackStmt()
            if self._match(TokenType.COMPACT):
                self._consume(TokenType.DOT, "Faltou '.' no fim do DB COMPACT.")
                return DbCompactStmt()
            raise ParserError("Comando DB inválido. Use DB CREATE, DB OPEN, DB BEGIN, DB COMMIT, DB ROLLBACK ou DB COMPACT.")

        if self._match(TokenType.TABLE):
            self._consume(TokenType.CREATE, "Esperado CREATE após TABLE.")
            table_name = self._consume(TokenType.IDENT, "Esperado nome da tabela.").lexeme
            self._consume(TokenType.LPAREN, "Esperado '(' em TABLE CREATE.")
            cols: List[ColumnDef] = []
            while not self._check(TokenType.RPAREN):
                col_name = self._consume(TokenType.IDENT, "Esperado nome da coluna.").lexeme
                col_type = self._parse_primitive_type()
                primary = False
                auto = False
                if self._match(TokenType.PRIMARY):
                    self._consume(TokenType.KEY, "Esperado KEY após PRIMARY.")
                    primary = True
                if self._match(TokenType.AUTO_INCREMENT):
                    auto = True
                cols.append(ColumnDef(name=col_name, col_type=col_type, primary_key=primary, auto_increment=auto))
                if not self._match(TokenType.COMMA):
                    break
            self._consume(TokenType.RPAREN, "Esperado ')' em TABLE CREATE.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do TABLE CREATE.")
            return TableCreateStmt(table_name=table_name, columns=cols)

        if self._match(TokenType.ALTER):
            self._consume(TokenType.TABLE, "Esperado TABLE após ALTER.")
            table_name = self._consume(TokenType.IDENT, "Esperado tabela no ALTER TABLE.").lexeme
            if self._match(TokenType.ADD):
                self._consume(TokenType.COLUMN, "Esperado COLUMN em ALTER TABLE ADD.")
                col_name = self._consume(TokenType.IDENT, "Esperado nome da coluna.").lexeme
                col_type = self._parse_primitive_type()
                self._consume(TokenType.DOT, "Faltou '.' no fim do ALTER TABLE ADD COLUMN.")
                return AlterTableAddColumnStmt(table_name=table_name, column=ColumnDef(name=col_name, col_type=col_type))
            if self._match(TokenType.DROP):
                self._consume(TokenType.COLUMN, "Esperado COLUMN em ALTER TABLE DROP.")
                col_name = self._consume(TokenType.IDENT, "Esperado nome da coluna.").lexeme
                self._consume(TokenType.DOT, "Faltou '.' no fim do ALTER TABLE DROP COLUMN.")
                return AlterTableDropColumnStmt(table_name=table_name, column_name=col_name)
            if self._match(TokenType.RENAME):
                if self._match(TokenType.COLUMN):
                    old = self._consume(TokenType.IDENT, "Esperado coluna antiga.").lexeme
                    self._consume(TokenType.TO, "Esperado TO em RENAME COLUMN.")
                    new = self._consume(TokenType.IDENT, "Esperado nova coluna.").lexeme
                    self._consume(TokenType.DOT, "Faltou '.' no fim do ALTER TABLE RENAME COLUMN.")
                    return AlterTableRenameColumnStmt(table_name=table_name, old_name=old, new_name=new)
                self._consume(TokenType.TO, "Esperado TO em ALTER TABLE RENAME.")
                new = self._consume(TokenType.IDENT, "Esperado novo nome da tabela.").lexeme
                self._consume(TokenType.DOT, "Faltou '.' no fim do ALTER TABLE RENAME TO.")
                return AlterTableRenameStmt(table_name=table_name, new_name=new)
            raise ParserError("ALTER TABLE inválido.")

        if self._match(TokenType.APPEND):
            if self._match(TokenType.STRUCT):
                struct_var = self._consume(TokenType.IDENT, "Esperado variável de struct no APPEND STRUCT.").lexeme
                self._consume(TokenType.INTO, "Esperado INTO no APPEND STRUCT.")
                table_name = self._consume(TokenType.IDENT, "Esperado tabela destino no APPEND STRUCT.").lexeme
                self._consume(TokenType.DOT, "Faltou '.' no fim do APPEND STRUCT.")
                return AppendStructStmt(struct_var=struct_var, table_name=table_name)
            self._consume(TokenType.INTO, "Esperado INTO no APPEND.")
            table_name = self._consume(TokenType.IDENT, "Esperado nome da tabela no APPEND.").lexeme
            self._consume(TokenType.VALUES, "Esperado VALUES no APPEND.")
            self._consume(TokenType.LPAREN, "Esperado '(' após VALUES.")
            assigns: List[tuple[str, Expr]] = []
            while not self._check(TokenType.RPAREN):
                n = self._consume(TokenType.IDENT, "Esperado coluna em APPEND VALUES.").lexeme
                self._consume(TokenType.EQUAL, "Esperado '=' em APPEND VALUES.")
                e = self._expression()
                assigns.append((n, e))
                if not self._match(TokenType.COMMA):
                    break
            self._consume(TokenType.RPAREN, "Esperado ')' no APPEND VALUES.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do APPEND.")
            return AppendValuesStmt(table_name=table_name, assignments=assigns)

        if self._match(TokenType.UPSERT):
            self._consume(TokenType.INTO, "Esperado INTO no UPSERT.")
            table_name = self._consume(TokenType.IDENT, "Esperado nome da tabela no UPSERT.").lexeme
            self._consume(TokenType.VALUES, "Esperado VALUES no UPSERT.")
            self._consume(TokenType.LPAREN, "Esperado '(' após VALUES.")
            assigns: List[tuple[str, Expr]] = []
            while not self._check(TokenType.RPAREN):
                n = self._consume(TokenType.IDENT, "Esperado coluna em UPSERT VALUES.").lexeme
                self._consume(TokenType.EQUAL, "Esperado '=' em UPSERT VALUES.")
                e = self._expression()
                assigns.append((n, e))
                if not self._match(TokenType.COMMA):
                    break
            self._consume(TokenType.RPAREN, "Esperado ')' no UPSERT VALUES.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do UPSERT.")
            return UpsertStmt(table_name=table_name, assignments=assigns)

        if self._match(TokenType.SELECT):
            if self._match(TokenType.COUNT):
                self._consume(TokenType.LPAREN, "Esperado '(' em COUNT.")
                self._consume(TokenType.STAR, "COUNT na Beta 2 suporta apenas COUNT(*).")
                self._consume(TokenType.RPAREN, "Esperado ')' em COUNT.")
                self._consume(TokenType.FROM, "Esperado FROM no SELECT COUNT.")
                table_name = self._consume(TokenType.IDENT, "Esperado tabela no SELECT COUNT.").lexeme
                cond = None
                if self._match(TokenType.WHERE):
                    cond = self._expression()
                self._consume(TokenType.INTO, "Esperado INTO no SELECT COUNT.")
                dest = self._consume(TokenType.IDENT, "Esperado destino no SELECT COUNT.").lexeme
                self._consume(TokenType.DOT, "Faltou '.' no fim do SELECT COUNT.")
                return SelectCountStmt(table_name=table_name, condition=cond, destination=dest)
            columns: List[str] = []
            if self._match(TokenType.STAR):
                columns = ["*"]
            else:
                columns.append(self._qualified_name())
                while self._match(TokenType.COMMA):
                    columns.append(self._qualified_name())
            self._consume(TokenType.FROM, "Esperado FROM no SELECT.")
            table_name = self._consume(TokenType.IDENT, "Esperado tabela no SELECT.").lexeme
            table_alias = None
            if self._check(TokenType.IDENT):
                table_alias = self._advance().lexeme
            joins: List[JoinClause] = []
            while self._match(TokenType.JOIN):
                join_table = self._consume(TokenType.IDENT, "Esperado tabela no JOIN.").lexeme
                join_alias = join_table
                if self._check(TokenType.IDENT):
                    join_alias = self._advance().lexeme
                self._consume(TokenType.ON, "Esperado ON no JOIN.")
                left_ref = self._qualified_name()
                self._consume(TokenType.EQEQ, "JOIN exige comparação '=='.")
                right_ref = self._qualified_name()
                joins.append(JoinClause(table_name=join_table, alias=join_alias, left_ref=left_ref, right_ref=right_ref))
            cond = None
            if self._match(TokenType.WHERE):
                cond = self._expression()
            self._consume(TokenType.INTO, "Esperado INTO no SELECT.")
            dest = self._consume(TokenType.IDENT, "Esperado destino no SELECT.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim do SELECT.")
            return SelectStmt(table_name=table_name, columns=columns, condition=cond, destination=dest, table_alias=table_alias, joins=joins)

        if self._match(TokenType.UPDATE):
            table_name = self._consume(TokenType.IDENT, "Esperado tabela no UPDATE.").lexeme
            self._consume(TokenType.SET, "Esperado SET no UPDATE.")
            assigns: List[tuple[str, Expr]] = []
            n = self._consume(TokenType.IDENT, "Esperado coluna no UPDATE.").lexeme
            self._consume(TokenType.EQUAL, "Esperado '=' no UPDATE.")
            assigns.append((n, self._expression()))
            while self._match(TokenType.COMMA):
                n = self._consume(TokenType.IDENT, "Esperado coluna no UPDATE.").lexeme
                self._consume(TokenType.EQUAL, "Esperado '=' no UPDATE.")
                assigns.append((n, self._expression()))
            self._consume(TokenType.WHERE, "Esperado WHERE no UPDATE.")
            cond = self._expression()
            self._consume(TokenType.DOT, "Faltou '.' no fim do UPDATE.")
            return UpdateStmt(table_name=table_name, assignments=assigns, condition=cond)

        if self._match(TokenType.DELETE):
            self._consume(TokenType.FROM, "Esperado FROM no DELETE.")
            table_name = self._consume(TokenType.IDENT, "Esperado tabela no DELETE.").lexeme
            self._consume(TokenType.WHERE, "Esperado WHERE no DELETE.")
            cond = self._expression()
            self._consume(TokenType.DOT, "Faltou '.' no fim do DELETE.")
            return DeleteStmt(table_name=table_name, condition=cond)

        if self._match(TokenType.SHOW):
            self._consume(TokenType.TABLES, "Esperado TABLES após SHOW.")
            dest = None
            if self._match(TokenType.INTO):
                dest = self._consume(TokenType.IDENT, "Esperado destino no SHOW TABLES.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim do SHOW TABLES.")
            return ShowTablesStmt(destination=dest)

        if self._match(TokenType.DESCRIBE):
            table_name = self._consume(TokenType.IDENT, "Esperado tabela no DESCRIBE.").lexeme
            dest = None
            if self._match(TokenType.INTO):
                dest = self._consume(TokenType.IDENT, "Esperado destino no DESCRIBE.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim do DESCRIBE.")
            return DescribeStmt(table_name=table_name, destination=dest)

        if self._match(TokenType.INDEX):
            self._consume(TokenType.CREATE, "Esperado CREATE após INDEX.")
            idx_name = self._consume(TokenType.IDENT, "Esperado nome do índice.").lexeme
            self._consume(TokenType.ON, "Esperado ON no INDEX CREATE.")
            table_name = self._consume(TokenType.IDENT, "Esperado tabela no INDEX CREATE.").lexeme
            self._consume(TokenType.LPAREN, "Esperado '(' no INDEX CREATE.")
            column_name = self._consume(TokenType.IDENT, "Esperado coluna no INDEX CREATE.").lexeme
            self._consume(TokenType.RPAREN, "Esperado ')' no INDEX CREATE.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do INDEX CREATE.")
            return IndexCreateStmt(index_name=idx_name, table_name=table_name, column_name=column_name)

        if self._match(TokenType.IF):
            return self._if_stmt()

        if self._match(TokenType.WHILE):
            return self._while_stmt()

        if self._match(TokenType.FOR):
            return self._for_stmt()

        if self._match(TokenType.TRY):
            return self._try_catch_stmt()

        if self._match(TokenType.SWITCH):
            return self._switch_stmt()

        if self._match(TokenType.BREAK):
            self._consume(TokenType.DOT, "Faltou '.' no fim do BREAK.")
            return BreakStmt()

        if self._match(TokenType.CONTINUE):
            self._consume(TokenType.DOT, "Faltou '.' no fim do CONTINUE.")
            return ContinueStmt()

        if self._match(TokenType.RETURN):
            expr = self._expression()
            self._consume(TokenType.DOT, "Faltou '.' no fim do return.")
            return ReturnStmt(expr)

        if self._is_assign_start():
            return self._assign_stmt()

        if self._check(TokenType.IDENT) and self._check_next(TokenType.LPAREN):
            call_expr = self._call_expr()
            self._consume(TokenType.DOT, "Faltou '.' no fim da chamada de função.")
            return CallStmt(call=call_expr)

        t = self._peek()
        raise ParserError(f"Comando inesperado '{t.lexeme}' em {t.line}:{t.col}")

    def _qualified_name(self) -> str:
        name = self._consume(TokenType.IDENT, "Esperado identificador.").lexeme
        if self._match(TokenType.DOT):
            right = self._consume(TokenType.IDENT, "Esperado identificador após '.'.").lexeme
            return f"{name}.{right}"
        return name

    def _if_stmt(self) -> IfStmt:
        condition = self._expression()
        self._consume(TokenType.DOT, "Faltou '.' após condição do if.")
        branches = [IfBranch(condition, self._block_until({TokenType.ELSEIF, TokenType.ELSE, TokenType.ENDIF}))]

        while self._match(TokenType.ELSEIF):
            cond = self._expression()
            self._consume(TokenType.DOT, "Faltou '.' após condição do elseif.")
            body = self._block_until({TokenType.ELSEIF, TokenType.ELSE, TokenType.ENDIF})
            branches.append(IfBranch(cond, body))

        else_body = None
        if self._match(TokenType.ELSE):
            self._consume(TokenType.DOT, "Faltou '.' após else.")
            else_body = self._block_until({TokenType.ENDIF})

        self._consume(TokenType.ENDIF, "Esperado 'endif'.")
        self._consume(TokenType.DOT, "Faltou '.' após endif.")
        return IfStmt(branches, else_body)

    def _while_stmt(self) -> WhileStmt:
        condition = self._expression()
        self._consume(TokenType.DOT, "Faltou '.' após condição do while.")
        body = self._block_until({TokenType.ENDWHILE})
        self._consume(TokenType.ENDWHILE, "Esperado 'endwhile'.")
        self._consume(TokenType.DOT, "Faltou '.' após endwhile.")
        return WhileStmt(condition, body)

    def _for_stmt(self) -> ForStmt:
        item_name = self._consume(TokenType.IDENT, "Esperado variável de iteração no FOR.").lexeme
        self._consume(TokenType.IN, "Esperado 'IN' no FOR.")
        collection = self._expression()
        self._consume(TokenType.DOT, "Faltou '.' após cabeçalho do FOR.")
        body = self._block_until({TokenType.ENDFOR})
        self._consume(TokenType.ENDFOR, "Esperado 'ENDFOR'.")
        self._consume(TokenType.DOT, "Faltou '.' após ENDFOR.")
        return ForStmt(item_name=item_name, collection=collection, body=body)

    def _switch_stmt(self) -> SwitchStmt:
        expression = self._expression()
        self._consume(TokenType.DOT, "Faltou '.' após expressão do SWITCH.")
        cases: List[SwitchCase] = []
        default_body = None
        while self._match(TokenType.CASE):
            case_expr = self._expression()
            self._consume(TokenType.DOT, "Faltou '.' após CASE.")
            body = self._block_until({TokenType.CASE, TokenType.DEFAULT, TokenType.ENDSWITCH})
            cases.append(SwitchCase(value=case_expr, body=body))
        if self._match(TokenType.DEFAULT):
            self._consume(TokenType.DOT, "Faltou '.' após DEFAULT.")
            default_body = self._block_until({TokenType.ENDSWITCH})
        self._consume(TokenType.ENDSWITCH, "Esperado ENDSWITCH.")
        self._consume(TokenType.DOT, "Faltou '.' após ENDSWITCH.")
        return SwitchStmt(expression=expression, cases=cases, default_body=default_body)

    def _try_catch_stmt(self) -> TryCatchStmt:
        self._consume(TokenType.DOT, "Faltou '.' após TRY.")
        try_body = self._block_until({TokenType.CATCH})
        self._consume(TokenType.CATCH, "TRY sem CATCH não é permitido.")
        self._consume(TokenType.DOT, "Faltou '.' após CATCH.")
        catch_body = self._block_until({TokenType.ENDTRY})
        self._consume(TokenType.ENDTRY, "ENDTRY esperado.")
        self._consume(TokenType.DOT, "Faltou '.' após ENDTRY.")
        return TryCatchStmt(try_body=try_body, catch_body=catch_body)

    def _call_expr(self) -> CallExpr:
        name = self._consume(TokenType.IDENT, "Esperado nome da função.").lexeme
        self._consume(TokenType.LPAREN, "Esperado '(' após nome da função.")
        args: List[Expr] = []
        if not self._check(TokenType.RPAREN):
            args.append(self._expression())
            while self._match(TokenType.COMMA):
                args.append(self._expression())
        self._consume(TokenType.RPAREN, "Esperado ')' após argumentos da chamada.")
        return CallExpr(name=name, args=args)

    def _assign_stmt(self) -> AssignStmt:
        target = self._assignment_target()
        self._consume(TokenType.EQUAL, "Esperado '=' na atribuição.")
        expr = self._expression()
        self._consume(TokenType.DOT, "Faltou '.' no fim da atribuição.")
        return AssignStmt(target=target, expr=expr)

    def _assignment_target(self) -> Expr:
        name = self._consume(TokenType.IDENT, "Esperado nome da variável.").lexeme
        target: Expr = VarRef(name)
        if self._match(TokenType.DOT):
            field = self._consume(TokenType.IDENT, "Esperado nome do campo.").lexeme
            target = FieldAccessExpr(base=target, field=field)
        return target

    def _is_assign_start(self) -> bool:
        if not self._check(TokenType.IDENT):
            return False
        if self._check_next(TokenType.EQUAL):
            return True
        if self.i + 3 < len(self.tokens):
            return (
                self.tokens[self.i + 1].type == TokenType.DOT
                and self.tokens[self.i + 2].type == TokenType.IDENT
                and self.tokens[self.i + 3].type == TokenType.EQUAL
            )
        return False

    def _block_until(self, stop: set[TokenType]) -> List[Stmt]:
        body: List[Stmt] = []
        while not self._check_any(stop) and not self._check(TokenType.EOF):
            body.append(self._statement())
        return body

    # -------------------------
    # Expressions
    # -------------------------
    def _expression(self) -> Expr:
        return self._or()

    def _or(self) -> Expr:
        expr = self._and()
        while self._match(TokenType.OR):
            op = self._previous().lexeme.lower()
            right = self._and()
            expr = Binary(expr, op, right)
        return expr

    def _and(self) -> Expr:
        expr = self._not()
        while self._match(TokenType.AND):
            op = self._previous().lexeme.lower()
            right = self._not()
            expr = Binary(expr, op, right)
        return expr

    def _not(self) -> Expr:
        if self._match(TokenType.NOT):
            op = self._previous().lexeme.lower()
            right = self._not()
            return Unary(op, right)
        return self._comparison()

    def _comparison(self) -> Expr:
        expr = self._term()
        while self._match(TokenType.EQEQ, TokenType.NOTEQ, TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self._previous().lexeme
            right = self._term()
            expr = Binary(expr, op, right)
        return expr

    def _term(self) -> Expr:
        expr = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous().lexeme
            right = self._factor()
            expr = Binary(expr, op, right)
        return expr

    def _factor(self) -> Expr:
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.MOD):
            op = self._previous().lexeme
            right = self._unary()
            expr = Binary(expr, op, right)
        return expr

    def _unary(self) -> Expr:
        if self._match(TokenType.MINUS, TokenType.PLUS):
            op = self._previous().lexeme
            right = self._unary()
            return Unary(op, right)
        return self._primary()

    def _primary(self) -> Expr:
        if self._match(TokenType.NUMBER):
            return IntLit(int(self._previous().lexeme))

        if self._match(TokenType.FLOAT):
            return FloatLit(float(self._previous().lexeme))

        if self._match(TokenType.STRING):
            return StringLit(self._previous().lexeme)

        if self._match(TokenType.CHAR):
            return CharLit(self._previous().lexeme)

        if self._match(TokenType.TRUE):
            return BoolLit(True)

        if self._match(TokenType.FALSE):
            return BoolLit(False)

        if self._match(TokenType.SIZE):
            self._consume(TokenType.LPAREN, "Esperado '(' após size.")
            collection = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após size(collection).")
            return SizeCall(collection=collection)

        if self._match(TokenType.COUNT):
            self._consume(TokenType.LPAREN, "Esperado '(' após count.")
            collection = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após count(collection).")
            return CountExpr(collection=collection)

        if self._match(TokenType.SUM):
            self._consume(TokenType.LPAREN, "Esperado '(' após sum.")
            target = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após sum(...).")
            return SumExpr(target=target)

        if self._match(TokenType.AVG):
            self._consume(TokenType.LPAREN, "Esperado '(' após avg.")
            target = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após avg(...).")
            return AvgExpr(target=target)

        if self._match(TokenType.IDENT):
            name = self._previous().lexeme
            if self._match(TokenType.LPAREN):
                args: List[Expr] = []
                if not self._check(TokenType.RPAREN):
                    args.append(self._expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._expression())
                self._consume(TokenType.RPAREN, "Esperado ')' após argumentos da chamada.")
                return CallExpr(name=name, args=args)
            expr: Expr = VarRef(name)
            expr = self._parse_postfix(expr)
            return expr

        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após expressão.")
            return expr

        t = self._peek()
        raise ParserError(f"Esperada expressão, achei '{t.lexeme}' em {t.line}:{t.col}")

    def _parse_postfix(self, expr: Expr) -> Expr:
        while True:
            if self._match(TokenType.LBRACKET):
                index = self._expression()
                self._consume(TokenType.RBRACKET, "Esperado ']' no acesso por índice.")
                expr = IndexAccessExpr(base=expr, index=index)
                continue
            if self._check(TokenType.DOT) and self._check_next(TokenType.IDENT):
                self._advance()
                field = self._consume(TokenType.IDENT, "Esperado nome do campo.").lexeme
                expr = FieldAccessExpr(base=expr, field=field)
                continue
            break
        return expr

    # -------------------------
    # Helpers
    # -------------------------
    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, ttype: TokenType, message: str) -> Token:
        if self._check(ttype):
            return self._advance()
        t = self._peek()
        raise ParserError(f"{message} (em {t.line}:{t.col})")

    def _check(self, ttype: TokenType) -> bool:
        return self._peek().type == ttype

    def _check_any(self, types: set[TokenType]) -> bool:
        return self._peek().type in types

    def _check_next(self, ttype: TokenType) -> bool:
        if self.i + 1 >= len(self.tokens):
            return False
        return self.tokens[self.i + 1].type == ttype

    def _advance(self) -> Token:
        if not self._check(TokenType.EOF):
            self.i += 1
        return self._previous()

    def _peek(self) -> Token:
        return self.tokens[self.i]

    def _previous(self) -> Token:
        return self.tokens[self.i - 1]
