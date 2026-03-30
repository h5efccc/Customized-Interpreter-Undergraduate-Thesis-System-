from __future__ import annotations
from typing import Any

from .ast_nodes import (
    BinaryExpr,
    Expr,
    LetStmt,
    NumberLiteral,
    PrintStmt,
    Stmt,
    StringLiteral,
    Variable,
)
from .tokens import TokenType


class RuntimeError_(Exception):
    pass


class Interpreter:
    def __init__(self):
        self.env: dict[str, Any] = {}

    def run(self, statements: list[Stmt]) -> None:
        for stmt in statements:
            self._execute(stmt)

    def _execute(self, stmt: Stmt) -> None:
        if isinstance(stmt, LetStmt):
            self.env[stmt.name] = self._evaluate(stmt.value)
            return

        if isinstance(stmt, PrintStmt):
            print(self._evaluate(stmt.expr))
            return

        raise RuntimeError_(f"Unknown statement type: {stmt}")

    def _evaluate(self, expr: Expr) -> Any:
        if isinstance(expr, NumberLiteral):
            return expr.value
        if isinstance(expr, StringLiteral):
            return expr.value
        if isinstance(expr, Variable):
            if expr.name not in self.env:
                raise RuntimeError_(f"Undefined variable '{expr.name}'")
            return self.env[expr.name]
        if isinstance(expr, BinaryExpr):
            left = self._evaluate(expr.left)
            right = self._evaluate(expr.right)
            op_type = expr.op.type

            if op_type == TokenType.PLUS:
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise RuntimeError_(
                    f"Type error: cannot apply '+' to {type(left).__name__} and {type(right).__name__}"
                )

            if op_type in (TokenType.MINUS, TokenType.STAR, TokenType.SLASH):
                if not (isinstance(left, (int, float)) and isinstance(right, (int, float))):
                    raise RuntimeError_(
                        f"Type error: cannot apply {expr.op.lexeme!r} to {type(left).__name__} and {type(right).__name__}"
                    )
                if op_type == TokenType.MINUS:
                    return left - right
                if op_type == TokenType.STAR:
                    return left * right
                if op_type == TokenType.SLASH:
                    if right == 0:
                        raise RuntimeError_("Division by zero")
                    return left / right

            raise RuntimeError_(f"Unknown operator {expr.op.lexeme!r}")

        raise RuntimeError_(f"Unknown expression type: {expr}")

