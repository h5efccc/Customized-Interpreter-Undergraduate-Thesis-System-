from __future__ import annotations

import io
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

from .automaton import AutomatonTrace, build_automaton_trace
from .interpreter import MAX_OUTPUT_CHARS, Interpreter, RuntimeError_
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


def analyze_source(source: str, *, run_execution: bool = False) -> AnalysisResult:
    result = AnalysisResult(source=source)

    trace = build_automaton_trace(source)
    result.automaton = trace
    result.tokens = list(trace.tokens)
    result.token_count = sum(1 for t in result.tokens if t.type != TokenType.EOF)

    if trace.error:
        result.lexical_error = trace.error
        result.lexical_tip = trace.tip
        return result

    outcome = Parser(result.tokens).parse_with_recovery()
    result.statements = outcome.statements
    result.statement_count = len(outcome.statements)

    if outcome.error:
        result.syntax_error = outcome.error
        result.syntax_tip = outcome.tip
        result.syntax_valid = False
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
