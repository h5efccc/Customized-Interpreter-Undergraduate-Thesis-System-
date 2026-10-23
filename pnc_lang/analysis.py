from __future__ import annotations

import io
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

from .automaton import AutomatonTrace, build_automaton_trace
from .diagnostics import (
    Diagnostic,
    format_diagnostic_report,
    parse_line_column,
    sort_diagnostics,
)
from .interpreter import MAX_OUTPUT_CHARS, Interpreter, RuntimeError_
from .lexer import Lexer, tip_for_lexical_error
from .parser import Parser
from .tokens import Token, TokenType


def _cap_output(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    omitted = len(text) - MAX_OUTPUT_CHARS
    return (
        text[:MAX_OUTPUT_CHARS]
        + f"\n... [output truncated — {omitted:,} more character(s) omitted]\n"
    )


def _ensure_diagnostic(
    diagnostics: list[Diagnostic],
    *,
    stage: str,
    message: str,
    tip: str,
) -> list[Diagnostic]:
    """Append a fallback diagnostic when a stage failed but the list is empty."""
    if any(d.stage == stage and d.message == message for d in diagnostics):
        return diagnostics
    line, column = parse_line_column(message)
    diagnostics.append(
        Diagnostic(stage=stage, message=message, tip=tip, line=line, column=column)
    )
    return diagnostics


@dataclass
class AnalysisResult:
    source: str
    source_path: str | None = None
    tokens: list[Token] = field(default_factory=list)
    statements: list = field(default_factory=list)
    automaton: AutomatonTrace | None = None
    token_count: int = 0
    statement_count: int = 0
    syntax_valid: bool = False
    lexical_error: str | None = None
    lexical_tip: str | None = None
    syntax_error: str | None = None
    syntax_tip: str | None = None
    # Full multi-error list (line order). Diagrams still use first-error fields above.
    diagnostics: list[Diagnostic] = field(default_factory=list)
    execution_output: str | None = None
    execution_error: str | None = None
    execution_ok: bool | None = None

    @property
    def failed_stage(self) -> int:
        if self.lexical_error:
            return 2
        if self.syntax_error:
            return 3
        return 4

    @property
    def error_count(self) -> int:
        return len(self.diagnostics)

    def format_diagnostics(self) -> str:
        return format_diagnostic_report(self.diagnostics)


def analyze_source(source: str, *, run_execution: bool = False) -> AnalysisResult:
    result = AnalysisResult(source=source)

    # FA / token-table path: halt at the first lexical dead state (unchanged pedagogy).
    trace = build_automaton_trace(source)
    result.automaton = trace
    result.tokens = list(trace.tokens)
    result.token_count = sum(1 for t in result.tokens if t.type != TokenType.EOF)

    # Resilient full-source scan: recover past bad lexemes so later syntax issues
    # can still be reported in the multi-error list.
    resilient_tokens, lexical_diagnostics = Lexer(source).tokenize_collecting_errors()
    syntax_diagnostics = Parser(resilient_tokens).parse_collecting_errors()
    result.diagnostics = sort_diagnostics(lexical_diagnostics + syntax_diagnostics)

    if trace.error:
        result.lexical_error = trace.error
        result.lexical_tip = trace.tip
        result.diagnostics = sort_diagnostics(
            _ensure_diagnostic(
                list(result.diagnostics),
                stage="lexical",
                message=trace.error,
                tip=trace.tip or tip_for_lexical_error(trace.error),
            )
        )
        # Surface the first syntax finding too (for Summary), even though AST is skipped.
        first_syntax = next((d for d in result.diagnostics if d.stage == "syntax"), None)
        if first_syntax is not None:
            result.syntax_error = first_syntax.message
            result.syntax_tip = first_syntax.tip
        result.syntax_valid = False
        return result

    # AST / diagram path: halt at the first syntax error (unchanged pedagogy).
    outcome = Parser(result.tokens).parse_with_recovery()
    result.statements = outcome.statements
    result.statement_count = len(outcome.statements)

    if outcome.error:
        result.syntax_error = outcome.error
        result.syntax_tip = outcome.tip
        result.syntax_valid = False
        result.diagnostics = sort_diagnostics(
            _ensure_diagnostic(
                list(result.diagnostics),
                stage="syntax",
                message=outcome.error,
                tip=outcome.tip
                or "Fix the syntax problem at the reported location, then run Analyze again.",
            )
        )
        return result

    result.syntax_valid = True

    if run_execution:
        buffer = io.StringIO()
        try:
            with redirect_stdout(buffer):
                Interpreter().run(result.statements)
            result.execution_output = _cap_output(buffer.getvalue())
            result.execution_ok = True
        except RuntimeError_ as e:
            result.execution_output = _cap_output(buffer.getvalue())
            result.execution_error = str(e)
            result.execution_ok = False

    return result


def analyze_file(path_str: str, *, run_execution: bool = False) -> AnalysisResult:
    path = Path(path_str)
    source = path.read_text(encoding="utf-8")
    result = analyze_source(source, run_execution=run_execution)
    result.source_path = str(path)
    return result
