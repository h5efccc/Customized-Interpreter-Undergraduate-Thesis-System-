from __future__ import annotations
from typing import Any
from .tokens import Token, TokenType

class LexerError(Exception):
    """Represents an error that happens during lexical analysis (tokenization)."""
class Lexer:
    """LEXER: turns raw source code characters into a list of tokens.

    This is the LEXICAL ANALYSIS phase of the interpreter pipeline.
    """
    def __init__(self, source: str):
        # Full source code as one string
        self.source = source
        # Accumulated list of tokens produced by the lexer
        self.tokens: list[Token] = []
        # Index where the current token starts
        self.start = 0
        # Index of the character we are currently looking at
        self.current = 0
        # Current line and column (for error messages)
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        """Scan the entire source string and return the list of tokens."""
        # Keep scanning until we reach the end of the source
        while not self._is_at_end():
            # Mark the start of the next token
            self.start = self.current
            self._scan_token()

        # Add a special EOF token so the parser knows where the input ends
        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return self.tokens

    def _is_at_end(self) -> bool:
        """Return True when we have consumed all characters in the source."""
        return self.current >= len(self.source)

    def _advance(self) -> str:
        """Consume the current character and move to the next one."""
        ch = self.source[self.current]
        self.current += 1
        self.column += 1
        return ch

    def _add_token(self, type_: str, value: Any = None) -> None:
        """Create a new token for the current lexeme and store it."""
        text = self.source[self.start : self.current]
        start_col = self.column - (self.current - self.start)
        self.tokens.append(Token(type_, text, value, self.line, start_col))

    def _peek(self) -> str:
        """Look at the current character without consuming it."""
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        """Look one character ahead without consuming it."""
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _scan_token(self) -> None:
        """Identify one token starting at the current position."""
        ch = self._advance()

        # Ignore whitespace characters (space, tab, carriage return)
        if ch in " \t\r":
            return

        # Newline: produce a NEWLINE token and update line/column counters
        if ch == "\n":
            self.tokens.append(Token(TokenType.NEWLINE, "\\n", None, self.line, self.column))
            self.line += 1
            self.column = 1
            return

        # Single-character tokens (operators and parentheses)
        if ch == "+":
            self._add_token(TokenType.PLUS)
            return
        if ch == "-":
            self._add_token(TokenType.MINUS)
            return
        if ch == "*":
            self._add_token(TokenType.STAR)
            return
        if ch == "/":
            self._add_token(TokenType.SLASH)
            return
        if ch == "=":
            self._add_token(TokenType.EQUAL)
            return
        if ch == "(":
            self._add_token(TokenType.LPAREN)
            return
        if ch == ")":
            self._add_token(TokenType.RPAREN)
            return

        # Start of a string literal
        if ch == '"':
            self._string()
            return

        # Start of a number (integer or decimal)
        if ch.isdigit():
            self._number()
            return

        # Start of an identifier or keyword
        if ch.isalpha() or ch == "_":
            self._identifier()
            return

        # Any other character is not allowed in this language
        raise LexerError(f"Unexpected character '{ch}' at line {self.line}, column {self.column}")

    def _string(self) -> None:
        """Scan a string literal until the closing quote or an error occurs."""
        start_col = self.column
        value_chars: list[str] = []
        # Keep consuming characters until we see another quote
        while not self._is_at_end() and self._peek() != '"':
            c = self._advance()
            # We do not allow multi-line strings in this simple language
            if c == "\n":
                raise LexerError(f"Unterminated string at line {self.line}, column {start_col}")
            value_chars.append(c)

        # If we reached the end of input without a closing quote, it's an error
        if self._is_at_end():
            raise LexerError(f"Unterminated string at line {self.line}, column {start_col}")

        # Consume the closing quote
        self._advance()
        # The token value is the contents between the quotes
        self._add_token(TokenType.STRING, "".join(value_chars))

    def _number(self) -> None:
        """Scan a number literal (e.g., 5, 10.5)."""
        # Consume the integer part
        while self._peek().isdigit():
            self._advance()
        # Optional fractional part after a dot
        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()

        num_text = self.source[self.start : self.current]
        self._add_token(TokenType.NUMBER, float(num_text))

    def _identifier(self) -> None:
        """Scan an identifier or a reserved keyword like 'let' or 'print'."""
        # Identifiers can contain letters, digits, and underscores
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        text = self.source[self.start : self.current]
        # Map exact words to keyword token types; otherwise it's a generic identifier
        if text == "let":
            type_ = TokenType.LET
        elif text == "print":
            type_ = TokenType.PRINT
        else:
            type_ = TokenType.IDENT

        start_col = self.column - (self.current - self.start)
        self.tokens.append(Token(type_, text, text, self.line, start_col))

