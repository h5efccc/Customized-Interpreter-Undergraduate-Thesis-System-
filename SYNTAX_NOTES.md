# PNC Syntax Notes

Quick reference for writing programs in the PNC educational language.

PNC is inspired by **Java**: you declare variables with a data type, every statement ends with a **semicolon** (`;`), and control flow uses **curly braces** `{ }`.

The print form stays simple and familiar:

```text
print("hi");
```

For the full formal grammar, see [GRAMMAR.md](GRAMMAR.md).

---

## Golden Rules

1. Every statement ends with `;` (except blocks and `if`/`else`/`while`/`for` headers)
2. Variables must be declared with a data type before use (reassignment `name = ...;` is allowed after that)
3. `if` / `else` / loop bodies **must** use curly braces `{ }`
4. Newlines are optional — formatting is up to you (like Java)
5. Use double quotes for strings: `"text"`
6. Comments use Java style: `//` and `/* */`
7. Array types use `[]` and must be initialized with `{ ... }`

---

## Templates

### Variable declaration

```text
DATATYPE IDENT = EXPRESSION;
```

| Part | Meaning | Examples |
|------|---------|----------|
| `DATATYPE` | Declared type | `int`, `double`, `string`, `boolean` |
| `IDENT` | Variable name | `a`, `score`, `ok` |
| `EXPRESSION` | Value to assign | `5`, `3.14`, `"hello"`, `true`, `a > b` |

### Print statement

```text
print(EXPRESSION);
```

### If / else statement (Java-style)

```text
if (CONDITION) {
    STATEMENTS
}

if (CONDITION) {
    STATEMENTS
} else {
    STATEMENTS
}

if (CONDITION) {
    STATEMENTS
} else if (CONDITION) {
    STATEMENTS
} else {
    STATEMENTS
}
```

`CONDITION` must evaluate to a **boolean** (`true` / `false`).

### While / do-while / for

```text
while (CONDITION) {
    STATEMENTS
}

do {
    STATEMENTS
} while (CONDITION);

for (INIT; CONDITION; UPDATE) {
    STATEMENTS
}
```

Examples:

```text
int i = 0;
while (i < 3) {
    print(i);
    i++;
}

int n = 0;
do {
    n++;
} while (n < 3);

for (int k = 0; k < 5; k++) {
    print(k);
}
```

`do-while` **must** end with `;`. Empty conditions like `while ()` are syntax errors.

### Arrays

```text
DATATYPE[] IDENT = { EXPR, EXPR, ... };
IDENT[INDEX]
IDENT[INDEX] = EXPR;
```

```text
int[] nums = {10, 20, 30};
print(nums[0]);
nums[1] = 99;
nums[0]++;
```

### Increment / decrement

```text
i++;      // postfix
++i;      // prefix
i--;
--i;
nums[0]++;
```

Works on variables and array elements.

---

## Data Types

| Data type | Use for | Example |
|-----------|---------|---------|
| `int` | Whole numbers | `int count = 10;` |
| `double` | Decimal numbers | `double price = 19.99;` |
| `string` | Text | `string name = "Ana";` |
| `boolean` | True / false | `boolean ok = true;` |
| `int[]` (and other `T[]`) | One-dimensional arrays | `int[] a = {1, 2, 3};` |

Boolean literals: `true`, `false`

---

## Comments

Java-style comments are supported and ignored by the lexer:

```text
// This is a single-line comment

/* This is a
   multi-line block comment */
```

---

## Statement Cheatsheet

```text
// Declarations
int IDENT = NUMBER;
double IDENT = NUMBER;
string IDENT = STRING;
boolean IDENT = true;   // or false, or a boolean expression
int[] IDENT = {1, 2, 3};

// Reassignment / updates
IDENT = EXPRESSION;
IDENT++;
++IDENT;

// Print
print(EXPRESSION);

// If / else
if (CONDITION) {
    STATEMENTS
} else {
    STATEMENTS
}

// Loops
while (CONDITION) { STATEMENTS }
do { STATEMENTS } while (CONDITION);
for (INIT; CONDITION; UPDATE) { STATEMENTS }
```

---

## Expressions

### Arithmetic

| Operator | Meaning | Example |
|----------|---------|---------|
| `+` | Add numbers, or concatenate strings | `a + b`, `"Hi " + name` |
| `-` | Subtract | `a - b` |
| `*` | Multiply | `a * b` |
| `/` | Divide | `a / b` |
| `++` / `--` | Increment / decrement | `i++`, `--nums[0]` |
| `( )` | Grouping / precedence | `(a + b) * 2` |
| `[ ]` | Array index | `nums[i]` |

### Comparison (produce `boolean`)

| Operator | Meaning | Example |
|----------|---------|---------|
| `==` | Equal | `a == b` |
| `!=` | Not equal | `a != b` |
| `<` | Less than | `a < b` |
| `<=` | Less than or equal | `a <= b` |
| `>` | Greater than | `a > b` |
| `>=` | Greater than or equal | `a >= b` |

### Logical (boolean operands)

| Operator | Meaning | Example |
|----------|---------|---------|
| `!` | Logical not | `!ok` |
| `&&` | Logical and (short-circuit) | `ok && ready` |
| `\|\|` | Logical or (short-circuit) | `ok \|\| ready` |

Precedence (highest → lowest):

`( )` `[ ]` postfix `++` `--` → prefix `++` `--` `!` → `*` `/` → `+` `-` → `<` `<=` `>` `>=` → `==` `!=` → `&&` → `||` → `=`

---

## Full Mini Program

```text
// Numbers and print
int a = 5;
int b = 10;
print(a + b);

// Booleans and comparisons
boolean passing = a < b;
print(passing);

/* If / else with curly braces */
if (a < b) {
    print("a is smaller");
} else {
    print("a is not smaller");
}

// else-if chain
int score = 85;
if (score >= 90) {
    print("A");
} else if (score >= 80) {
    print("B");
} else {
    print("C");
}

string fname = "Sheban";
string lname = "Austria";
print(fname + " " + lname);

// Arrays + loops + ++
int[] nums = {1, 2, 3};
int i = 0;
int sum = 0;
while (i < 3) {
    sum = sum + nums[i];
    i++;
}
print(sum);
```

Expected output when executed:

```text
15
True
a is smaller
B
Sheban Austria
6
```

See also `examples/loops_arrays.pnc` for a fuller demo of `while` / `do-while` / `for` and array updates.

---

## Common Mistakes

| Wrong | Why | Correct |
|-------|-----|---------|
| `int a = 5` | Missing `;` | `int a = 5;` |
| `let a = 5;` | `let` is not used | `int a = 5;` |
| `print("hi")` | Missing `;` | `print("hi");` |
| `string n = 5;` | Type mismatch | `string n = "5";` or `int n = 5;` |
| `boolean ok = 1;` | Must be `true`/`false` | `boolean ok = true;` |
| `if (a < b) print(a);` | Body must use `{ }` | `if (a < b) { print(a); }` |
| `if a < b { ... }` | Missing parentheses | `if (a < b) { ... }` |
| `whille (i < 3) { ... }` | Misspelled keyword | `while (i < 3) { ... }` |
| `while () { ... }` | Empty condition | `while (i < 3) { ... }` |
| `do { ... } while (true)` | Missing `;` after do-while | `do { ... } while (true);` |
| `int[] a = {1, 2, 3` | Unclosed array literal | `int[] a = {1, 2, 3};` |
| `int 3rd = 10;` | Identifier cannot start with a digit | `int third = 10;` |

---

## File Extension

Save programs as `.pnc` files (for example `examples/hello.pnc`).
