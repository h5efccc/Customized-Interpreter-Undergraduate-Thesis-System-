from __future__ import annotations
from dataclasses import dataclass
from .tokens import Token

class Stmt:
    pass


class Expr:
    pass

@dataclass(frozen=True)
class LetStmt(Stmt):
    name: str
    value: Expr


@dataclass(frozen=True)
class PrintStmt(Stmt):
    expr: Expr


@dataclass(frozen=True)
class BinaryExpr(Expr):
    left: Expr
    op: Token
    right: Expr


@dataclass(frozen=True)
class NumberLiteral(Expr):
    value: float


@dataclass(frozen=True)
class StringLiteral(Expr):
    value: str


@dataclass(frozen=True)
class Variable(Expr):
    name: str

