# PNC Language Analysis Simulator

An **instructional simulation tool** for demonstrating **lexical analysis** and **syntax analysis** using the PNC educational language (`.pnc` files).

Following panel recommendations, this system focuses on the **scanner–parser architecture**: a lexer converts source code into tokens, a parser validates those tokens against a context-free grammar and builds an Abstract Syntax Tree (AST), and a visual feedback layer presents each stage transparently for learners.

> This is **not** a general-purpose interpreter. Execution is available as an optional secondary phase.

## What it demonstrates

| Stage | Component | Output |
|-------|-----------|--------|
| Source input | — | Numbered source listing |
| Lexical analysis | `pnc_lang/lexer.py` | Token table + token stream |
| Syntax analysis | `pnc_lang/parser.py` | Validation result + AST tree |
| Visual feedback | `pnc_lang/visualizer.py` | Pipeline summary |

## Project structure

```
pnc_lang/
  tokens.py        Token definitions
  lexer.py         Lexical analyzer (scanner)
  parser.py        Syntax analyzer (parser)
  ast_nodes.py     AST node definitions
  visualizer.py    Educational output formatting (CLI)
  analysis.py      Shared analysis engine (lexer + parser + optional execution)
  gui.py           Graphical simulator interface
  runner.py        CLI simulation pipeline
  interpreter.py   Optional execution (secondary)
web/
  app.py           FastAPI web API + static file hosting
  static/          Plain HTML/CSS/JS front-end
edu_interpreter.py CLI entry point
GRAMMAR.md         Complete CFG specification
SYNTAX_NOTES.md    Syntax templates and quick-start guide
DEVELOPER_GUIDE.md Extension and modification guide
requirements-web.txt  Dependencies for the web app
examples/          Sample .pnc programs
```

## Supported language features

- Typed variable declaration (`int`, `double`, `string`, `boolean`)
- One-dimensional arrays (`int[] a = {1, 2, 3};`, indexing `a[i]`)
- Statements end with semicolons (Java-inspired)
- Print output (`print(...);`)
- Numbers, strings, booleans (`true` / `false`), identifiers
- Arithmetic: `+`, `-`, `*`, `/`
- Increment / decrement: `++`, `--` (prefix and postfix, on variables or array elements)
- Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Logical: `!`, `&&`, `||`
- Java-style `if` / `else` / `else if` with curly braces `{ }`
- Loops: `while`, `do` / `while`, and `for` (all require `{ }` bodies)
- Java-style comments: `//` and `/* */`
- String concatenation (`+` on strings)
- Operator precedence and parentheses
- Lexical and syntax error reporting with tips (misspellings, bad identifiers, missing `;`, empty conditions, etc.)
- Runtime safety limits on loops / `print` floods so infinite programs stop cleanly instead of freezing the GUI

## Intentionally unsupported

- Functions and OOP
- Multi-dimensional arrays (`int[][]`)
- `break` / `continue`
- See `GRAMMAR.md` for the full specification

## Example programs

File: `examples/hello.pnc`

```text
int a = 5;
int b = 10;
print(a + b);
print("Hello World");
```

File: `examples/loops_arrays.pnc` — `while` / `do-while` / `for`, arrays, and `++` / `--`.
## How to run

### GUI (recommended)

Double-click is not set up — use one of these:

```powershell
# Opens the simulator window (with a sample program pre-loaded)
python .\edu_interpreter.py

# Opens the GUI with a specific file loaded
python .\edu_interpreter.py .\examples\hello.pnc
```

In the GUI:
1. Edit code in the **Source Code** panel (or click **Open .pnc File**)
2. Click **Analyze** to see tokens, AST, and summary in the tabs
3. Click **Analyze + Execute** to also run the optional execution phase

### VS Code / Cursor

Select **Run PNC Simulator (GUI)** in the Run dropdown, open a `.pnc` file, and click **Run**.

Use **Run PNC Simulator (CLI)** if you still want terminal output.

### Terminal (CLI mode)

```powershell
python .\edu_interpreter.py --cli .\examples\hello.pnc
python .\edu_interpreter.py --cli --execute .\examples\CSD11.pnc
```

### Web app (FastAPI + plain HTML)

```powershell
pip install -r .\requirements-web.txt
python -m uvicorn web.app:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). The page calls `POST /api/analyze` and reuses the same `analyze_source` engine as the desktop GUI.

To host online later: deploy this app on Render, Railway, or Fly.io (run `uvicorn web.app:app --host 0.0.0.0 --port $PORT`).

## Documentation

- **[SYNTAX_NOTES.md](SYNTAX_NOTES.md)** — How to write PNC programs (templates & examples)
- **[GRAMMAR.md](GRAMMAR.md)** — Context-free grammar specification
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** — Architecture and extension guide
- **`web/`** — Browser front-end (FastAPI + static HTML)
