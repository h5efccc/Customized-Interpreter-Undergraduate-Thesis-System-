from __future__ import annotations

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
    IncompleteExpr,
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
from .tokens import Token, TokenType


STAGE_WIDTH = 62


def stage_banner(title: str, stage_num: int, total: int) -> str:
    label = f" STAGE {stage_num}/{total}: {title} "
    pad = max(0, STAGE_WIDTH - len(label) - 2)
    left = pad // 2
    right = pad - left
    return f"\n{'=' * left}{label}{'=' * right}\n"


def format_source(source: str) -> str:
    lines = source.splitlines()
    width = max(len(str(len(lines))), 2)
    numbered = []
    for i, line in enumerate(lines, start=1):
        numbered.append(f"  {i:>{width}} | {line}")
    return "\n".join(numbered)


def format_token_table(tokens: list[Token]) -> str:
    display_tokens = [t for t in tokens if t.type != TokenType.EOF]
    if not display_tokens:
        return "  (no tokens produced)\n"

    rows: list[tuple[str, str, str, str, str]] = []
    for i, token in enumerate(display_tokens, start=1):
        value = "" if token.value is None else repr(token.value)
        rows.append((str(i), token.type, token.lexeme, value, str(token.line)))

    headers = ("#", "Token Type", "Lexeme", "Value", "Line")
    widths = [len(h) for h in headers]
    for row in rows:
        for col, cell in enumerate(row):
            widths[col] = max(widths[col], len(cell))

    def fmt_row(cells: tuple[str, ...]) -> str:
        return "  " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    divider = "  " + "-+-".join("-" * w for w in widths)
    lines = [fmt_row(headers), divider]
    lines.extend(fmt_row(row) for row in rows)
    return "\n".join(lines) + "\n"


def format_token_stream(tokens: list[Token]) -> str:
    meaningful = [t for t in tokens if t.type != TokenType.EOF]
    if not meaningful:
        return "  (empty stream)\n"
    parts = [f"[{t.type}: {t.lexeme!r}]" for t in meaningful]
    return "  " + " -> ".join(parts) + "\n"


def format_ast_tree(statements: list[Stmt]) -> str:
    if not statements:
        return "  (empty program)\n"

    lines: list[str] = ["  Program"]
    for i, stmt in enumerate(statements):
        is_last = i == len(statements) - 1
        _append_stmt(lines, stmt, prefix="", is_last=is_last)
    return "\n".join(lines) + "\n"


def _append_stmt(lines: list[str], stmt: Stmt, prefix: str, is_last: bool) -> None:
    branch = "+-- " if is_last else "|-- "
    child_prefix = prefix + ("    " if is_last else "|   ")

    if isinstance(stmt, VarDeclStmt):
        lines.append(f"{prefix}{branch}VarDeclStmt: {stmt.datatype} {stmt.name}")
        _append_expr(lines, stmt.value, child_prefix, is_last=True)
        return

    if isinstance(stmt, AssignStmt):
        lines.append(f"{prefix}{branch}AssignStmt")
        _append_expr(lines, stmt.target, child_prefix, is_last=False)
        _append_expr(lines, stmt.value, child_prefix, is_last=True)
        return

    if isinstance(stmt, ExprStmt):
        lines.append(f"{prefix}{branch}ExprStmt")
        _append_expr(lines, stmt.expr, child_prefix, is_last=True)
        return

    if isinstance(stmt, PrintStmt):
        lines.append(f"{prefix}{branch}PrintStmt")
        _append_expr(lines, stmt.expr, child_prefix, is_last=True)
        return

    if isinstance(stmt, BlockStmt):
        lines.append(f"{prefix}{branch}BlockStmt")
        for i, inner in enumerate(stmt.statements):
            _append_stmt(lines, inner, child_prefix, is_last=(i == len(stmt.statements) - 1))
        return

    if isinstance(stmt, IfStmt):
        lines.append(f"{prefix}{branch}IfStmt")
        _append_expr(lines, stmt.condition, child_prefix, is_last=False)
        has_else = stmt.else_branch is not None
        _append_stmt(lines, stmt.then_branch, child_prefix, is_last=not has_else)
        if has_else and stmt.else_branch is not None:
            _append_stmt(lines, stmt.else_branch, child_prefix, is_last=True)
        return

    if isinstance(stmt, WhileStmt):
        lines.append(f"{prefix}{branch}WhileStmt")
        _append_expr(lines, stmt.condition, child_prefix, is_last=False)
        _append_stmt(lines, stmt.body, child_prefix, is_last=True)
        return

    if isinstance(stmt, DoWhileStmt):
        lines.append(f"{prefix}{branch}DoWhileStmt")
        _append_stmt(lines, stmt.body, child_prefix, is_last=False)
        _append_expr(lines, stmt.condition, child_prefix, is_last=True)
        return

    if isinstance(stmt, ForStmt):
        lines.append(f"{prefix}{branch}ForStmt")
        parts: list[tuple[str, object]] = []
        if stmt.initializer is not None:
            parts.append(("init", stmt.initializer))
        if stmt.condition is not None:
            parts.append(("cond", stmt.condition))
        if stmt.update is not None:
            parts.append(("update", stmt.update))
        parts.append(("body", stmt.body))
        for i, (label, node) in enumerate(parts):
            last = i == len(parts) - 1
            if isinstance(node, Stmt):
                _append_stmt(lines, node, child_prefix, is_last=last)
            else:
                _append_expr(lines, node, child_prefix, is_last=last)  # type: ignore[arg-type]
        return

    lines.append(f"{prefix}{branch}{type(stmt).__name__}")


def _append_expr(lines: list[str], expr: Expr, prefix: str, is_last: bool) -> None:
    branch = "+-- " if is_last else "|-- "
    child_prefix = prefix + ("    " if is_last else "|   ")

    if isinstance(expr, NumberLiteral):
        lines.append(f"{prefix}{branch}NumberLiteral: {expr.value}")
        return
    if isinstance(expr, StringLiteral):
        lines.append(f"{prefix}{branch}StringLiteral: {expr.value!r}")
        return
    if isinstance(expr, BoolLiteral):
        lines.append(f"{prefix}{branch}BoolLiteral: {expr.value}")
        return
    if isinstance(expr, Variable):
        lines.append(f"{prefix}{branch}Variable: {expr.name}")
        return
    if isinstance(expr, IncompleteExpr):
        lines.append(f"{prefix}{branch}IncompleteExpr: {expr.placeholder}")
        return
    if isinstance(expr, ArrayLiteral):
        lines.append(f"{prefix}{branch}ArrayLiteral")
        for i, el in enumerate(expr.elements):
            _append_expr(lines, el, child_prefix, is_last=(i == len(expr.elements) - 1))
        return
    if isinstance(expr, IndexExpr):
        lines.append(f"{prefix}{branch}IndexExpr")
        _append_expr(lines, expr.array, child_prefix, is_last=False)
        _append_expr(lines, expr.index, child_prefix, is_last=True)
        return
    if isinstance(expr, AssignExpr):
        lines.append(f"{prefix}{branch}AssignExpr")
        _append_expr(lines, expr.target, child_prefix, is_last=False)
        _append_expr(lines, expr.value, child_prefix, is_last=True)
        return
    if isinstance(expr, UpdateExpr):
        kind = "prefix" if expr.prefix else "postfix"
        lines.append(f"{prefix}{branch}UpdateExpr ({kind} {expr.op.lexeme})")
        _append_expr(lines, expr.target, child_prefix, is_last=True)
        return
    if isinstance(expr, UnaryExpr):
        lines.append(f"{prefix}{branch}UnaryExpr ({expr.op.lexeme})")
        _append_expr(lines, expr.right, child_prefix, is_last=True)
        return
    if isinstance(expr, BinaryExpr):
        lines.append(f"{prefix}{branch}BinaryExpr ({expr.op.lexeme})")
        _append_expr(lines, expr.left, child_prefix, is_last=False)
        _append_expr(lines, expr.right, child_prefix, is_last=True)
        return

    lines.append(f"{prefix}{branch}{type(expr).__name__}")


def format_pipeline_summary(
    token_count: int,
    statement_count: int,
    syntax_valid: bool,
    executed: bool,
    execution_ok: bool | None = None,
) -> str:
    lines = [
        "  Pipeline Summary",
        "  ----------------",
        f"  Tokens produced (excluding EOF): {token_count}",
        f"  Statements parsed:                     {statement_count}",
        f"  Syntax validation:                     {'PASSED' if syntax_valid else 'FAILED'}",
    ]
    if executed:
        status = "PASSED" if execution_ok else "FAILED"
        lines.append(f"  Optional execution:                    {status}")
    else:
        lines.append("  Optional execution:                    SKIPPED")
    return "\n".join(lines) + "\n"


def format_transformation_flow() -> str:
    return (
        "  Source Code  -->  [ Lexer / Scanner ]  -->  Token Stream\n"
        "                         |\n"
        "                         v\n"
        "                   [ Parser ]  -->  Syntax Validation + AST\n"
        "                         |\n"
        "                         v\n"
        "              [ Visual Feedback Layer ]  -->  Educational Output\n"
    )
