from __future__ import annotations
from typing import Any
from .tokens import Token, TokenType

# Java-inspired reserved words
KEYWORDS = frozenset({
    "int", "double", "string", "boolean",
    "print", "if", "else", "while", "for", "do",
    "true", "false",
})

# Tokens that cannot legally end a complete source file on their own.
# A trailing '/' after `int a = 10;` is a common student mistake.
INCOMPLETE_AT_EOF = frozenset({
    TokenType.PLUS,
    TokenType.MINUS,
    TokenType.STAR,
    TokenType.SLASH,
    TokenType.EQUAL,
    TokenType.EQEQ,
    TokenType.BANG,
    TokenType.BANG_EQUAL,
    TokenType.LESS,
    TokenType.LESS_EQUAL,
    TokenType.GREATER,
    TokenType.GREATER_EQUAL,
    TokenType.ANDAND,
    TokenType.OROR,
    TokenType.LPAREN,
    TokenType.LBRACE,
    TokenType.LBRACKET,
    TokenType.COMMA,
})


def suggest_keyword(text: str) -> str | None:
    """If `text` looks like a near-miss spelling of a keyword, return that keyword.

    Catches:
    - same-length single substitution / adjacent transpose (`imt` → `int`, `pritn` → `print`)
    - one missing letter (`pint` → `print`, `doubl` → `double`)
    - one doubled extra letter (`intt` → `int`, `printt` → `print`)

    Deliberately does **not** flag ordinary identifiers like `into` or `score`
    (extra non-repeated letters are allowed).
    """
    if text in KEYWORDS or len(text) < 2:
        return None
    best: str | None = None
    best_rank = 99  # lower is better
    for kw in KEYWORDS:
        rank = _keyword_near_miss_rank(text, kw)
        if rank is not None and rank < best_rank:
            best_rank = rank
            best = kw
    return best


def _keyword_near_miss_rank(text: str, kw: str) -> int | None:
    """Return a small rank if `text` is a near miss of `kw`, else None."""
    if text == kw:
        return None
    # Same length: one substitution or adjacent transposition
    if len(text) == len(kw):
        if _levenshtein(text, kw) == 1:
            return 1
        if _is_adjacent_transpose(text, kw):
            return 1
        return None
    # One extra letter — only doubled-adjacent typos (intt→int), not into→int
    if len(text) == len(kw) + 1:
        for i in range(len(text)):
            if text[:i] + text[i + 1 :] != kw:
                continue
            left = text[i - 1] if i > 0 else None
            right = text[i + 1] if i + 1 < len(text) else None
            if text[i] == left or text[i] == right:
                return 2
        return None
    # One missing letter (pint→print, prin→print)
    if len(text) == len(kw) - 1:
        for i in range(len(kw)):
            if text == kw[:i] + kw[i + 1 :]:
                return 2
        return None
    return None


def _is_adjacent_transpose(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    diffs = [i for i in range(len(a)) if a[i] != b[i]]
    if len(diffs) != 2:
        return False
    i, j = diffs
    return j == i + 1 and a[i] == b[j] and a[j] == b[i]


def tip_for_lexical_error(message: str, *, symbol: str | None = None) -> str:
    """Educational tip paired with a lexical error message."""
    lower = message.lower()
    if "did you mean" in lower or "misspelled" in lower or "unrecognized word" in lower:
        return (
            "Reserved keywords must be spelled exactly. "
            "Fix the highlighted word, then run Analyze again."
        )
    if "identifier" in lower and ("digit" in lower or "start" in lower):
        return (
            "Variable names must start with a letter or underscore, not a digit. "
            "Example: use `value3` or `_3rdvalue`, not `3rdvalue`."
        )
    if "unterminated string" in lower:
        return 'Close the string with a matching `"`. Example: `print("Hello");`'
    if "unterminated block comment" in lower:
        return "Close the block comment with `*/`. Example: `/* comment */`"
    if "malformed number" in lower or "invalid number" in lower:
        return (
            "Numbers may have at most one decimal point (e.g. `1.25`). "
            "Remove the extra `.` or split into separate values."
        )
    if "did you mean '&&'" in lower or symbol == "&":
        return "Logical AND is written as `&&` with two ampersands."
    if "did you mean '||'" in lower or symbol == "|":
        return "Logical OR is written as `||` with two pipes."
    if "unexpected character" in lower:
        ch = symbol
        if ch in (None, "✗", "EOF", "eps"):
            # Recover the character from: Unexpected character 'X'
            start = message.find("'")
            end = message.find("'", start + 1) if start >= 0 else -1
            ch = message[start + 1 : end] if start >= 0 and end > start else None
        if ch:
            return (
                f"Character `{ch}` is not recognized by the lexer. "
                "Remove it or replace it with a valid operator, punctuation, or literal."
            )
        return (
            "This character is not part of the PNC language. "
            "Remove it, or check for a typo near operators / literals."
        )
    return "Fix the lexical problem highlighted above, then run Analyze again."


def incomplete_eof_message(token: Token) -> str:
    """Educational message when a source ends on an incomplete operator/token."""
    lex = token.lexeme
    if token.type == TokenType.SLASH:
        return (
            f"Unexpected '{lex}' at end of input (line {token.line}, column {token.column}). "
            f"A lone '/' is not a finished statement — use '//' for a comment, "
            f"or write a full expression such as `a / b`."
        )
    if token.type == TokenType.EQUAL:
        return (
            f"Unexpected '{lex}' at end of input (line {token.line}, column {token.column}). "
            f"An assignment is incomplete — provide a value after '='."
        )
    return (
        f"Unexpected '{lex}' at end of input (line {token.line}, column {token.column}). "
        f"The operator/token is incomplete — a program cannot end here."
    )


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            ins = curr[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            curr.append(min(ins, delete, sub))
        prev = curr
    return prev[-1]


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

        if self.tokens and self.tokens[-1].type in INCOMPLETE_AT_EOF:
            raise LexerError(incomplete_eof_message(self.tokens[-1]))

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

    def _match(self, expected: str) -> bool:
        """If the current character equals expected, consume it and return True."""
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _scan_token(self) -> None:
        """Identify one token starting at the current position."""
        ch = self._advance()

        # Whitespace (including newlines) is ignored — statements end with ';'
        if ch in " \t\r\n":
            if ch == "\n":
                self.line += 1
                self.column = 1
            return

        # Single-character tokens (operators and punctuation)
        if ch == "+":
            self._add_token(TokenType.PLUSPLUS if self._match("+") else TokenType.PLUS)
            return
        if ch == "-":
            self._add_token(TokenType.MINUSMINUS if self._match("-") else TokenType.MINUS)
            return
        if ch == "*":
            self._add_token(TokenType.STAR)
            return
        if ch == "/":
            # // line comment or /* block comment */, otherwise division
            if self._match("/"):
                while not self._is_at_end() and self._peek() != "\n":
                    self._advance()
                self._add_token(TokenType.LINE_COMMENT)
                return
            if self._match("*"):
                self._block_comment()
                self._add_token(TokenType.BLOCK_COMMENT)
                return
            self._add_token(TokenType.SLASH)
            return
        if ch == "=":
            self._add_token(TokenType.EQEQ if self._match("=") else TokenType.EQUAL)
            return
        if ch == "!":
            self._add_token(TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG)
            return
        if ch == "<":
            self._add_token(TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS)
            return
        if ch == ">":
            self._add_token(TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER)
            return
        if ch == "&":
            if self._match("&"):
                self._add_token(TokenType.ANDAND)
                return
            raise LexerError(f"Unexpected character '&' at line {self.line}, column {self.column - 1} (did you mean '&&'?)")
        if ch == "|":
            if self._match("|"):
                self._add_token(TokenType.OROR)
                return
            raise LexerError(f"Unexpected character '|' at line {self.line}, column {self.column - 1} (did you mean '||'?)")
        if ch == "(":
            self._add_token(TokenType.LPAREN)
            return
        if ch == ")":
            self._add_token(TokenType.RPAREN)
            return
        if ch == "{":
            self._add_token(TokenType.LBRACE)
            return
        if ch == "}":
            self._add_token(TokenType.RBRACE)
            return
        if ch == "[":
            self._add_token(TokenType.LBRACKET)
            return
        if ch == "]":
            self._add_token(TokenType.RBRACKET)
            return
        if ch == ",":
            self._add_token(TokenType.COMMA)
            return
        if ch == ";":
            self._add_token(TokenType.SEMICOLON)
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
        raise LexerError(
            f"Unexpected character '{ch}' at line {self.line}, column {self.column - 1}"
        )

    def _block_comment(self) -> None:
        """Consume a /* ... */ block comment (Java-style)."""
        start_line = self.line
        start_col = self.column - 2  # points at the opening '/'
        while not self._is_at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()  # *
                self._advance()  # /
                return
            c = self._advance()
            if c == "\n":
                self.line += 1
                self.column = 1
        raise LexerError(f"Unterminated block comment starting at line {start_line}, column {start_col}")

    def _string(self) -> None:
        """Scan a string literal until the closing quote or an error occurs."""
        start_col = self.column - 1  # opening quote
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
        """Scan a number literal (e.g., 5, 10.5). Reject glued identifiers and extra dots."""
        start_line = self.line
        start_col = self.column - (self.current - self.start)

        # Consume the integer part
        while self._peek().isdigit():
            self._advance()
        # Optional fractional part after a dot
        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()

        # Trailing letter/underscore → invalid identifier like `3rdvalue`
        if self._peek().isalpha() or self._peek() == "_":
            while self._peek().isalnum() or self._peek() == "_":
                self._advance()
            text = self.source[self.start : self.current]
            raise LexerError(
                f"Invalid identifier '{text}' at line {start_line}, column {start_col}. "
                f"Identifiers cannot start with a digit"
            )

        # Extra decimal point → malformed number like `1.2.3` or `10.`
        if self._peek() == ".":
            self._advance()
            while self._peek().isdigit():
                self._advance()
            text = self.source[self.start : self.current]
            raise LexerError(
                f"Malformed number '{text}' at line {start_line}, column {start_col}. "
                f"A number may contain at most one decimal point"
            )

        num_text = self.source[self.start : self.current]
        self._add_token(TokenType.NUMBER, float(num_text))

    def _identifier(self) -> None:
        """Scan an identifier or a reserved keyword like 'int' or 'print'."""
        # Identifiers can contain letters, digits, and underscores
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        text = self.source[self.start : self.current]
        start_col = self.column - (self.current - self.start)

        # Map exact words to reserved keywords; otherwise it's a generic identifier
        if text in KEYWORDS:
            type_ = TokenType.RESERVED_KEYWORD
        else:
            suggestion = suggest_keyword(text)
            if suggestion is not None:
                raise LexerError(
                    f"Unrecognized word '{text}' at line {self.line}, column {start_col}. "
                    f"Did you mean '{suggestion}'?"
                )
            type_ = TokenType.IDENT

        self.tokens.append(Token(type_, text, text, self.line, start_col))
