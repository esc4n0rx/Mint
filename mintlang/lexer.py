from __future__ import annotations
from typing import List
from .tokens import Token, TokenType
from .errors import LexerError

KEYWORDS = {
    "program": TokenType.PROGRAM,
    "init": TokenType.INIT,
    "initialization": TokenType.INITIALIZATION,
    "endprogram": TokenType.ENDPROGRAM,

    "var": TokenType.VAR,
    "type": TokenType.TYPE,

    "int": TokenType.INT_T,
    "string": TokenType.STRING_T,
    "bool": TokenType.BOOL_T,
    "float": TokenType.FLOAT_T,
    "char": TokenType.CHAR_T,
    "list": TokenType.LIST,
    "table": TokenType.TABLE,

    "true": TokenType.TRUE,
    "false": TokenType.FALSE,

    "write": TokenType.WRITE,
    "add": TokenType.ADD,
    "insert": TokenType.INSERT,
    "size": TokenType.SIZE,
    "input": TokenType.INPUT,
    "move": TokenType.MOVE,
    "to": TokenType.TO,
    "load": TokenType.LOAD,
    "save": TokenType.SAVE,
    "export": TokenType.EXPORT,
    "query": TokenType.QUERY,
    "from": TokenType.FROM,
    "where": TokenType.WHERE,
    "into": TokenType.INTO,
    "db": TokenType.DB,
    "create": TokenType.CREATE,
    "open": TokenType.OPEN,
    "append": TokenType.APPEND,
    "values": TokenType.VALUES,
    "select": TokenType.SELECT,
    "update": TokenType.UPDATE,
    "set": TokenType.SET,
    "delete": TokenType.DELETE,
    "primary": TokenType.PRIMARY,
    "key": TokenType.KEY,
    "auto_increment": TokenType.AUTO_INCREMENT,
    "if": TokenType.IF,
    "elseif": TokenType.ELSEIF,
    "else": TokenType.ELSE,
    "endif": TokenType.ENDIF,
    "while": TokenType.WHILE,
    "endwhile": TokenType.ENDWHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "endfor": TokenType.ENDFOR,
    "try": TokenType.TRY,
    "catch": TokenType.CATCH,
    "endtry": TokenType.ENDTRY,
    "count": TokenType.COUNT,
    "sum": TokenType.SUM,
    "avg": TokenType.AVG,
    "func": TokenType.FUNC,
    "endfunc": TokenType.ENDFUNC,
    "return": TokenType.RETURN,
    "returns": TokenType.RETURNS,
    "struct": TokenType.STRUCT,
    "endstruct": TokenType.ENDSTRUCT,
    "import": TokenType.IMPORT,
    "IMPORT": TokenType.IMPORT,
    "FUNC": TokenType.FUNC,
    "ENDFUNC": TokenType.ENDFUNC,
    "RETURN": TokenType.RETURN,
    "RETURNS": TokenType.RETURNS,
    "STRUCT": TokenType.STRUCT,
    "ENDSTRUCT": TokenType.ENDSTRUCT,
    "QUERY": TokenType.QUERY,
    "FROM": TokenType.FROM,
    "WHERE": TokenType.WHERE,
    "INTO": TokenType.INTO,
    "DB": TokenType.DB,
    "CREATE": TokenType.CREATE,
    "OPEN": TokenType.OPEN,
    "APPEND": TokenType.APPEND,
    "VALUES": TokenType.VALUES,
    "SELECT": TokenType.SELECT,
    "UPDATE": TokenType.UPDATE,
    "SET": TokenType.SET,
    "DELETE": TokenType.DELETE,
    "PRIMARY": TokenType.PRIMARY,
    "KEY": TokenType.KEY,
    "AUTO_INCREMENT": TokenType.AUTO_INCREMENT,
    "TABLE": TokenType.TABLE,
    "DB": TokenType.DB,
    "LOAD": TokenType.LOAD,
    "SAVE": TokenType.SAVE,
    "EXPORT": TokenType.EXPORT,
    "TO": TokenType.TO,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "NOT": TokenType.NOT,
    "FOR": TokenType.FOR,
    "IN": TokenType.IN,
    "ENDFOR": TokenType.ENDFOR,
    "TRY": TokenType.TRY,
    "CATCH": TokenType.CATCH,
    "ENDTRY": TokenType.ENDTRY,
}

class Lexer:
    """
    Regras:
    - String literal: "texto" (com escapes \", \n, \t)
    - Comentário estilo BASIC: " comentário" somente se " for o primeiro não-espaço da linha
    - Comentário inline adicional: // comentário (em qualquer lugar)
    """
    def __init__(self, source: str):
        self.source = source
        self.i = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self._line_has_code = False  # virou True quando aparece o primeiro token não-whitespace na linha

    def tokenize(self) -> List[Token]:
        while not self._is_at_end():
            c = self._peek()

            # whitespace
            if c in " \t\r":
                self._advance()
                continue

            # newline
            if c == "\n":
                self._advance_newline()
                continue

            start_line, start_col = self.line, self.col

            # comentário // (inline)
            if c == "/" and self._peek_next() == "/":
                self._consume_line_comment()
                continue

            # comentário com " somente no começo lógico da linha (antes de qualquer código)
            if c == '"' and not self._line_has_code:
                self._consume_line_comment_quote()
                continue

            # números
            if c.isdigit():
                self._line_has_code = True
                self.tokens.append(self._number(start_line, start_col))
                continue

            # identificadores / keywords
            if c.isalpha() or c == "_":
                self._line_has_code = True
                self.tokens.append(self._identifier_or_keyword(start_line, start_col))
                continue

            # string literal
            if c == '"':
                self._line_has_code = True
                self.tokens.append(self._string(start_line, start_col))
                continue
            # char literal
            if c == "'":
                self._line_has_code = True
                self.tokens.append(self._char(start_line, start_col))
                continue

            # operators (one or two chars)
            if c == "=":
                self._line_has_code = True
                if self._peek_next() == "=":
                    self._advance()
                    self._advance()
                    self.tokens.append(Token(TokenType.EQEQ, "==", start_line, start_col))
                else:
                    self._advance()
                    self.tokens.append(Token(TokenType.EQUAL, "=", start_line, start_col))
                continue
            if c == "!":
                self._line_has_code = True
                if self._peek_next() == "=":
                    self._advance()
                    self._advance()
                    self.tokens.append(Token(TokenType.NOTEQ, "!=", start_line, start_col))
                    continue
                raise LexerError(f"Caractere inesperado '{c}' em {start_line}:{start_col}")
            if c == "<":
                self._line_has_code = True
                if self._peek_next() == "=":
                    self._advance()
                    self._advance()
                    self.tokens.append(Token(TokenType.LTE, "<=", start_line, start_col))
                else:
                    self._advance()
                    self.tokens.append(Token(TokenType.LT, "<", start_line, start_col))
                continue
            if c == ">":
                self._line_has_code = True
                if self._peek_next() == "=":
                    self._advance()
                    self._advance()
                    self.tokens.append(Token(TokenType.GTE, ">=", start_line, start_col))
                else:
                    self._advance()
                    self.tokens.append(Token(TokenType.GT, ">", start_line, start_col))
                continue

            # single-char tokens
            single = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                ".": TokenType.DOT,
                ",": TokenType.COMMA,
            }
            if c in single:
                self._line_has_code = True
                self._advance()
                self.tokens.append(Token(single[c], c, start_line, start_col))
                continue

            raise LexerError(f"Caractere inesperado '{c}' em {start_line}:{start_col}")

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens

    def _consume_line_comment(self) -> None:
        # consome // e tudo até a quebra de linha
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _consume_line_comment_quote(self) -> None:
        # consome " e tudo até a quebra de linha
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _string(self, start_line: int, start_col: int) -> Token:
        # consume opening "
        self._advance()
        chars = []
        while not self._is_at_end():
            c = self._peek()
            if c == '"':
                self._advance()
                return Token(TokenType.STRING, "".join(chars), start_line, start_col)
            if c == "\\":
                self._advance()
                if self._is_at_end():
                    break
                esc = self._peek()
                if esc == '"':
                    chars.append('"')
                elif esc == "n":
                    chars.append("\n")
                elif esc == "t":
                    chars.append("\t")
                else:
                    chars.append(esc)
                self._advance()
                continue
            if c == "\n":
                raise LexerError(f"String não fechada em {start_line}:{start_col}")
            chars.append(c)
            self._advance()

        raise LexerError(f"String não fechada em {start_line}:{start_col}")

    def _char(self, start_line: int, start_col: int) -> Token:
        # consume opening '
        self._advance()
        chars = []
        while not self._is_at_end():
            c = self._peek()
            if c == "'":
                self._advance()
                return Token(TokenType.CHAR, "".join(chars), start_line, start_col)
            if c == "\\":
                self._advance()
                if self._is_at_end():
                    break
                esc = self._peek()
                if esc == "'":
                    chars.append("'")
                elif esc == "n":
                    chars.append("\n")
                elif esc == "t":
                    chars.append("\t")
                elif esc == "\\":
                    chars.append("\\")
                else:
                    chars.append(esc)
                self._advance()
                continue
            if c == "\n":
                raise LexerError(f"Char não fechado em {start_line}:{start_col}")
            chars.append(c)
            self._advance()

        raise LexerError(f"Char não fechado em {start_line}:{start_col}")

    def _number(self, start_line: int, start_col: int) -> Token:
        start = self.i
        while not self._is_at_end() and self._peek().isdigit():
            self._advance()
        if not self._is_at_end() and self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while not self._is_at_end() and self._peek().isdigit():
                self._advance()
            lexeme = self.source[start:self.i]
            return Token(TokenType.FLOAT, lexeme, start_line, start_col)
        lexeme = self.source[start:self.i]
        return Token(TokenType.NUMBER, lexeme, start_line, start_col)

    def _identifier_or_keyword(self, start_line: int, start_col: int) -> Token:
        start = self.i
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        text = self.source[start:self.i]
        ttype = KEYWORDS.get(text, TokenType.IDENT)
        return Token(ttype, text, start_line, start_col)

    def _advance(self) -> str:
        c = self.source[self.i]
        self.i += 1
        self.col += 1
        return c

    def _advance_newline(self):
        self.i += 1
        self.line += 1
        self.col = 1
        self._line_has_code = False

    def _peek(self) -> str:
        return self.source[self.i]

    def _peek_next(self) -> str:
        if self.i + 1 >= len(self.source):
            return "\0"
        return self.source[self.i + 1]

    def _is_at_end(self) -> bool:
        return self.i >= len(self.source)
