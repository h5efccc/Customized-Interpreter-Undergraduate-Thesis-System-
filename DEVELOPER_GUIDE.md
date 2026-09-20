# PNC Developer Guide

This guide explains the project architecture and how to extend the PNC Language Analysis Simulator.

## Purpose

Following panel recommendations, this system is an **instructional simulation tool** — not a general-purpose programming language runtime. Its primary goal is to demonstrate:

1. **Lexical analysis** — scanning source code into tokens
2. **Syntax analysis** — validating tokens against a CFG and building an AST
3. **Visual feedback** — presenting each stage transparently for learners

Optional execution exists but is secondary. In the GUI, use **Analyze + Execute**. In CLI mode, pass `--cli --execute`.

## Architecture Overview

```
Source (.pnc)
    │
    ▼
┌─────────┐     tokens      ┌─────────┐     AST
│  Lexer  │ ──────────────► │ Parser  │ ────────────┐
│ (scan)  │                 │ (CFG)   │             │
└─────────┘                 └─────────┘             │
                              │                     │
                              ▼                     ▼
                       Interpreter          ┌──────────────┐
                       (optional)           │  analysis.py │
                              │              │ (shared core)│
                              │              └──────┬───────┘
                              │                     │
                              │            ┌────────┴────────┐
                              │            ▼                 ▼
                              │      ┌──────────┐     ┌───────────┐
                              │      │  gui.py  │     │ runner.py │
                              │      │ (primary)│     │   (CLI)   │
                              │      └──────────┘     └─────┬─────┘
                              │            │                 │
                              │            ▼                 ▼
                              │      GUI window       visualizer.py
                              │      (tkinter)        (text output)
                              ▼
                         stdout capture
                         (execution tab / CLI)
```

Both the GUI and CLI paths call the same `analyze_source()` function in `analysis.py`. This keeps lexer/parser behavior identical regardless of how the user runs the simulator.

## Module Reference

| Module | Role |
|--------|------|
| `pnc_lang/tokens.py` | Token type constants and `Token` dataclass |
| `pnc_lang/lexer.py` | Scanner — converts characters to tokens |
| `pnc_lang/parser.py` | Parser — validates syntax, builds AST |
| `pnc_lang/ast_nodes.py` | AST node definitions (`VarDeclStmt`, `BinaryExpr`, etc.) |
| `pnc_lang/analysis.py` | Shared analysis engine — returns `AnalysisResult` |
| `pnc_lang/gui.py` | Graphical simulator (primary interface, tkinter) |
| `pnc_lang/visualizer.py` | Formats educational output for CLI mode |
| `pnc_lang/runner.py` | CLI pipeline orchestrator |
| `pnc_lang/interpreter.py` | Optional runtime (secondary) |
| `edu_interpreter.py` | Main entry point — launches GUI by default |
| `GRAMMAR.md` | Complete CFG specification |
| `SYNTAX_NOTES.md` | Syntax templates for learners |
| `examples/` | Sample `.pnc` programs |

## Entry Points

| Command | What it does |
|---------|--------------|
| `python edu_interpreter.py` | Opens GUI with a sample program |
| `python edu_interpreter.py file.pnc` | Opens GUI with that file loaded |
| `python edu_interpreter.py --cli file.pnc` | Terminal simulation (no GUI) |
| `python edu_interpreter.py --cli --execute file.pnc` | Terminal simulation + execution |

## GUI Layout

The GUI (`pnc_lang/gui.py`) is built with **tkinter** (included with Python — no extra install needed).

| Area | Widget | Purpose |
|------|--------|---------|
| Header | Labels | Title and pipeline flow (Source → Lexer → Parser → AST → Summary) |
| Left panel | `Text` editor | Write or edit `.pnc` source code |
| Tokens tab | `Treeview` + stream text | Token table and left-to-right token stream |
| AST tab | `Treeview` | Expandable abstract syntax tree |
| Summary tab | `Text` | Pipeline summary (token count, validation status) |
| Execution Output tab | `Text` | Captured `print()` output (Analyze + Execute only) |
| Toolbar | Buttons | Open, Analyze, Analyze + Execute, Clear |

Stage indicators in the header turn green as each analysis stage completes.

## Shared Analysis Engine

`pnc_lang/analysis.py` is the core that both GUI and CLI use:

```python
from pnc_lang.analysis import analyze_source

result = analyze_source(source_code, run_execution=False)
# result.tokens          — list of Token objects
# result.statements      — list of AST statement nodes
# result.token_count     — meaningful token count
# result.syntax_valid    — True if parser succeeded
# result.lexical_error   — error message or None
# result.syntax_error    — error message or None
# result.execution_output — captured print output (if run_execution=True)
# result.execution_ok    — True/False/None
```

When adding new language features, update lexer/parser/interpreter first — `analysis.py` picks up the changes automatically. Update `gui.py` and `visualizer.py` only if new AST node types need custom display logic.

## Pipeline Stages

Whether in GUI or CLI, the simulator walks through four stages:

| Stage | What happens | GUI location |
|-------|--------------|--------------|
| 1 — Source Input | User provides `.pnc` code | Left editor panel |
| 2 — Lexical Analysis | Scanner produces tokens | **Tokens** tab |
| 3 — Syntax Analysis | Parser validates grammar, builds AST | **AST** tab |
| 4 — Visual Feedback | Summary of the full pipeline | **Summary** tab |

Optional execution output appears in the **Execution Output** tab (GUI) or at the bottom of CLI output.

## How to Add a New Keyword

Example: adding a `show` keyword as an alias for `print`.

### Step 1 — Lexer (`lexer.py`)

In `_identifier()`, add the word to the reserved keyword set:

```python
if text in ("int", "double", "string", "print", "show"):
    type_ = TokenType.RESERVED_KEYWORD
```

### Step 2 — AST node (`ast_nodes.py`)

Reuse `PrintStmt` or create a new statement node if semantics differ.

### Step 3 — Parser (`parser.py`)

In `_statement()`, add a match branch:

```python
if self._match_keyword("show"):
    return self._print_statement()
```

### Step 4 — Grammar doc (`GRAMMAR.md`)

Document the new production rule.

### Step 5 — Display layers (only if new AST node type)

- **CLI:** update `_append_stmt()` in `visualizer.py`
- **GUI:** update `_insert_stmt()` in `gui.py`

### Step 6 — Execution (optional)

Handle the new statement in `interpreter._execute()` if runtime behavior is needed.

## How to Add a New Operator

Example: adding modulo `%`.

1. Add `PERCENT = "PERCENT"` to `TokenType` in `tokens.py`
2. Handle `%` in `Lexer._scan_token()`
3. Add `%` to the `_term()` loop in `parser.py` (same precedence as `*` and `/`)
4. Handle `TokenType.PERCENT` in `interpreter.py` (if execution is needed)
5. Update `GRAMMAR.md`

No changes to `analysis.py`, `gui.py`, or `visualizer.py` are needed unless the AST structure changes.

## How to Add a New Statement Type

Example: adding `input(x)` for reading user input.

1. Define a new AST node in `ast_nodes.py` (e.g., `InputStmt`)
2. Add a parser method `_input_statement()` in `parser.py`
3. Register it in `_statement()`
4. Add rendering in `visualizer._append_stmt()` (CLI)
5. Add rendering in `gui._insert_stmt()` (GUI)
6. Optionally handle it in `interpreter._execute()`
7. Document in `GRAMMAR.md`

## Running and Testing

```powershell
# GUI (default — recommended)
python .\edu_interpreter.py
python .\edu_interpreter.py .\examples\hello.pnc

# CLI (terminal output)
python .\edu_interpreter.py --cli .\examples\hello.pnc
python .\edu_interpreter.py --cli --execute .\examples\CSD11.pnc
```

### VS Code / Cursor launch configurations

| Configuration | Behavior |
|---------------|----------|
| **Run PNC Simulator (GUI)** | Opens GUI with the active `.pnc` file loaded |
| **Run PNC Simulator (CLI)** | Runs terminal simulation on the active file |

## File Conventions

- Source programs use the `.pnc` extension
- Example programs live in `examples/`
- Grammar rules are authoritative in `GRAMMAR.md`
- The **GUI** is the primary user-facing interface; CLI/visualizer is the secondary path
- Use `analysis.py` for any programmatic access to the pipeline — do not call lexer/parser separately unless testing in isolation

## Design Principles

1. **Transparency over brevity** — show what the lexer and parser are doing
2. **Separation of concerns** — each pipeline phase is its own module
3. **Single analysis core** — GUI and CLI share `analysis.py` so behavior stays consistent
4. **Grammar-first** — parser changes must be reflected in `GRAMMAR.md`
5. **Execution is optional** — the simulator works fully without running code
