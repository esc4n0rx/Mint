from dataclasses import dataclass
from enum import Enum, auto

class TokenType(Enum):
    # Operators / punctuation
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    LPAREN = auto()
    RPAREN = auto()
    EQUAL = auto()
    DOT = auto()

    # Literals / identifiers
    NUMBER = auto()
    FLOAT = auto()
    STRING = auto()
    CHAR = auto()
    IDENT = auto()

    # Keywords
    PROGRAM = auto()
    INIT = auto()
    INITIALIZATION = auto()
    ENDPROGRAM = auto()

    VAR = auto()
    TYPE = auto()

    INT_T = auto()
    STRING_T = auto()
    BOOL_T = auto()
    FLOAT_T = auto()
    CHAR_T = auto()

    TRUE = auto()
    FALSE = auto()

    WRITE = auto()

    # Special
    EOF = auto()

@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    col: int
