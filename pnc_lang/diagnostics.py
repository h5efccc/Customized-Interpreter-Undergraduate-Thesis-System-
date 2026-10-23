from __future__ import annotations

import re
from dataclasses import dataclass


_LINE_COL_RE = re.compile(
    r"line\s+(\d+)\s*,\s*column\s+(\d+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Diagnostic:
    """One lexical or syntax problem with an educational fix tip."""

    stage: str  # "lexical" | "syntax"
    message: str
    tip: str
    line: int
    column: int

    @property
    def location(self) -> str:
        return f"line {self.line}, column {self.column}"


def parse_line_column(message: str, *, default_line: int = 1, default_column: int = 1) -> tuple[int, int]:
    """Extract (line, column) from an error message, with fallbacks."""
    match = _LINE_COL_RE.search(message)
    if match:
        return int(match.group(1)), int(match.group(2))
    return default_line, default_column


def sort_diagnostics(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    """Order diagnostics by line, then column, then stage (lexical before syntax)."""
    stage_rank = {"lexical": 0, "syntax": 1}
    return sorted(
        diagnostics,
        key=lambda d: (d.line, d.column, stage_rank.get(d.stage, 9), d.message),
    )


def format_diagnostic_report(diagnostics: list[Diagnostic]) -> str:
    """Human-readable multi-error report ordered by source location."""
    if not diagnostics:
        return ""
    ordered = sort_diagnostics(diagnostics)
    n = len(ordered)
    lines = [
        f"Errors found: {n}",
        "-" * 40,
    ]
    for i, d in enumerate(ordered, start=1):
        stage = "Lexical" if d.stage == "lexical" else "Syntax"
        lines.append(f"{i}. [{stage}] {d.location}")
        lines.append(f"   {d.message}")
        if d.tip:
            lines.append(f"   Suggestion: {d.tip}")
        if i < n:
            lines.append("")
    return "\n".join(lines)
