from __future__ import annotations
from pathlib import Path
from .interpreter import Interpreter, RuntimeError_
from .lexer import Lexer, LexerError
from .parser import ParseError, Parser


def run_file(path_str: str) -> int:
    path = Path(path_str)
    if path.suffix.lower() != ".pnc":
        print(f"Error: expected a .pnc file, got {path.suffix}")
        return 2

    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        return 2

    print("=== SOURCE CODE ===")
    print(source)

    print("\n=== LEXICAL ANALYSIS (TOKENS) ===")
    try:
        tokens = Lexer(source).tokenize()
        for t in tokens:
            print(t)
    except LexerError as e:
        print(f"Lexical error: {e}")
        return 1

    print("\n=== SYNTAX ANALYSIS ===")
    try:
        statements = Parser(tokens).parse()
        print("Syntax: VALID")
    except ParseError as e:
        print(f"Syntax error: {e}")
        return 1

    print("\n=== EXECUTION ===")
    try:
        Interpreter().run(statements)
        print("\nProgram finished successfully.")
        return 0
    except RuntimeError_ as e:
        print(f"Runtime error: {e}")
        return 1

