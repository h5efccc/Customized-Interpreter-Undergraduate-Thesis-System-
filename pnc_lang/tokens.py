from __future__ import annotations
from dataclasses import dataclass
from typing import Any


class TokenType:
    # single-character operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"  # Multiplication
    SLASH = "SLASH"  # Division
    EQUAL = "EQUAL"
    BANG = "BANG"  # !
    LESS = "LESS"
    GREATER = "GREATER"

    # two-character operators
    PLUSPLUS = "PLUSPLUS"  # ++
    MINUSMINUS = "MINUSMINUS"  # --
    EQEQ = "EQEQ"  # ==
    BANG_EQUAL = "BANG_EQUAL"  # !=
    LESS_EQUAL = "LESS_EQUAL"  # <=
    GREATER_EQUAL = "GREATER_EQUAL"  # >=
    ANDAND = "ANDAND"  # &&
    OROR = "OROR"  # ||

    # punctuation
    LPAREN = "LPAREN"  # Left
    RPAREN = "RPAREN"  # Right
    LBRACE = "LBRACE"  # {
    RBRACE = "RBRACE"  # }
    LBRACKET = "LBRACKET"  # [
    RBRACKET = "RBRACKET"  # ]
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    EOF = "EOF"  # EndOfFile

    # literals and identifiers
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENT = "IDENT"

    # keywords (int, double, string, boolean, print, if, else, while, for, do, true, false)
    RESERVED_KEYWORD = "KEYWORD"

    # comments (recognized by lexer, skipped by parser)
    LINE_COMMENT = "LINE_COMMENT"
    BLOCK_COMMENT = "BLOCK_COMMENT"

    # lexical failure fragment (shown in the token table / FA path)
    ERROR = "ERROR"


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
