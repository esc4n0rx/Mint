from __future__ import annotations
from typing import List, Optional
from .tokens import Token, TokenType
from .errors import ParserError
from .ast_nodes import (
    Program, Stmt, WriteStmt, VarDeclStmt, IfStmt, IfBranch, AssignStmt, WhileStmt, InputStmt, MoveStmt,
    Expr, IntLit, FloatLit, StringLit, CharLit, BoolLit, VarRef, Binary, Unary, MintType
)

class Parser:
    """
    Gramática (MVP 2):
      program      -> "program" "init" "." decls "initialization" "." stmts "endprogram" "."
      decls        -> ( "var" IDENT "type" TYPE ( "=" expr )? "." )*
      stmts        -> ( write_stmt | input_stmt | move_stmt | if_stmt | assign_stmt | while_stmt )*
      write_stmt   -> "write" "(" expr ")" "."
      input_stmt   -> "input" "(" expr ")" "."
      move_stmt    -> "move" expr "to" IDENT "."
      if_stmt      -> "if" expr "." stmts ( "elseif" expr "." stmts )* ( "else" "." stmts )? "endif" "."
      assign_stmt  -> IDENT "=" expr "."
      while_stmt   -> "while" expr "." stmts "endwhile" "."
      expr         -> or_expr
      or_expr      -> and_expr ( "or" and_expr )*
      and_expr     -> not_expr ( "and" not_expr )*
      not_expr     -> "not" not_expr | comparison
      comparison   -> term (("==" | "!=" | "<" | ">" | "<=" | ">=") term)*
      term         -> factor (("+" | "-") factor)*
      factor       -> unary (("*" | "/") unary)*
      unary        -> (("+" | "-") unary) | primary
      primary      -> NUMBER | FLOAT | STRING | CHAR | TRUE | FALSE | IDENT | "(" expr ")"
      TYPE         -> "int" | "string" | "bool" | "float" | "char"
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def parse(self) -> Program:
        self._consume(TokenType.PROGRAM, "Esperado 'program'.")
        self._consume(TokenType.INIT, "Esperado 'init' após 'program'.")
        self._consume(TokenType.DOT, "Esperado '.' após 'program init'.")

        decls: List[VarDeclStmt] = []
        while self._check(TokenType.VAR):
            decls.append(self._vardecl())

        self._consume(TokenType.INITIALIZATION, "Esperado 'initialization'.")
        self._consume(TokenType.DOT, "Esperado '.' após 'initialization'.")

        body: List[Stmt] = []
        while not self._check(TokenType.ENDPROGRAM) and not self._check(TokenType.EOF):
            body.append(self._statement())

        self._consume(TokenType.ENDPROGRAM, "Esperado 'endprogram'.")
        self._consume(TokenType.DOT, "Esperado '.' após 'endprogram'.")

        # opcional: aceitar apenas EOF depois
        if not self._check(TokenType.EOF):
            t = self._peek()
            raise ParserError(f"Texto extra após endprogram em {t.line}:{t.col}")

        return Program(decls=decls, body=body)

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
        t = self._peek()
        raise ParserError(f"Tipo inválido '{t.lexeme}' em {t.line}:{t.col}")

    def _statement(self) -> Stmt:
        if self._match(TokenType.WRITE):
            self._consume(TokenType.LPAREN, "Esperado '(' após write.")
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após expressão do write.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do write.")
            return WriteStmt(expr)

        if self._match(TokenType.INPUT):
            self._consume(TokenType.LPAREN, "Esperado '(' após input.")
            target = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após alvo do input.")
            self._consume(TokenType.DOT, "Faltou '.' no fim do input.")
            return InputStmt(target)

        if self._match(TokenType.MOVE):
            source = self._expression()
            self._consume(TokenType.TO, "Esperado 'to' no comando move.")
            target = self._consume(TokenType.IDENT, "Esperado variável destino no move.").lexeme
            self._consume(TokenType.DOT, "Faltou '.' no fim do move.")
            return MoveStmt(source=source, target=target)

        if self._match(TokenType.IF):
            return self._if_stmt()

        if self._match(TokenType.WHILE):
            return self._while_stmt()

        if self._check(TokenType.IDENT) and self._check_next(TokenType.EQUAL):
            return self._assign_stmt()

        t = self._peek()
        raise ParserError(f"Comando inesperado '{t.lexeme}' em {t.line}:{t.col}")

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

    def _assign_stmt(self) -> AssignStmt:
        name = self._consume(TokenType.IDENT, "Esperado nome da variável.").lexeme
        self._consume(TokenType.EQUAL, "Esperado '=' na atribuição.")
        expr = self._expression()
        self._consume(TokenType.DOT, "Faltou '.' no fim da atribuição.")
        return AssignStmt(name=name, expr=expr)

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
            op = self._previous().lexeme
            right = self._and()
            expr = Binary(expr, op, right)
        return expr

    def _and(self) -> Expr:
        expr = self._not()
        while self._match(TokenType.AND):
            op = self._previous().lexeme
            right = self._not()
            expr = Binary(expr, op, right)
        return expr

    def _not(self) -> Expr:
        if self._match(TokenType.NOT):
            op = self._previous().lexeme
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
        while self._match(TokenType.STAR, TokenType.SLASH):
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

        if self._match(TokenType.IDENT):
            return VarRef(self._previous().lexeme)

        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após expressão.")
            return expr

        t = self._peek()
        raise ParserError(f"Esperada expressão, achei '{t.lexeme}' em {t.line}:{t.col}")

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
