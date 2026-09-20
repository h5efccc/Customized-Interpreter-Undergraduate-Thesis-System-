"""FastAPI web front-end for the PNC Language Analysis Simulator.

Run from the repo root:
    pip install -r requirements-web.txt
    python -m uvicorn web.app:app --reload --host 127.0.0.1 --port 8000

Then open http://127.0.0.1:8000/
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pnc_lang.analysis import AnalysisResult, analyze_source
from pnc_lang.ast_nodes import (
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
from pnc_lang.tokens import Token, TokenType
from pnc_lang.visualizer import format_ast_tree

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_SOURCE_CHARS = 32_000

DEFAULT_SOURCE = """int a = 5;
int b = 10;
print(a + b);
print("Hello World");
"""

app = FastAPI(
    title="PNC Language Analysis Simulator",
    description="Web UI for the educational PNC lexer / parser / optional executor.",
    version="1.0.0",
)


class AnalyzeRequest(BaseModel):
    source: str = Field(..., min_length=0, max_length=MAX_SOURCE_CHARS)
    execute: bool = False


def _token_dict(tok: Token) -> dict[str, Any]:
    return {
        "type": tok.type,
        "lexeme": tok.lexeme,
        "value": tok.value,
        "line": tok.line,
        "column": tok.column,
    }


def _expr_dict(expr: Expr) -> dict[str, Any]:
    if isinstance(expr, NumberLiteral):
        return {"kind": "NumberLiteral", "value": expr.value}
    if isinstance(expr, StringLiteral):
        return {"kind": "StringLiteral", "value": expr.value}
    if isinstance(expr, BoolLiteral):
        return {"kind": "BoolLiteral", "value": expr.value}
    if isinstance(expr, Variable):
        return {"kind": "Variable", "name": expr.name}
    if isinstance(expr, IncompleteExpr):
        return {"kind": "IncompleteExpr", "placeholder": expr.placeholder}
    if isinstance(expr, ArrayLiteral):
        return {
            "kind": "ArrayLiteral",
            "elements": [_expr_dict(e) for e in expr.elements],
        }
    if isinstance(expr, IndexExpr):
        return {
            "kind": "IndexExpr",
            "array": _expr_dict(expr.array),
            "index": _expr_dict(expr.index),
        }
    if isinstance(expr, AssignExpr):
        return {
            "kind": "AssignExpr",
            "target": _expr_dict(expr.target),
            "value": _expr_dict(expr.value),
        }
    if isinstance(expr, UpdateExpr):
        return {
            "kind": "UpdateExpr",
            "op": expr.op.lexeme,
            "prefix": expr.prefix,
            "target": _expr_dict(expr.target),
        }
    if isinstance(expr, UnaryExpr):
        return {
            "kind": "UnaryExpr",
            "op": expr.op.lexeme,
            "right": _expr_dict(expr.right),
        }
    if isinstance(expr, BinaryExpr):
        return {
            "kind": "BinaryExpr",
            "op": expr.op.lexeme,
            "left": _expr_dict(expr.left),
            "right": _expr_dict(expr.right),
        }
    return {"kind": type(expr).__name__}


def _stmt_dict(stmt: Stmt) -> dict[str, Any]:
    if isinstance(stmt, VarDeclStmt):
        return {
            "kind": "VarDeclStmt",
            "datatype": stmt.datatype,
            "name": stmt.name,
            "value": _expr_dict(stmt.value),
        }
    if isinstance(stmt, AssignStmt):
        return {
            "kind": "AssignStmt",
            "target": _expr_dict(stmt.target),
            "value": _expr_dict(stmt.value),
        }
    if isinstance(stmt, ExprStmt):
        return {"kind": "ExprStmt", "expr": _expr_dict(stmt.expr)}
    if isinstance(stmt, PrintStmt):
        return {"kind": "PrintStmt", "expr": _expr_dict(stmt.expr)}
    if isinstance(stmt, BlockStmt):
        return {
            "kind": "BlockStmt",
            "statements": [_stmt_dict(s) for s in stmt.statements],
        }
    if isinstance(stmt, IfStmt):
        return {
            "kind": "IfStmt",
            "condition": _expr_dict(stmt.condition),
            "then_branch": _stmt_dict(stmt.then_branch),
            "else_branch": _stmt_dict(stmt.else_branch) if stmt.else_branch else None,
        }
    if isinstance(stmt, WhileStmt):
        return {
            "kind": "WhileStmt",
            "condition": _expr_dict(stmt.condition),
            "body": _stmt_dict(stmt.body),
        }
    if isinstance(stmt, DoWhileStmt):
        return {
            "kind": "DoWhileStmt",
            "body": _stmt_dict(stmt.body),
            "condition": _expr_dict(stmt.condition),
        }
    if isinstance(stmt, ForStmt):
        return {
            "kind": "ForStmt",
            "initializer": _stmt_dict(stmt.initializer) if stmt.initializer else None,
            "condition": _expr_dict(stmt.condition) if stmt.condition else None,
            "update": _expr_dict(stmt.update) if stmt.update else None,
            "body": _stmt_dict(stmt.body),
        }
    return {"kind": type(stmt).__name__}


def _result_to_json(result: AnalysisResult) -> dict[str, Any]:
    raw_tokens = [t for t in result.tokens if t.type != TokenType.EOF]
    tokens = [_token_dict(t) for t in raw_tokens]
    stream = " ".join(
        (t.lexeme if t.lexeme else f"<{t.type}>") for t in raw_tokens
    )

    automaton: dict[str, Any] | None = None
    if result.automaton is not None:
        automaton = {
            "states": [
                {
                    "id": s.id,
                    "kind": s.kind,
                    "label": s.label,
                    "accept_info": s.accept_info,
                }
                for s in result.automaton.states
            ],
            "transitions": [
                {
                    "from_id": t.from_id,
                    "symbol": t.symbol,
                    "to_id": t.to_id,
                }
                for t in result.automaton.transitions
            ],
            "has_dead_state": result.automaton.has_dead_state,
        }

    ast_tree = ""
    ast_nodes: list[dict[str, Any]] = []
    if result.statements:
        ast_tree = format_ast_tree(result.statements)
        ast_nodes = [_stmt_dict(s) for s in result.statements]

    if result.lexical_error:
        stage = "lexical"
    elif result.syntax_error:
        stage = "syntax"
    elif result.execution_ok is False:
        stage = "execution"
    elif result.execution_ok is True:
        stage = "execution"
    else:
        stage = "syntax" if result.syntax_valid else "idle"

    return {
        "ok": result.lexical_error is None and result.syntax_error is None,
        "stage": stage,
        "token_count": result.token_count,
        "statement_count": result.statement_count,
        "syntax_valid": result.syntax_valid,
        "lexical_error": result.lexical_error,
        "lexical_tip": result.lexical_tip,
        "syntax_error": result.syntax_error,
        "syntax_tip": result.syntax_tip,
        "tokens": tokens,
        "token_stream": stream,
        "automaton": automaton,
        "ast_tree": ast_tree,
        "ast": ast_nodes,
        "execution_ok": result.execution_ok,
        "execution_output": result.execution_output,
        "execution_error": result.execution_error,
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/defaults")
def defaults() -> dict[str, Any]:
    return {
        "source": DEFAULT_SOURCE,
        "max_source_chars": MAX_SOURCE_CHARS,
    }


@app.post("/api/analyze")
def analyze(body: AnalyzeRequest) -> dict[str, Any]:
    source = body.source
    if len(source) > MAX_SOURCE_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Source exceeds {MAX_SOURCE_CHARS:,} character limit.",
        )
    result = analyze_source(source, run_execution=body.execute)
    return _result_to_json(result)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
