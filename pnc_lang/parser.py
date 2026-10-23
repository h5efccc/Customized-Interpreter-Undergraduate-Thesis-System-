from __future__ import annotations

from dataclasses import dataclass

from .ast_nodes import (
    ArrayLiteral,
    AssignExpr,
    AssignStmt,
    BinaryExpr,
    BlockStmt,
    BoolLiteral,
    DoWhileStmt,
    Expr,
    ExprStmt,
    ForStmt,
    IfStmt,
    IncompleteExpr,
    IndexExpr,
    NumberLiteral,
    PrintStmt,
    Stmt,
    StringLiteral,
    UnaryExpr,
    UpdateExpr,
    VarDeclStmt,
    Variable,
    WhileStmt,
)
from .diagnostics import Diagnostic, parse_line_column
from .tokens import Token, TokenType

# Data type keywords used in variable declarations
DATA_TYPES = frozenset({"int", "double", "string", "boolean"})
# Keywords that may appear while synchronizing; `else` is included so we can
# stop before an orphaned else, but it cannot *start* a recovered statement.
_STATEMENT_START_KEYWORDS = frozenset({
    "print", "if", "while", "for", "do", "else",
    "int", "double", "string", "boolean",
})
# Tokens that can begin a fresh statement after panic-mode recovery.
_RECOVERABLE_STATEMENT_KEYWORDS = frozenset({
    "print", "if", "while", "for", "do",
    "int", "double", "string", "boolean",
})


class ParseError(Exception):
    """Represents a SYNTAX error detected by the parser."""

    def __init__(
        self,
        message: str,
        *,
        tip: str | None = None,
        partial: Stmt | None = None,
        partial_expr: Expr | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.tip = tip
        self.partial = partial
        self.partial_expr = partial_expr


@dataclass
class ParseOutcome:
    """Result of parsing, including any recoverable partial AST."""

    statements: list[Stmt]
    error: str | None = None
    tip: str | None = None


class Parser:
    """PARSER: checks syntax and builds an abstract syntax tree (AST).

    This is the SYNTAX ANALYSIS phase of the interpreter pipeline.
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0
        # When True, panic-mode recovery continues past errors (multi-error scan).
        # The FA/AST halt-on-first path leaves this False.
        self._collecting_errors = False
        self._diagnostics: list[Diagnostic] = []

    def parse(self) -> list[Stmt]:
        outcome = self.parse_with_recovery()
        if outcome.error:
            raise ParseError(outcome.error, tip=outcome.tip)
        return outcome.statements

    def parse_with_recovery(self) -> ParseOutcome:
        """Parse until the first syntax error (used for AST / diagram display)."""
        statements: list[Stmt] = []
        while not self._is_at_end():
            try:
                statements.append(self._statement())
            except ParseError as e:
                if e.partial is not None:
                    statements.append(e.partial)
                return ParseOutcome(statements, error=e.message, tip=e.tip)
        return ParseOutcome(statements)

    def parse_collecting_errors(self) -> list[Diagnostic]:
        """Scan the full token stream and collect every syntax error.

        Uses panic-mode synchronization so later statements are still checked.
        Does not replace ``parse_with_recovery`` for AST construction.
        """
        self._collecting_errors = True
        self._diagnostics = []
        self.current = 0
        while not self._is_at_end():
            try:
                self._statement()
            except ParseError as e:
                self._record_parse_error(e)
                self._synchronize()
        return list(self._diagnostics)

    def _record_parse_error(self, error: ParseError) -> None:
        line, column = parse_line_column(error.message)
        tip = error.tip or (
            "Fix the syntax problem at the reported location, then run Analyze again."
        )
        self._diagnostics.append(
            Diagnostic(
                stage="syntax",
                message=error.message,
                tip=tip,
                line=line,
                column=column,
            )
        )

    def _at_recoverable_statement(self) -> bool:
        """True when the current token can start a fresh recovered statement."""
        if self._check_keyword(*_RECOVERABLE_STATEMENT_KEYWORDS):
            return True
        if self._check(TokenType.PLUSPLUS) or self._check(TokenType.MINUSMINUS):
            return True
        if self._check(TokenType.IDENT):
            nxt = self._peek_ahead(1)
            if nxt is not None and nxt.type in (
                TokenType.EQUAL,
                TokenType.PLUSPLUS,
                TokenType.MINUSMINUS,
                TokenType.LBRACKET,
                TokenType.SEMICOLON,
                TokenType.RESERVED_KEYWORD,  # e.g. swapped `name type`
            ):
                return True
        return False

    def _synchronize(self) -> None:
        """Skip tokens until a likely statement boundary (panic-mode recovery).

        If the error token already starts the next statement (common when a
        semicolon is missing before `if` / `print` / a declaration), stay put
        so that statement can still be parsed and reported accurately.
        """
        if self._is_at_end():
            return
        if self._at_recoverable_statement():
            return
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._check(TokenType.RBRACE):
                return
            if self._check_keyword("else"):
                return
            if self._at_recoverable_statement():
                return
            self._advance()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        while self.tokens[self.current].type in (
            TokenType.LINE_COMMENT,
            TokenType.BLOCK_COMMENT,
        ):
            self.current += 1
        return self.tokens[self.current]

    def _peek_ahead(self, offset: int = 1) -> Token | None:
        self._peek()
        idx = self.current
        seen = -1
        while idx < len(self.tokens):
            tok = self.tokens[idx]
            idx += 1
            if tok.type in (TokenType.LINE_COMMENT, TokenType.BLOCK_COMMENT):
                continue
            seen += 1
            if seen == offset:
                return tok
        return None

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _check(self, type_: str) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type_

    def _match(self, *types: str) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _match_keyword(self, lexeme: str) -> bool:
        if self._check(TokenType.RESERVED_KEYWORD) and self._peek().lexeme == lexeme:
            self._advance()
            return True
        return False

    def _check_keyword(self, *lexemes: str) -> bool:
        if not self._check(TokenType.RESERVED_KEYWORD):
            return False
        return self._peek().lexeme in lexemes

    def _error(
        self,
        message: str,
        *,
        tip: str | None = None,
        partial: Stmt | None = None,
    ) -> ParseError:
        token = self._peek()
        found = "end of input" if token.type == TokenType.EOF else repr(token.lexeme)
        full = f"{message} at line {token.line}, column {token.column} (found {found})"
        return ParseError(full, tip=tip, partial=partial)

    def _consume(self, type_: str, message: str, *, tip: str | None = None) -> Token:
        if self._check(type_):
            return self._advance()
        raise self._error(message, tip=tip)

    # --- Statements ---

    def _statement(self) -> Stmt:
        if self._check_keyword(*DATA_TYPES):
            return self._var_decl_statement()
        if self._match_keyword("print"):
            return self._print_statement()
        if self._match_keyword("if"):
            return self._if_statement()
        if self._match_keyword("while"):
            return self._while_statement()
        if self._match_keyword("do"):
            return self._do_while_statement()
        if self._match_keyword("for"):
            return self._for_statement()

        token = self._peek()
        if token.type == TokenType.IDENT:
            nxt = self._peek_ahead(1)
            if (
                nxt is not None
                and nxt.type == TokenType.RESERVED_KEYWORD
                and nxt.lexeme in DATA_TYPES
            ):
                return self._recover_swapped_var_decl(token, nxt)

        if self._starts_assign_or_update():
            return self._assign_or_expr_statement()

        tip = self._tip_unexpected_statement(token)
        raise self._error(
            f"Unexpected token {token.lexeme!r}. "
            f"Expected a data type, 'print', 'if', 'while', 'for', 'do', or an assignment",
            tip=tip,
        )

    def _starts_assign_or_update(self) -> bool:
        tok = self._peek()
        if tok.type in (TokenType.PLUSPLUS, TokenType.MINUSMINUS):
            return True
        return tok.type == TokenType.IDENT

    def _assign_or_expr_statement(self) -> Stmt:
        empty = IncompleteExpr("<incomplete>")
        try:
            expr = self._assignment()
        except ParseError as e:
            raise ParseError(
                e.message,
                tip=e.tip or "Expected an assignment or update such as `a = 1;` or `i++;`",
                partial=ExprStmt(e.partial_expr or empty),
            ) from None

        if not self._check(TokenType.SEMICOLON):
            if isinstance(expr, AssignExpr):
                partial: Stmt = AssignStmt(expr.target, expr.value)
            else:
                partial = ExprStmt(expr)
            raise self._error(
                "Expected ';' after statement",
                tip="End the statement with `;`. Example: `i++;` or `a = 10;`",
                partial=partial,
            )
        self._advance()

        if isinstance(expr, AssignExpr):
            return AssignStmt(expr.target, expr.value)
        if isinstance(expr, UpdateExpr):
            return ExprStmt(expr)
        raise self._error(
            "Only assignments and ++/-- updates can be used as expression statements",
            tip="Use `name = value;` or `i++;` / `i--;`. A bare value is not a statement.",
            partial=ExprStmt(expr),
        )

    def _recover_swapped_var_decl(self, name_token: Token, type_token: Token) -> Stmt:
        name = name_token.lexeme
        datatype = type_token.lexeme
        tip = (
            f"Data type should come first before the variable name. "
            f"You wrote `{name} {datatype}`, but the correct order is "
            f"`{datatype} {name} = ...;`. Example: `{datatype} {name} = 10;`"
        )
        self._advance()
        self._advance()

        if not self._check(TokenType.EQUAL):
            raise self._error(
                f"Unexpected token {name!r}. Data type must come before the variable name",
                tip=tip,
                partial=VarDeclStmt(datatype, name, IncompleteExpr("<incomplete>")),
            )
        self._advance()

        try:
            expr = self._expression()
        except ParseError:
            raise ParseError(
                (
                    f"Unexpected token {name!r}. Data type must come before the variable name; "
                    f"also the declaration is incomplete"
                ),
                tip=tip + f" Also finish the value after `=`. Example: `{datatype} {name} = 10;`",
                partial=VarDeclStmt(datatype, name, IncompleteExpr("<missing expression>")),
            ) from None

        if not self._check(TokenType.SEMICOLON):
            raise self._error(
                f"Unexpected token {name!r}. Data type must come before the variable name",
                tip=tip + f" Also end the statement with `;`. Example: `{datatype} {name} = ...;`",
                partial=VarDeclStmt(datatype, name, expr),
            )
        self._advance()
        raise ParseError(
            (
                f"Unexpected token {name!r} at line {name_token.line}, column {name_token.column} "
                f"(found {name!r}). Data type must come before the variable name"
            ),
            tip=tip,
            partial=VarDeclStmt(datatype, name, expr),
        )

    def _tip_unexpected_statement(self, token: Token) -> str:
        if token.type == TokenType.EOF:
            return (
                "The program looks unfinished. Add a complete statement such as "
                "`int a = 10;`, `while (cond) { ... }`, or `print(a);`."
            )
        if token.type == TokenType.NUMBER:
            nxt = self._peek_ahead(1)
            if nxt is not None and nxt.type == TokenType.EQUAL:
                return (
                    "A number cannot be assigned to. "
                    "Did you mean a comparison like `x == 5`, or a declaration like `int x = 5;`?"
                )
            return (
                "A statement cannot start with a number. "
                "Start with a data type, `print`, `if`, `while`, `for`, or `do`."
            )
        if token.type == TokenType.IDENT:
            nxt = self._peek_ahead(1)
            if (
                nxt is not None
                and nxt.type == TokenType.RESERVED_KEYWORD
                and nxt.lexeme in DATA_TYPES
            ):
                return (
                    f"Data type should come first before the variable name. "
                    f"You wrote `{token.lexeme} {nxt.lexeme}`, but the correct order is "
                    f"`{nxt.lexeme} {token.lexeme} = ...;`."
                )
            if nxt is not None and nxt.type == TokenType.LPAREN:
                return (
                    f"`{token.lexeme}` is not a valid statement keyword. "
                    f"If you meant to print, write `print(...)`. "
                    f"For loops use `while`, `for`, or `do`."
                )
            if nxt is not None and nxt.type == TokenType.EQUAL:
                return (
                    f"Assignment alone needs a semicolon: `{token.lexeme} = ...;`. "
                    f"Or declare first: `int {token.lexeme} = ...;`"
                )
            return (
                "A variable declaration must start with a data type "
                "(int, double, string, or boolean), then the variable name. "
                f"Example: `int {token.lexeme} = 10;`"
            )
        if token.type == TokenType.RESERVED_KEYWORD and token.lexeme in {
            "else",
            "true",
            "false",
        }:
            return (
                f"`{token.lexeme}` cannot start a statement here. "
                "Use a data type, `print`, `if`, `while`, `for`, or `do`."
            )
        return (
            "Statements must begin with a data type, `print`, `if`, `while`, `for`, `do`, "
            "or an assignment / update. Example: `int a = 10;` or `while (i < 3) { ... }`"
        )

    def _parse_datatype(self) -> str:
        """Parse `int` or `int[]` (and the same for other types)."""
        type_token = self._advance()
        datatype = type_token.lexeme
        if self._match(TokenType.LBRACKET):
            if not self._check(TokenType.RBRACKET):
                raise self._error(
                    "Expected ']' after '[' in array type",
                    tip=f"Write array types as `{datatype}[] name = {{...}};`",
                    partial=VarDeclStmt(f"{datatype}[]", "<missing name>", IncompleteExpr("<incomplete>")),
                )
            self._advance()
            datatype = f"{datatype}[]"
        return datatype

    def _var_decl_statement(self, *, consume_semicolon: bool = True) -> VarDeclStmt:
        """Parse: DATATYPE([])? IDENT = Expression ;?"""
        datatype = self._parse_datatype()

        if not self._check(TokenType.IDENT):
            raise self._error(
                f"Expected variable name after '{datatype}'",
                tip=(
                    f"After the data type `{datatype}`, write a variable name, then `=`, "
                    f"then a value, then `;`. Example: `{datatype} myVar = 0;`"
                ),
                partial=VarDeclStmt(datatype, "<missing name>", IncompleteExpr("<incomplete>")),
            )
        name_token = self._advance()
        name = name_token.lexeme

        if not self._check(TokenType.EQUAL):
            raise self._error(
                "Expected '=' after variable name",
                tip=(
                    f"After `{datatype} {name}`, write `=` then a value. "
                    f"Example: `{datatype} {name} = 10;`"
                ),
                partial=VarDeclStmt(datatype, name, IncompleteExpr("<incomplete>")),
            )
        self._advance()

        try:
            if datatype.endswith("[]") and self._check(TokenType.LBRACE):
                expr = self._array_literal()
            else:
                expr = self._expression()
        except ParseError as e:
            tip = e.tip or (
                f"The declaration `{datatype} {name} =` is incomplete. "
                f"Provide a value after `=` and end the statement with `;`."
            )
            if datatype.endswith("[]"):
                tip = (
                    f"Array declarations need an initializer list. "
                    f"Example: `{datatype} {name} = {{1, 2, 3}};`"
                )
            raise ParseError(
                e.message,
                tip=tip,
                partial=VarDeclStmt(
                    datatype, name, e.partial_expr or IncompleteExpr("<missing expression>")
                ),
            ) from None

        if consume_semicolon:
            if not self._check(TokenType.SEMICOLON):
                raise self._error(
                    "Expected ';' after variable declaration",
                    tip=(
                        f"Every variable declaration must end with a semicolon. "
                        f"Try: `{datatype} {name} = ...;`"
                    ),
                    partial=VarDeclStmt(datatype, name, expr),
                )
            self._advance()
        return VarDeclStmt(datatype, name, expr)

    def _array_literal(self) -> ArrayLiteral:
        """Parse: { Expression ( , Expression )* }"""
        self._advance()  # {
        elements: list[Expr] = []
        if not self._check(TokenType.RBRACE):
            while True:
                try:
                    elements.append(self._expression())
                except ParseError as e:
                    raise ParseError(
                        e.message,
                        tip=e.tip or "Array elements must be valid expressions separated by commas.",
                        partial_expr=ArrayLiteral(tuple(elements)),
                    ) from None
                if not self._match(TokenType.COMMA):
                    break
                if self._check(TokenType.RBRACE):
                    raise self._error(
                        "Trailing comma in array literal",
                        tip="Remove the extra comma before `}`. Example: `{1, 2, 3}`",
                        partial=None,
                    )
        if not self._check(TokenType.RBRACE):
            raise self._error(
                "Expected '}' to close array literal",
                tip="Close the array initializer with `}`. Example: `int[] a = {1, 2, 3};`",
                partial=None,
            )
        self._advance()
        return ArrayLiteral(tuple(elements))

    def _print_statement(self) -> PrintStmt:
        if not self._check(TokenType.LPAREN):
            raise self._error(
                "Expected '(' after 'print'",
                tip="`print` must be followed by parentheses. Example: `print(a);`",
                partial=PrintStmt(IncompleteExpr("<incomplete>")),
            )
        self._advance()

        try:
            expr = self._expression()
        except ParseError as e:
            raise ParseError(
                e.message,
                tip="`print(...)` needs an expression inside the parentheses. Example: `print(10);`",
                partial=PrintStmt(IncompleteExpr("<missing expression>")),
            ) from None

        if not self._check(TokenType.RPAREN):
            tip = self._tip_unclosed_paren(self._peek(), context="print(...) argument")
            raise self._error(
                "Expected ')' after expression",
                tip=tip,
                partial=PrintStmt(expr),
            )
        self._advance()

        if not self._check(TokenType.SEMICOLON):
            raise self._error(
                "Expected ';' after print statement",
                tip="End the print statement with `;`. Example: `print(a);`",
                partial=PrintStmt(expr),
            )
        self._advance()
        return PrintStmt(expr)

    def _if_statement(self) -> IfStmt:
        empty_then = BlockStmt(())
        if not self._check(TokenType.LPAREN):
            raise self._error(
                "Expected '(' after 'if'",
                tip="An `if` condition must be wrapped in parentheses. Example: `if (a > 0) { ... }`",
                partial=IfStmt(IncompleteExpr("<incomplete>"), empty_then, None),
            )
        self._advance()

        if self._check(TokenType.RPAREN):
            raise self._error(
                "Empty if condition: expected an expression inside the parentheses",
                tip="Write a boolean condition inside `if (...)`. Example: `if (a > 0) { print(a); }`",
                partial=IfStmt(IncompleteExpr("<empty condition>"), empty_then, None),
            )

        try:
            condition = self._expression()
        except ParseError as e:
            raise ParseError(
                e.message,
                tip=e.tip
                or "Write a boolean condition inside `if (...)`. Example: `if (a > 0) { print(a); }`",
                partial=IfStmt(
                    e.partial_expr or IncompleteExpr("<missing condition>"),
                    empty_then,
                    None,
                ),
            ) from None

        if not self._check(TokenType.RPAREN):
            bad = self._peek()
            tip = self._tip_unclosed_paren(bad, context="if condition")
            if bad.type == TokenType.BANG:
                nxt = self._peek_ahead(1)
                if nxt is not None and nxt.type == TokenType.EQUAL:
                    raise self._error(
                        "Invalid operator sequence '! =' - write '!=' as one token",
                        tip=tip,
                        partial=IfStmt(condition, empty_then, None),
                    )
            if bad.type == TokenType.EQUAL:
                raise self._error(
                    "Invalid '=' in if condition - use '==' for comparison",
                    tip=tip,
                    partial=IfStmt(condition, empty_then, None),
                )
            if bad.type == TokenType.LBRACE:
                raise self._error(
                    "Expected ')' after if condition before '{'",
                    tip=tip,
                    partial=IfStmt(condition, empty_then, None),
                )
            raise self._error(
                "Expected ')' after if condition",
                tip=tip,
                partial=IfStmt(condition, empty_then, None),
            )
        self._advance()

        try:
            then_branch = self._block(context="if")
        except ParseError as e:
            then_partial = empty_then
            if isinstance(e.partial, BlockStmt):
                then_partial = e.partial
            elif isinstance(e.partial, Stmt):
                then_partial = BlockStmt((e.partial,))
            raise ParseError(
                e.message,
                tip=e.tip or "After `if (condition)` write a curly-brace block: `if (cond) { ... }`",
                partial=IfStmt(condition, then_partial, None),
            ) from None

        else_branch: Stmt | None = None
        if self._match_keyword("else"):
            try:
                if self._match_keyword("if"):
                    else_branch = self._if_statement()
                else:
                    else_branch = self._block(context="else")
            except ParseError as e:
                else_partial: Stmt | None = None
                if isinstance(e.partial, (BlockStmt, IfStmt)):
                    else_partial = e.partial
                elif isinstance(e.partial, Stmt):
                    else_partial = BlockStmt((e.partial,))
                raise ParseError(
                    e.message,
                    tip=e.tip or "After `else` write a `{ ... }` block or another `if`.",
                    partial=IfStmt(condition, then_branch, else_partial),
                ) from None

        return IfStmt(condition, then_branch, else_branch)

    def _while_statement(self) -> WhileStmt:
        empty = BlockStmt(())
        if not self._check(TokenType.LPAREN):
            raise self._error(
                "Expected '(' after 'while'",
                tip="A `while` condition must be in parentheses. Example: `while (i < 10) { ... }`",
                partial=WhileStmt(IncompleteExpr("<incomplete>"), empty),
            )
        self._advance()

        if self._check(TokenType.RPAREN):
            raise self._error(
                "Empty while condition: expected an expression inside the parentheses",
                tip="Write a boolean condition inside `while (...)`. Example: `while (i < 10) { i++; }`",
                partial=WhileStmt(IncompleteExpr("<empty condition>"), empty),
            )

        try:
            condition = self._expression()
        except ParseError as e:
            raise ParseError(
                e.message,
                tip=e.tip or "Write a boolean condition inside `while (...)`.",
                partial=WhileStmt(e.partial_expr or IncompleteExpr("<missing condition>"), empty),
            ) from None

        if not self._check(TokenType.RPAREN):
            tip = self._tip_unclosed_paren(self._peek(), context="while condition")
            raise self._error(
                "Expected ')' after while condition",
                tip=tip,
                partial=WhileStmt(condition, empty),
            )
        self._advance()

        try:
            body = self._block(context="while")
        except ParseError as e:
            body_partial = empty
            if isinstance(e.partial, BlockStmt):
                body_partial = e.partial
            elif isinstance(e.partial, Stmt):
                body_partial = BlockStmt((e.partial,))
            raise ParseError(
                e.message,
                tip=e.tip or "After `while (condition)` write a `{ ... }` block.",
                partial=WhileStmt(condition, body_partial),
            ) from None
        return WhileStmt(condition, body)

    def _do_while_statement(self) -> DoWhileStmt:
        empty = BlockStmt(())
        try:
            body = self._block(context="do")
        except ParseError as e:
            body_partial = empty
            if isinstance(e.partial, BlockStmt):
                body_partial = e.partial
            elif isinstance(e.partial, Stmt):
                body_partial = BlockStmt((e.partial,))
            raise ParseError(
                e.message,
                tip=e.tip or "After `do` write a `{ ... }` block, then `while (cond);`.",
                partial=DoWhileStmt(body_partial, IncompleteExpr("<incomplete>")),
            ) from None

        if not self._match_keyword("while"):
            raise self._error(
                "Expected 'while' after do-block",
                tip="A do-while loop ends with `while (condition);`. Example: `do { i++; } while (i < 10);`",
                partial=DoWhileStmt(body, IncompleteExpr("<missing while>")),
            )

        if not self._check(TokenType.LPAREN):
            raise self._error(
                "Expected '(' after 'while' in do-while",
                tip="Write `do { ... } while (condition);`",
                partial=DoWhileStmt(body, IncompleteExpr("<incomplete>")),
            )
        self._advance()

        if self._check(TokenType.RPAREN):
            raise self._error(
                "Empty do-while condition: expected an expression inside the parentheses",
                tip="Write a boolean condition inside `while (...)`.",
                partial=DoWhileStmt(body, IncompleteExpr("<empty condition>")),
            )

        try:
            condition = self._expression()
        except ParseError as e:
            raise ParseError(
                e.message,
                tip=e.tip or "Write a boolean condition inside `do { ... } while (...)`.",
                partial=DoWhileStmt(body, e.partial_expr or IncompleteExpr("<missing condition>")),
            ) from None

        if not self._check(TokenType.RPAREN):
            tip = self._tip_unclosed_paren(self._peek(), context="do-while condition")
            raise self._error(
                "Expected ')' after do-while condition",
                tip=tip,
                partial=DoWhileStmt(body, condition),
            )
        self._advance()

        if not self._check(TokenType.SEMICOLON):
            raise self._error(
                "Expected ';' after do-while statement",
                tip="End a do-while with a semicolon: `do { ... } while (cond);`",
                partial=DoWhileStmt(body, condition),
            )
        self._advance()
        return DoWhileStmt(body, condition)

    def _for_statement(self) -> ForStmt:
        empty = BlockStmt(())
        if not self._check(TokenType.LPAREN):
            raise self._error(
                "Expected '(' after 'for'",
                tip="A `for` header looks like `for (init; condition; update) { ... }`",
                partial=ForStmt(None, IncompleteExpr("<incomplete>"), None, empty),
            )
        self._advance()

        # init
        initializer: Stmt | None = None
        if not self._check(TokenType.SEMICOLON):
            try:
                if self._check_keyword(*DATA_TYPES):
                    initializer = self._var_decl_statement(consume_semicolon=False)
                else:
                    expr = self._assignment()
                    if isinstance(expr, AssignExpr):
                        initializer = AssignStmt(expr.target, expr.value)
                    elif isinstance(expr, UpdateExpr):
                        initializer = ExprStmt(expr)
                    else:
                        raise self._error(
                            "Invalid for-loop initializer",
                            tip="Use a declaration or assignment: `for (int i = 0; ...)` or `for (i = 0; ...)`.",
                            partial=ForStmt(None, None, None, empty),
                        )
            except ParseError as e:
                raise ParseError(
                    e.message,
                    tip=e.tip or "Invalid for-loop initializer. Example: `for (int i = 0; i < 10; i++) { ... }`",
                    partial=ForStmt(e.partial, None, None, empty) if isinstance(e.partial, Stmt) else ForStmt(None, None, None, empty),
                ) from None

        if not self._check(TokenType.SEMICOLON):
            raise self._error(
                "Expected ';' after for-loop initializer",
                tip="`for` needs three parts separated by `;`: `for (init; condition; update)`.",
                partial=ForStmt(initializer, None, None, empty),
            )
        self._advance()

        # condition (optional)
        condition: Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            try:
                condition = self._expression()
            except ParseError as e:
                raise ParseError(
                    e.message,
                    tip=e.tip or "Invalid for-loop condition. Example: `i < 10`",
                    partial=ForStmt(initializer, e.partial_expr, None, empty),
                ) from None

        if not self._check(TokenType.SEMICOLON):
            raise self._error(
                "Expected ';' after for-loop condition",
                tip="`for` needs three parts separated by `;`: `for (init; condition; update)`.",
                partial=ForStmt(initializer, condition, None, empty),
            )
        self._advance()

        # update (optional)
        update: Expr | None = None
        if not self._check(TokenType.RPAREN):
            try:
                update = self._assignment()
            except ParseError as e:
                raise ParseError(
                    e.message,
                    tip=e.tip or "Invalid for-loop update. Example: `i++` or `i = i + 1`",
                    partial=ForStmt(initializer, condition, e.partial_expr, empty),
                ) from None

        if not self._check(TokenType.RPAREN):
            tip = self._tip_unclosed_paren(self._peek(), context="for header")
            raise self._error(
                "Expected ')' after for-loop header",
                tip=tip,
                partial=ForStmt(initializer, condition, update, empty),
            )
        self._advance()

        try:
            body = self._block(context="for")
        except ParseError as e:
            body_partial = empty
            if isinstance(e.partial, BlockStmt):
                body_partial = e.partial
            elif isinstance(e.partial, Stmt):
                body_partial = BlockStmt((e.partial,))
            raise ParseError(
                e.message,
                tip=e.tip or "After `for (...)` write a `{ ... }` block.",
                partial=ForStmt(initializer, condition, update, body_partial),
            ) from None
        return ForStmt(initializer, condition, update, body)

    def _block(self, *, context: str = "block") -> BlockStmt:
        if not self._check(TokenType.LBRACE):
            raise self._error(
                f"Expected '{{' to start a {context} body",
                tip=(
                    f"In PNC, `{context}` bodies must use curly braces `{{ }}`. "
                    f"Example: `{context} (...) {{ ... }}`"
                    if context in {"if", "while", "for", "else"}
                    else f"After `{context}` write a curly-brace block `{{ ... }}`."
                ),
            )
        self._advance()
        statements: list[Stmt] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            try:
                statements.append(self._statement())
            except ParseError as e:
                if self._collecting_errors:
                    self._record_parse_error(e)
                    if e.partial is not None:
                        statements.append(e.partial)
                    self._synchronize()
                    continue
                recovered = list(statements)
                if e.partial is not None:
                    recovered.append(e.partial)
                raise ParseError(
                    e.message,
                    tip=e.tip,
                    partial=BlockStmt(tuple(recovered)),
                ) from None
        if not self._check(TokenType.RBRACE):
            raise self._error(
                "Expected '}' after block - unmatched opening '{'",
                tip="Close the block with `}`. Every `{` needs a matching `}`.",
                partial=BlockStmt(tuple(statements)),
            )
        self._advance()
        return BlockStmt(tuple(statements))

    def _tip_unclosed_paren(self, token: Token, *, context: str) -> str:
        if token.type == TokenType.BANG:
            nxt = self._peek_ahead(1)
            if nxt is not None and nxt.type == TokenType.EQUAL:
                return (
                    "Write inequality as one operator `!=` with no spaces between `!` and `=`. "
                    "Example: `if (x != 5) { ... }`"
                )
            return (
                f"Unexpected `!` inside the {context}. "
                "For inequality use `!=` (no spaces). For logical not use `!ok`."
            )
        if token.type == TokenType.EQUAL:
            return (
                f"Found `=` inside the {context}. "
                "Use `==` for equality comparison (assignment `=` is not allowed in conditions)."
            )
        if token.type == TokenType.LBRACE:
            return (
                f"Missing `)` before `{{` in the {context}. "
                "Close the parentheses first, then open the block."
            )
        if "print" in context:
            return "Close the `print` call with `)` before the semicolon. Example: `print(a);`"
        if "grouped" in context:
            return "A grouped expression needs a closing `)`. Example: `(a + b)`"
        if "for" in context:
            return "Close the `for` header with `)` then open a `{ ... }` block."
        return f"Close the {context} with `)` then continue the statement."

    # --- Expressions ---

    def _expression(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        expr = self._logic_or()
        if self._match(TokenType.EQUAL):
            if not self._is_lvalue(expr):
                raise self._error(
                    "Invalid assignment target",
                    tip="Only variables and array elements can be assigned. Example: `a = 1;` or `nums[0] = 1;`",
                    partial=None,
                )
            try:
                value = self._assignment()
            except ParseError as e:
                raise ParseError(
                    e.message,
                    tip=e.tip or "Provide a value after `=`. Example: `a = 10`",
                    partial_expr=AssignExpr(expr, e.partial_expr or IncompleteExpr("<missing>")),
                ) from None
            return AssignExpr(expr, value)
        return expr

    @staticmethod
    def _is_lvalue(expr: Expr) -> bool:
        return isinstance(expr, (Variable, IndexExpr))

    def _finish_binary(self, left: Expr, op: Token, parse_right) -> Expr:
        try:
            right = parse_right()
        except ParseError as e:
            incomplete = BinaryExpr(left, op, e.partial_expr or IncompleteExpr("<missing operand>"))
            raise ParseError(
                e.message,
                tip=(
                    f"Operator `{op.lexeme}` is missing its right-hand expression. "
                    f"Example: `a {op.lexeme} b`"
                ),
                partial_expr=incomplete,
            ) from None
        return BinaryExpr(left, op, right)

    def _logic_or(self) -> Expr:
        expr = self._logic_and()
        while self._match(TokenType.OROR):
            op = self._previous()
            expr = self._finish_binary(expr, op, self._logic_and)
        return expr

    def _logic_and(self) -> Expr:
        expr = self._equality()
        while self._match(TokenType.ANDAND):
            op = self._previous()
            expr = self._finish_binary(expr, op, self._equality)
        return expr

    def _equality(self) -> Expr:
        expr = self._comparison()
        while self._match(TokenType.EQEQ, TokenType.BANG_EQUAL):
            op = self._previous()
            expr = self._finish_binary(expr, op, self._comparison)
        return expr

    def _comparison(self) -> Expr:
        expr = self._term()
        while self._match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            op = self._previous()
            expr = self._finish_binary(expr, op, self._term)
        return expr

    def _term(self) -> Expr:
        expr = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous()
            expr = self._finish_binary(expr, op, self._factor)
        return expr

    def _factor(self) -> Expr:
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH):
            op = self._previous()
            expr = self._finish_binary(expr, op, self._unary)
        return expr

    def _unary(self) -> Expr:
        if self._match(TokenType.BANG):
            op = self._previous()
            try:
                right = self._unary()
            except ParseError as e:
                raise ParseError(
                    e.message,
                    tip=e.tip or "Unary `!` needs an expression after it. Example: `!ok`",
                    partial_expr=UnaryExpr(op, e.partial_expr or IncompleteExpr("<missing operand>")),
                ) from None
            return UnaryExpr(op, right)

        if self._match(TokenType.PLUSPLUS, TokenType.MINUSMINUS):
            op = self._previous()
            try:
                target = self._unary()
            except ParseError as e:
                raise ParseError(
                    e.message,
                    tip=e.tip or f"Prefix `{op.lexeme}` needs a variable. Example: `{op.lexeme}i`",
                    partial_expr=UpdateExpr(op, e.partial_expr or IncompleteExpr("<missing>"), True),
                ) from None
            if not self._is_lvalue(target):
                raise self._error(
                    f"Invalid operand for prefix '{op.lexeme}'",
                    tip=f"`{op.lexeme}` only works on variables or array elements. Example: `{op.lexeme}i`",
                )
            return UpdateExpr(op, target, True)

        return self._postfix()

    def _postfix(self) -> Expr:
        expr = self._primary()
        while True:
            if self._match(TokenType.LBRACKET):
                try:
                    index = self._expression()
                except ParseError as e:
                    raise ParseError(
                        e.message,
                        tip=e.tip or "Array index must be an expression. Example: `nums[0]`",
                        partial_expr=IndexExpr(expr, e.partial_expr or IncompleteExpr("<missing index>")),
                    ) from None
                if not self._check(TokenType.RBRACKET):
                    raise self._error(
                        "Expected ']' after array index",
                        tip="Close the index with `]`. Example: `nums[i]`",
                    )
                self._advance()
                expr = IndexExpr(expr, index)
                continue

            if self._match(TokenType.PLUSPLUS, TokenType.MINUSMINUS):
                op = self._previous()
                if not self._is_lvalue(expr):
                    raise self._error(
                        f"Invalid operand for postfix '{op.lexeme}'",
                        tip=f"`{op.lexeme}` only works on variables or array elements. Example: `i{op.lexeme}`",
                    )
                expr = UpdateExpr(op, expr, False)
                continue
            break
        return expr

    def _primary(self) -> Expr:
        if self._match(TokenType.NUMBER):
            return NumberLiteral(self._previous().value)
        if self._match(TokenType.STRING):
            return StringLiteral(self._previous().value)
        if self._match_keyword("true"):
            return BoolLiteral(True)
        if self._match_keyword("false"):
            return BoolLiteral(False)
        if self._match(TokenType.IDENT):
            return Variable(self._previous().lexeme)
        if self._match(TokenType.LPAREN):
            try:
                expr = self._expression()
            except ParseError as e:
                raise ParseError(
                    e.message,
                    tip=e.tip or "A grouped expression needs a complete value inside `(...)`.",
                    partial_expr=e.partial_expr or IncompleteExpr("<incomplete group>"),
                ) from None
            if not self._check(TokenType.RPAREN):
                tip = self._tip_unclosed_paren(self._peek(), context="grouped expression")
                raise self._error("Expected ')' after expression", tip=tip)
            self._advance()
            return expr

        # Array literal only valid as a primary when `{` starts an initializer expression
        if self._check(TokenType.LBRACE):
            return self._array_literal()

        token = self._peek()
        if token.type == TokenType.EOF:
            raise self._error(
                "Expected expression",
                tip="The expression is missing. Add a value such as a number, string, variable, or `true`/`false`.",
            )
        if token.type == TokenType.BANG:
            nxt = self._peek_ahead(1)
            if nxt is not None and nxt.type == TokenType.EQUAL:
                raise self._error(
                    "Expected expression",
                    tip=(
                        "Write inequality as one operator `!=` with no spaces between `!` and `=`. "
                        "Example: `x != 5`"
                    ),
                )
        if token.type == TokenType.EQUAL:
            raise self._error(
                "Expected expression",
                tip=(
                    "Found `=` where an expression value was expected. "
                    "Use `==` for comparison, or put assignment in a statement like `int x = 5;`."
                ),
            )
        raise self._error(
            "Expected expression",
            tip=(
                f"Expected a value here, but found {token.lexeme!r}. "
                "Use a number, string, variable name, array index, or `true`/`false`."
            ),
        )
