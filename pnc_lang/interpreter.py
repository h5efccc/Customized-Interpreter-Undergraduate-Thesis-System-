from __future__ import annotations
from typing import Any

from .ast_nodes import (
    ArrayLiteral,
    AssignExpr,
    AssignStmt,
    BinaryExpr,
    BlockStmt,
    BoolLiteral,
    DoWhileStmt,
    Expr,
    ExprStmt,
    ForStmt,
    IfStmt,
    IndexExpr,
    NumberLiteral,
    PrintStmt,
    Stmt,
    StringLiteral,
    UnaryExpr,
    UpdateExpr,
    VarDeclStmt,
    Variable,
    WhileStmt,
)
from .tokens import TokenType


# Educational runtime guards — prevent infinite loops / output floods from freezing the GUI.
MAX_LOOP_ITERATIONS = 5_000
MAX_PRINT_STATEMENTS = 500
MAX_OUTPUT_CHARS = 40_000


class RuntimeError_(Exception):
    pass


class Interpreter:
    def __init__(
        self,
        *,
        max_loop_iterations: int = MAX_LOOP_ITERATIONS,
        max_print_statements: int = MAX_PRINT_STATEMENTS,
    ) -> None:
        self.env: dict[str, Any] = {}
        self.types: dict[str, str] = {}
        self.max_loop_iterations = max_loop_iterations
        self.max_print_statements = max_print_statements
        self._print_count = 0

    def run(self, statements: list[Stmt]) -> None:
        for stmt in statements:
            self._execute(stmt)

    def _check_loop_limit(self, kind: str, iterations: int) -> None:
        if iterations > self.max_loop_iterations:
            raise RuntimeError_(
                f"Runtime limit: {kind} loop exceeded {self.max_loop_iterations:,} iterations "
                f"(possible infinite loop). Make sure the loop condition eventually becomes false, "
                f"or reduce how many times the body runs."
            )

    def _execute(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDeclStmt):
            value = self._evaluate(stmt.value)
            value = self._coerce_and_check(stmt.datatype, stmt.name, value)
            self.env[stmt.name] = value
            self.types[stmt.name] = stmt.datatype
            return

        if isinstance(stmt, AssignStmt):
            self._assign(stmt.target, stmt.value)
            return

        if isinstance(stmt, ExprStmt):
            self._evaluate(stmt.expr)
            return

        if isinstance(stmt, PrintStmt):
            self._print_count += 1
            if self._print_count > self.max_print_statements:
                raise RuntimeError_(
                    f"Runtime limit: more than {self.max_print_statements:,} print statements "
                    f"(possible infinite loop). Stop printing endlessly, or add a loop condition "
                    f"that becomes false."
                )
            print(self._format_print(self._evaluate(stmt.expr)))
            return

        if isinstance(stmt, BlockStmt):
            for inner in stmt.statements:
                self._execute(inner)
            return

        if isinstance(stmt, IfStmt):
            condition = self._evaluate(stmt.condition)
            if not isinstance(condition, bool):
                raise RuntimeError_(
                    f"Type error: if condition must be boolean, got {type(condition).__name__}"
                )
            if condition:
                self._execute(stmt.then_branch)
            elif stmt.else_branch is not None:
                self._execute(stmt.else_branch)
            return

        if isinstance(stmt, WhileStmt):
            iterations = 0
            while True:
                condition = self._evaluate(stmt.condition)
                if not isinstance(condition, bool):
                    raise RuntimeError_(
                        f"Type error: while condition must be boolean, got {type(condition).__name__}"
                    )
                if not condition:
                    break
                iterations += 1
                self._check_loop_limit("while", iterations)
                self._execute(stmt.body)
            return

        if isinstance(stmt, DoWhileStmt):
            iterations = 0
            while True:
                iterations += 1
                self._check_loop_limit("do-while", iterations)
                self._execute(stmt.body)
                condition = self._evaluate(stmt.condition)
                if not isinstance(condition, bool):
                    raise RuntimeError_(
                        f"Type error: do-while condition must be boolean, got {type(condition).__name__}"
                    )
                if not condition:
                    break
            return

        if isinstance(stmt, ForStmt):
            if stmt.initializer is not None:
                self._execute(stmt.initializer)
            iterations = 0
            while True:
                if stmt.condition is not None:
                    condition = self._evaluate(stmt.condition)
                    if not isinstance(condition, bool):
                        raise RuntimeError_(
                            f"Type error: for condition must be boolean, got {type(condition).__name__}"
                        )
                    if not condition:
                        break
                iterations += 1
                self._check_loop_limit("for", iterations)
                self._execute(stmt.body)
                if stmt.update is not None:
                    self._evaluate(stmt.update)
            return

        raise RuntimeError_(f"Unknown statement type: {stmt}")

    def _format_print(self, value: Any) -> Any:
        if isinstance(value, list):
            return "[" + ", ".join(str(v) for v in value) + "]"
        return value

    def _element_type(self, array_type: str) -> str:
        if array_type.endswith("[]"):
            return array_type[:-2]
        raise RuntimeError_(f"Type error: '{array_type}' is not an array type")

    def _coerce_and_check(self, datatype: str, name: str, value: Any) -> Any:
        """Validate (and lightly coerce) a value against the declared data type."""
        if datatype.endswith("[]"):
            elem = self._element_type(datatype)
            if not isinstance(value, list):
                raise RuntimeError_(
                    f"Type error: cannot assign {type(value).__name__} value to '{datatype} {name}'"
                )
            return [self._coerce_and_check(elem, f"{name}[]", item) for item in value]

        if datatype == "int":
            if isinstance(value, float) and value == int(value):
                return int(value)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
            raise RuntimeError_(
                f"Type error: cannot assign {type(value).__name__} value to 'int {name}'"
            )

        if datatype == "double":
            if isinstance(value, bool):
                raise RuntimeError_(
                    f"Type error: cannot assign {type(value).__name__} value to 'double {name}'"
                )
            if isinstance(value, (int, float)):
                return float(value)
            raise RuntimeError_(
                f"Type error: cannot assign {type(value).__name__} value to 'double {name}'"
            )

        if datatype == "string":
            if isinstance(value, str):
                return value
            raise RuntimeError_(
                f"Type error: cannot assign {type(value).__name__} value to 'string {name}'"
            )

        if datatype == "boolean":
            if isinstance(value, bool):
                return value
            raise RuntimeError_(
                f"Type error: cannot assign {type(value).__name__} value to 'boolean {name}'"
            )

        raise RuntimeError_(f"Unknown data type '{datatype}'")

    def _is_number(self, value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _assign(self, target: Expr, value_expr: Expr) -> Any:
        value = self._evaluate(value_expr)
        if isinstance(target, Variable):
            if target.name not in self.env:
                raise RuntimeError_(f"Undefined variable '{target.name}'")
            datatype = self.types[target.name]
            coerced = self._coerce_and_check(datatype, target.name, value)
            self.env[target.name] = coerced
            return coerced

        if isinstance(target, IndexExpr):
            array = self._evaluate(target.array)
            index = self._evaluate(target.index)
            if not isinstance(array, list):
                raise RuntimeError_(
                    f"Type error: cannot index into {type(array).__name__}"
                )
            if not (isinstance(index, int) and not isinstance(index, bool)):
                if isinstance(index, float) and index == int(index):
                    index = int(index)
                else:
                    raise RuntimeError_(
                        f"Type error: array index must be an integer, got {type(index).__name__}"
                    )
            if index < 0 or index >= len(array):
                raise RuntimeError_(
                    f"Index error: index {index} out of range for array of length {len(array)}"
                )
            # Infer element type from the root variable when possible
            elem_type = "double"
            if isinstance(target.array, Variable) and target.array.name in self.types:
                declared = self.types[target.array.name]
                if declared.endswith("[]"):
                    elem_type = declared[:-2]
            coerced = self._coerce_and_check(elem_type, "element", value)
            array[index] = coerced
            return coerced

        raise RuntimeError_("Type error: invalid assignment target")

    def _apply_update(self, target: Expr, op_type: str, *, prefix: bool) -> Any:
        if isinstance(target, Variable):
            if target.name not in self.env:
                raise RuntimeError_(f"Undefined variable '{target.name}'")
            current = self.env[target.name]
            datatype = self.types[target.name]
            if datatype.endswith("[]") or not self._is_number(current):
                raise RuntimeError_(
                    f"Type error: cannot apply '{ '++' if op_type == TokenType.PLUSPLUS else '--' }' "
                    f"to '{datatype} {target.name}'"
                )
            delta = 1 if op_type == TokenType.PLUSPLUS else -1
            new_value = current + delta
            if datatype == "int":
                new_value = int(new_value)
            else:
                new_value = float(new_value)
            self.env[target.name] = new_value
            return new_value if prefix else current

        if isinstance(target, IndexExpr):
            array = self._evaluate(target.array)
            index = self._evaluate(target.index)
            if not isinstance(array, list):
                raise RuntimeError_(
                    f"Type error: cannot index into {type(array).__name__}"
                )
            if isinstance(index, float) and index == int(index):
                index = int(index)
            if not (isinstance(index, int) and not isinstance(index, bool)):
                raise RuntimeError_(
                    f"Type error: array index must be an integer, got {type(index).__name__}"
                )
            if index < 0 or index >= len(array):
                raise RuntimeError_(
                    f"Index error: index {index} out of range for array of length {len(array)}"
                )
            current = array[index]
            if not self._is_number(current):
                raise RuntimeError_(
                    f"Type error: cannot apply increment/decrement to {type(current).__name__} array element"
                )
            delta = 1 if op_type == TokenType.PLUSPLUS else -1
            new_value = current + delta
            if isinstance(current, int) and not isinstance(current, bool):
                new_value = int(new_value)
            array[index] = new_value
            return new_value if prefix else current

        raise RuntimeError_("Type error: invalid increment/decrement target")

    def _evaluate(self, expr: Expr) -> Any:
        if isinstance(expr, NumberLiteral):
            return expr.value
        if isinstance(expr, StringLiteral):
            return expr.value
        if isinstance(expr, BoolLiteral):
            return expr.value
        if isinstance(expr, Variable):
            if expr.name not in self.env:
                raise RuntimeError_(f"Undefined variable '{expr.name}'")
            return self.env[expr.name]

        if isinstance(expr, ArrayLiteral):
            return [self._evaluate(el) for el in expr.elements]

        if isinstance(expr, IndexExpr):
            array = self._evaluate(expr.array)
            index = self._evaluate(expr.index)
            if not isinstance(array, list):
                raise RuntimeError_(
                    f"Type error: cannot index into {type(array).__name__}"
                )
            if isinstance(index, float) and index == int(index):
                index = int(index)
            if not (isinstance(index, int) and not isinstance(index, bool)):
                raise RuntimeError_(
                    f"Type error: array index must be an integer, got {type(index).__name__}"
                )
            if index < 0 or index >= len(array):
                raise RuntimeError_(
                    f"Index error: index {index} out of range for array of length {len(array)}"
                )
            return array[index]

        if isinstance(expr, AssignExpr):
            return self._assign(expr.target, expr.value)

        if isinstance(expr, UpdateExpr):
            return self._apply_update(expr.target, expr.op.type, prefix=expr.prefix)

        if isinstance(expr, UnaryExpr):
            right = self._evaluate(expr.right)
            if expr.op.type == TokenType.BANG:
                if not isinstance(right, bool):
                    raise RuntimeError_(
                        f"Type error: cannot apply '!' to {type(right).__name__}"
                    )
                return not right
            raise RuntimeError_(f"Unknown unary operator {expr.op.lexeme!r}")

        if isinstance(expr, BinaryExpr):
            op_type = expr.op.type

            if op_type == TokenType.OROR:
                left = self._evaluate(expr.left)
                if not isinstance(left, bool):
                    raise RuntimeError_(
                        f"Type error: cannot apply '||' to {type(left).__name__}"
                    )
                if left:
                    return True
                right = self._evaluate(expr.right)
                if not isinstance(right, bool):
                    raise RuntimeError_(
                        f"Type error: cannot apply '||' to {type(right).__name__}"
                    )
                return right

            if op_type == TokenType.ANDAND:
                left = self._evaluate(expr.left)
                if not isinstance(left, bool):
                    raise RuntimeError_(
                        f"Type error: cannot apply '&&' to {type(left).__name__}"
                    )
                if not left:
                    return False
                right = self._evaluate(expr.right)
                if not isinstance(right, bool):
                    raise RuntimeError_(
                        f"Type error: cannot apply '&&' to {type(right).__name__}"
                    )
                return right

            left = self._evaluate(expr.left)
            right = self._evaluate(expr.right)

            if op_type == TokenType.PLUS:
                if self._is_number(left) and self._is_number(right):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise RuntimeError_(
                    f"Type error: cannot apply '+' to {type(left).__name__} and {type(right).__name__}"
                )

            if op_type in (TokenType.MINUS, TokenType.STAR, TokenType.SLASH):
                if not (self._is_number(left) and self._is_number(right)):
                    raise RuntimeError_(
                        f"Type error: cannot apply {expr.op.lexeme!r} to {type(left).__name__} and {type(right).__name__}"
                    )
                if op_type == TokenType.MINUS:
                    return left - right
                if op_type == TokenType.STAR:
                    return left * right
                if right == 0:
                    raise RuntimeError_("Division by zero")
                return left / right

            if op_type in (
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
            ):
                if not (self._is_number(left) and self._is_number(right)):
                    raise RuntimeError_(
                        f"Type error: cannot apply {expr.op.lexeme!r} to {type(left).__name__} and {type(right).__name__}"
                    )
                if op_type == TokenType.GREATER:
                    return left > right
                if op_type == TokenType.GREATER_EQUAL:
                    return left >= right
                if op_type == TokenType.LESS:
                    return left < right
                return left <= right

            if op_type in (TokenType.EQEQ, TokenType.BANG_EQUAL):
                equal = left == right and type(left) is type(right)
                if self._is_number(left) and self._is_number(right):
                    equal = left == right
                if op_type == TokenType.EQEQ:
                    return equal
                return not equal

            raise RuntimeError_(f"Unknown operator {expr.op.lexeme!r}")

        raise RuntimeError_(f"Unknown expression type: {expr}")
