from __future__ import annotations

from .ast_nodes import (
    BinaryExpr,
    Expr,
    LetStmt,
    NumberLiteral,
    PrintStmt,
    Stmt,
    StringLiteral,
    Variable,
)
from .tokens import Token, TokenType


class ParseError(Exception):
    """Represents a SYNTAX error detected by the parser."""


class Parser:
    """PARSER: checks syntax and builds an abstract syntax tree (AST).

    This is the SYNTAX ANALYSIS phase of the interpreter pipeline.
    """

    def __init__(self, tokens: list[Token]):
        # List of tokens previously produced by the lexer
        self.tokens = tokens
        # Index of the current token in that list
        self.current = 0

    def parse(self) -> list[Stmt]:
        """Parse the full token list into a list of statement nodes."""
        statements: list[Stmt] = []
        # Continue until we hit the EOF token
        while not self._is_at_end():
            # Ignore empty lines
            if self._match(TokenType.NEWLINE):
                continue
            # Parse a single statement (let or print)
            statements.append(self._statement())
        return statements

    def _is_at_end(self) -> bool:
        """Return True once we have reached the EOF token."""
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        """Look at the current token without consuming it."""
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        """Consume the current token and move to the next one."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _check(self, type_: str) -> bool:
        """Return True if the current token has the given type."""
        if self._is_at_end():
            return False
        return self._peek().type == type_

    def _match(self, *types: str) -> bool:
        """If the current token matches any of the given types, consume it."""
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, type_: str, message: str) -> Token:
        """Consume a token of a specific type or raise a syntax error."""
        if self._check(type_):
            return self._advance()
        token = self._peek()
        # Attach line/column info to make error messages educational
        raise ParseError(f"{message} at line {token.line}, column {token.column} (found {token.lexeme!r})")

    def _statement(self) -> Stmt:
        """Parse a single statement (either 'let' or 'print')."""
        if self._match(TokenType.LET):
            return self._let_statement()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        token = self._peek()
        raise ParseError(f"Unexpected token {token.lexeme!r} at line {token.line}, column {token.column}")

    def _let_statement(self) -> LetStmt:
        """Parse: let <identifier> = <expression>"""
        name_token = self._consume(TokenType.IDENT, "Expected variable name after 'let'")
        self._consume(TokenType.EQUAL, "Expected '=' after variable name")
        expr = self._expression()
        # NEWLINE is optional because we treat EOF similarly
        self._match(TokenType.NEWLINE)
        return LetStmt(name_token.lexeme, expr)

    def _print_statement(self) -> PrintStmt:
        """Parse: print(<expression>)"""
        self._consume(TokenType.LPAREN, "Expected '(' after 'print'")
        expr = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after expression")
        self._match(TokenType.NEWLINE)
        return PrintStmt(expr)

    def _expression(self) -> Expr:
        """Parse an expression with + and - (lowest precedence)."""
        expr = self._term()
        # Allow chains like: a + b - c
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous()
            right = self._term()
            expr = BinaryExpr(expr, op, right)
        return expr

    def _term(self) -> Expr:
        """Parse a term with * and / (higher precedence than + and -)."""
        expr = self._factor()
        # Allow chains like: a * b / c
        while self._match(TokenType.STAR, TokenType.SLASH):
            op = self._previous()
            right = self._factor()
            expr = BinaryExpr(expr, op, right)
        return expr

    def _factor(self) -> Expr:
        """Parse the smallest building blocks: numbers, strings, variables, (expr)."""
        if self._match(TokenType.NUMBER):
            return NumberLiteral(self._previous().value)
        if self._match(TokenType.STRING):
            return StringLiteral(self._previous().value)
        if self._match(TokenType.IDENT):
            return Variable(self._previous().lexeme)
        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        token = self._peek()
        raise ParseError(f"Expected expression at line {token.line}, column {token.column}")
