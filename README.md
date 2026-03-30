# Educational Interpreter Prototype (PNC)

This is a small demo interpreter for a custom educational language using the file extension **`.pnc`**.

## Example program

File: `examples/hello.pnc`

```text
let a = 5
let b = 10
print(a + b)
print("Hello World")
```

## How to run

From `c:\Thesis System`:

```powershell
python .\edu_interpreter.py .\examples\hello.pnc
```

## What it shows

- **Lexical analysis**: prints the list of tokens
- **Syntax analysis**: prints whether syntax is valid, otherwise a friendly error
- **Execution**: runs `let` assignments and `print(...)`

## Project structure (separated components)

- `pnc_lang/lexer.py`: lexical analysis (tokenization)
- `pnc_lang/parser.py`: syntax analysis (parsing)
- `pnc_lang/interpreter.py`: execution (runtime semantics)
- `pnc_lang/tokens.py`: token definitions
- `pnc_lang/ast_nodes.py`: AST node definitions
- `pnc_lang/runner.py`: runs the pipeline and prints educational output
- `edu_interpreter.py`: small CLI entrypoint that calls the runner

## What our Interpreter can do (at this moment)
- Variable seclaration and store values
- Basic aritmethic operations (like + | - | * | / | = )
- Print outputs

## What our Interpreter can't do (at this moment)
- for/while loops                                                   Should we include this?
- Logical Operations (like > | < | == | != | && | etc... )          Should we include this?
- if statements                                                     Should we include this?

## What our Interpreter will not support
- OOP features
- Anything that is outside of our Scope and Limitations