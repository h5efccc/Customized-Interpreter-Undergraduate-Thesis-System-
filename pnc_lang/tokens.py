from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class TokenType:
    # single-character operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    EQUAL = "EQUAL"

    # punctuation
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    NEWLINE = "NEWLINE"
    EOF = "EOF"

    # literals and identifiers
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENT = "IDENT"

    # keywords
    LET = "LET"
    PRINT = "PRINT"


@dataclass(frozen=True)
class Token:
    type: str
    lexeme: str
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return (
            f"Token({self.type}, {self.lexeme!r}, {self.value!r}, "
            f"line={self.line}, col={self.column})"
        )

