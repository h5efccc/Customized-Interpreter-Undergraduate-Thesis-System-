from __future__ import annotations

from pathlib import Path

from .analysis import analyze_file, analyze_source
from .visualizer import (
    format_ast_tree,
    format_pipeline_summary,
    format_source,
    format_token_stream,
    format_token_table,
    format_transformation_flow,
    stage_banner,
)

TOTAL_STAGES = 4


def run_source(source: str, *, run_execution: bool = False) -> int:
    """Run the CLI simulation on source text."""
    print("VCSS Language Analysis Simulator")
    print("Scanner-Parser Architecture Demonstration")
    print(format_transformation_flow())

    print(stage_banner("SOURCE INPUT", 1, TOTAL_STAGES))
    print(format_source(source))

    print(stage_banner("LEXICAL ANALYSIS (Scanner)", 2, TOTAL_STAGES))
    print("The lexer scans the source character-by-character and emits tokens.\n")

    result = analyze_source(source, run_execution=run_execution)

    if result.lexical_error:
        print(f"Lexical error: {result.lexical_error}")
        if result.lexical_tip:
            print(f"  Tip: {result.lexical_tip}")
        print()
        if result.diagnostics:
            print("All errors (lexical + syntax), ordered by line number.")
            print("Token table / FA / AST still stop at the first pipeline failure.")
            print()
            print(result.format_diagnostics())
            print()
        if result.tokens:
            print("Partial Token Table (before dead state):")
            print(format_token_table(result.tokens))
            print("Partial Token Stream:")
            print(format_token_stream(result.tokens))
        if result.automaton and result.automaton.has_dead_state:
            print("FA simulation ended in DEAD state.\n")
        print(format_pipeline_summary(
            result.token_count, 0, syntax_valid=False, executed=False,
        ))
        return 1

    print("Token Table:")
    print(format_token_table(result.tokens))
    print("Token Stream (left-to-right):")
    print(format_token_stream(result.tokens))

    print(stage_banner("SYNTAX ANALYSIS (Parser) + AST CONSTRUCTION", 3, TOTAL_STAGES))
    print("The parser validates tokens against the context-free grammar (see GRAMMAR.md)")
    print("and builds an Abstract Syntax Tree (AST).\n")

    if result.syntax_error:
        print("Syntax validation: FAILED")
        print(f"  {result.syntax_error}")
        if result.syntax_tip:
            print(f"  Tip: {result.syntax_tip}")
        print()
        if result.diagnostics:
            print(result.format_diagnostics())
            print()
        if result.statements:
            print("Partial Abstract Syntax Tree (recovered before the error):")
            print(format_ast_tree(result.statements))
        else:
            print("No AST nodes could be recovered before the error.\n")
        print(format_pipeline_summary(
            result.token_count,
            result.statement_count,
            syntax_valid=False,
            executed=False,
        ))
        return 1

    print("Syntax validation: PASSED\n")
    print("Abstract Syntax Tree:")
    print(format_ast_tree(result.statements))

    print(stage_banner("VISUAL FEEDBACK SUMMARY", 4, TOTAL_STAGES))
    if run_execution:
        print("Optional execution phase enabled.\n")
        if result.execution_output:
            print(result.execution_output, end="" if result.execution_output.endswith("\n") else "\n")
        if result.execution_ok:
            print("\nExecution completed without runtime errors.")
        else:
            print(f"\nRuntime error during optional execution: {result.execution_error}")
    else:
        print(
            "This simulator focuses on lexical and syntax analysis.\n"
            "Execution is optional. Re-run with --execute to simulate runtime.\n"
        )

    print(format_pipeline_summary(
        result.token_count,
        result.statement_count,
        syntax_valid=True,
        executed=run_execution,
        execution_ok=result.execution_ok,
    ))
    return 0 if (not run_execution or result.execution_ok) else 1


def run_file(path_str: str, *, run_execution: bool = False) -> int:
    """Run the CLI simulation on a .pnc source file."""
    path = Path(path_str)
    if path.suffix.lower() != ".pnc":
        print(f"Error: expected a .pnc file, got {path.suffix!r}")
        return 2

    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        return 2

    return run_source(source, run_execution=run_execution)
