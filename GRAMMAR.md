# PNC Language Grammar Specification

This document defines the **context-free grammar (CFG)** for the PNC educational language.
The parser in `pnc_lang/parser.py` implements these rules.

PNC uses **Java-inspired syntax**: typed declarations, statements that end with `;`,
`if` / `else` / loops with curly braces, one-dimensional arrays, and Java-style comments.

## Notation

| Symbol | Meaning |
|--------|---------|
| `→`    | Production rule ("produces") |
| `\|`   | Alternative |
| `?`    | Optional (0 or 1 occurrence) |
| `*`    | Zero or more repetitions |
| `"..."` | Terminal token (exact lexeme) |
| `IDENT` | Identifier token |
| `NUMBER` | Numeric literal token |
| `STRING` | String literal token |

## Lexical Rules (Scanner)

The lexer recognizes the following token categories before parsing begins.

### Keywords

| Lexeme | Token Type | Role |
|--------|------------|------|
| `int`  | `Reserved Keyword` | Integer data type |
| `double` | `Reserved Keyword` | Floating-point data type |
| `string` | `Reserved Keyword` | Text data type |
| `boolean` | `Reserved Keyword` | Boolean data type |
| `true` | `Reserved Keyword` | Boolean literal |
| `false` | `Reserved Keyword` | Boolean literal |
| `print`| `Reserved Keyword` | Output statement |
| `if` | `Reserved Keyword` | Conditional |
| `else` | `Reserved Keyword` | Conditional alternative |
| `while` | `Reserved Keyword` | Loop |
| `for` | `Reserved Keyword` | Counted loop |
| `do` | `Reserved Keyword` | Do-while loop |

### Operators and Punctuation

| Lexeme | Token Type |
|--------|------------|
| `+` | `PLUS` |
| `-` | `MINUS` |
| `*` | `STAR` |
| `/` | `SLASH` |
| `++` | `PLUSPLUS` |
| `--` | `MINUSMINUS` |
| `=` | `EQUAL` |
| `!` | `BANG` |
| `==` | `EQEQ` |
| `!=` | `BANG_EQUAL` |
| `<` | `LESS` |
| `<=` | `LESS_EQUAL` |
| `>` | `GREATER` |
| `>=` | `GREATER_EQUAL` |
| `&&` | `ANDAND` |
| `\|\|` | `OROR` |
| `(` | `LPAREN` |
| `)` | `RPAREN` |
| `{` | `LBRACE` |
| `}` | `RBRACE` |
| `[` | `LBRACKET` |
| `]` | `RBRACKET` |
| `,` | `COMMA` |
| `;` | `SEMICOLON` |

### Literals and Identifiers

| Pattern | Token Type | Notes |
|---------|------------|-------|
| `[0-9]+(\.[0-9]+)?` | `NUMBER` | Integer or decimal |
| `"..."` | `STRING` | Double-quoted; no embedded newlines |
| `[A-Za-z_][A-Za-z0-9_]*` | `IDENT` | Variable names |

### Comments

| Form | Handling |
|------|----------|
| `// ...` | Line comment — ignored through end of line |
| `/* ... */` | Block comment — ignored (may span lines) |

### Whitespace

| Character | Handling |
|-----------|----------|
| space, tab, carriage return, newline | Ignored (Java-style; statements end with `;`) |

### End of Input

When all characters are consumed, the lexer emits an `EOF` token.

---

## Context-Free Grammar (Parser)

### Program

```
Program     → Statement*
```

A program is a sequence of zero or more statements.

### Statements

```
Statement   → VarDeclStmt
            | AssignStmt
            | ExprStmt
            | PrintStmt
            | IfStmt
            | WhileStmt
            | DoWhileStmt
            | ForStmt

VarDeclStmt → DataType IDENT EQUAL ( ArrayLiteral | Expression ) SEMICOLON

DataType    → ("int" | "double" | "string" | "boolean") ( LBRACKET RBRACKET )?

ArrayLiteral → LBRACE Expression ( COMMA Expression )* RBRACE

AssignStmt  → LValue EQUAL Expression SEMICOLON

ExprStmt    → UpdateExpr SEMICOLON

PrintStmt   → "print" LPAREN Expression RPAREN SEMICOLON

IfStmt      → "if" LPAREN Expression RPAREN Block
              ( "else" ( IfStmt | Block ) )?

WhileStmt   → "while" LPAREN Expression RPAREN Block

DoWhileStmt → "do" Block "while" LPAREN Expression RPAREN SEMICOLON

ForStmt     → "for" LPAREN ForInit? SEMICOLON Expression? SEMICOLON ForUpdate? RPAREN Block

ForInit     → VarDeclStmtNoSemi | AssignExpr | UpdateExpr

ForUpdate   → AssignExpr | UpdateExpr

Block       → LBRACE Statement* RBRACE

LValue      → IDENT ( LBRACKET Expression RBRACKET )?
```

Variable declarations, assignments, updates, `print`, and `do-while` **must** end with a semicolon.
`if` / `else` / loop bodies **must** be blocks enclosed in `{ }`.
Empty conditions in `if ()`, `while ()`, and `do ... while ()` are syntax errors.

### Expressions (Operator Precedence)

```
Expression  → Assignment

Assignment  → LValue EQUAL Assignment
            | LogicOr

LogicOr     → LogicAnd ( OROR LogicAnd )*

LogicAnd    → Equality ( ANDAND Equality )*

Equality    → Comparison ( ( EQEQ | BANG_EQUAL ) Comparison )*

Comparison  → Term ( ( GREATER | GREATER_EQUAL | LESS | LESS_EQUAL ) Term )*

Term        → Factor ( ( PLUS | MINUS ) Factor )*

Factor      → Unary ( ( STAR | SLASH ) Unary )*

Unary       → ( BANG | PLUSPLUS | MINUSMINUS ) Unary
            | Postfix

Postfix    → Primary ( LBRACKET Expression RBRACKET | PLUSPLUS | MINUSMINUS )*

Primary     → NUMBER
            | STRING
            | "true"
            | "false"
            | IDENT
            | LPAREN Expression RPAREN
```

Precedence (highest to lowest):

1. Parentheses `( ... )`, indexing `[ ... ]`, postfix `++` / `--`
2. Prefix `++` / `--`, logical not (`!`)
3. Multiplication / Division (`*`, `/`)
4. Addition / Subtraction (`+`, `-`)
5. Comparison (`>`, `>=`, `<`, `<=`)
6. Equality (`==`, `!=`)
7. Logical and (`&&`)
8. Logical or (`||`)
9. Assignment (`=`)

All binary operators are **left-associative**. `&&` and `||` short-circuit at runtime.

---

## Example Derivation

Source:

```text
int a = 5;
if (a < 10) {
    print("ok");
}
```

Token stream (simplified):

```
KEYWORD IDENT EQUAL NUMBER SEMICOLON
KEYWORD LPAREN IDENT LESS NUMBER RPAREN
LBRACE KEYWORD LPAREN STRING RPAREN SEMICOLON RBRACE EOF
```

Parse tree (AST):

```
Program
├── VarDeclStmt: int a
│   └── NumberLiteral: 5.0
└── IfStmt
    ├── BinaryExpr (<)
    │   ├── Variable: a
    │   └── NumberLiteral: 10.0
    └── BlockStmt
        └── PrintStmt
            └── StringLiteral: 'ok'
```

---

## Intentionally Unsupported Constructs

The following are **outside the current grammar scope**:

- Function definitions and calls (other than `print`)
- Object-oriented features
- Multi-dimensional arrays (`int[][]`)
- `break` / `continue`
- Multi-line strings
- `if` / `else` / loops without curly braces

These limitations keep the grammar suitable for introductory lexical and syntax analysis demonstrations.
