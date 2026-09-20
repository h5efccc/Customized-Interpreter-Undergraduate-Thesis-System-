from __future__ import annotations
from dataclasses import dataclass
from .tokens import Token


class Stmt:
    pass


class Expr:
    pass


@dataclass(frozen=True)
class VarDeclStmt(Stmt):
    """Typed variable / array declaration: DATATYPE IDENT = Expression ;"""
    datatype: str
    name: str
    value: Expr


@dataclass(frozen=True)
class AssignStmt(Stmt):
    """Assignment statement: target = Expression ;"""
    target: Expr
    value: Expr


@dataclass(frozen=True)
class ExprStmt(Stmt):
    """Expression used as a statement (e.g. i++;)."""
    expr: Expr


@dataclass(frozen=True)
class PrintStmt(Stmt):
    expr: Expr


@dataclass(frozen=True)
class BlockStmt(Stmt):
    """Curly-brace block: { Statement* }"""
    statements: tuple[Stmt, ...]


@dataclass(frozen=True)
class IfStmt(Stmt):
    """Java-style if / else: if (cond) { ... } else { ... }"""
    condition: Expr
    then_branch: BlockStmt
    else_branch: Stmt | None  # BlockStmt, nested IfStmt (else if), or None


@dataclass(frozen=True)
class WhileStmt(Stmt):
    """while (condition) { ... }"""
    condition: Expr
    body: BlockStmt


@dataclass(frozen=True)
class DoWhileStmt(Stmt):
    """do { ... } while (condition);"""
    body: BlockStmt
    condition: Expr


@dataclass(frozen=True)
class ForStmt(Stmt):
    """for (init; condition; update) { ... }"""
    initializer: Stmt | None
    condition: Expr | None
    update: Expr | None
    body: BlockStmt


@dataclass(frozen=True)
class BinaryExpr(Expr):
    left: Expr
    op: Token
    right: Expr


@dataclass(frozen=True)
class UnaryExpr(Expr):
    op: Token
    right: Expr


@dataclass(frozen=True)
class UpdateExpr(Expr):
    """Prefix or postfix ++ / -- on an lvalue."""
    op: Token
    target: Expr
    prefix: bool


@dataclass(frozen=True)
class AssignExpr(Expr):
    """Assignment used inside for-headers / expressions: target = value."""
    target: Expr
    value: Expr


@dataclass(frozen=True)
class IndexExpr(Expr):
    """Array indexing: array[index]"""
    array: Expr
    index: Expr


@dataclass(frozen=True)
class ArrayLiteral(Expr):
    """Array initializer: { e1, e2, ... }"""
    elements: tuple[Expr, ...]


@dataclass(frozen=True)
class NumberLiteral(Expr):
    value: float


@dataclass(frozen=True)
class StringLiteral(Expr):
    value: str


@dataclass(frozen=True)
class BoolLiteral(Expr):
    value: bool


@dataclass(frozen=True)
class Variable(Expr):
    name: str


@dataclass(frozen=True)
class IncompleteExpr(Expr):
    """Placeholder used when a syntax error cuts an expression short."""
    placeholder: str = "<incomplete>"
