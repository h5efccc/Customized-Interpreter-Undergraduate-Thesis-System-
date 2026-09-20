from __future__ import annotations

from dataclasses import dataclass, field

from .lexer import (
    INCOMPLETE_AT_EOF,
    KEYWORDS,
    incomplete_eof_message,
    suggest_keyword,
    tip_for_lexical_error,
)
from .tokens import Token, TokenType


@dataclass
class FAState:
    """One node in the lexical finite-automaton path."""

    id: str
    kind: str  # "start" | "normal" | "final" | "warn" | "dead"
    label: str
    accept_info: str | None = None  # e.g. "KEYWORD: int" for final states


@dataclass
class FATransition:
    """Labeled edge between two FA states."""

    from_id: str
    symbol: str
    to_id: str


@dataclass
class AutomatonTrace:
    """Character-by-character FA simulation of the lexer over source text."""

    states: list[FAState] = field(default_factory=list)
    transitions: list[FATransition] = field(default_factory=list)
    tokens: list[Token] = field(default_factory=list)
    error: str | None = None
    tip: str | None = None

    @property
    def has_dead_state(self) -> bool:
        return any(s.kind == "dead" for s in self.states)


def build_automaton_trace(source: str) -> AutomatonTrace:
    """Walk `source` the way the lexer does and record FA transitions."""
    return _FABuilder(source).run()


class _FABuilder:
    def __init__(self, source: str) -> None:
        self.source = source
        self.trace = AutomatonTrace()
        self.current = 0
        self.line = 1
        self.column = 1
        self._state_n = 0
        self._final_n = 0
        start = self._new_state("start", "q0")
        self._cursor = start.id
        self.trace.states.append(start)

    def run(self) -> AutomatonTrace:
        try:
            while not self._at_end():
                self._scan_token()
            self._reject_incomplete_tail()
            # Successful scan ends in an accepting EOF marker from the latest start-ish state
            eof_state = self._new_final("EOF")
            self._edge("EOF", eof_state.id)
            self.trace.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        except _DeadEnd as e:
            dead = FAState("DEAD", "dead", "DEAD", accept_info="lexical error")
            self.trace.states.append(dead)
            self._edge(e.symbol, dead.id)
            self.trace.error = e.message
            self.trace.tip = e.tip or tip_for_lexical_error(e.message, symbol=e.symbol)
            if e.error_lexeme is not None:
                self.trace.tokens.append(
                    Token(
                        TokenType.ERROR,
                        e.error_lexeme,
                        None,
                        e.error_line or self.line,
                        e.error_column or max(1, self.column - 1),
                    )
                )
        return self.trace

    def _reject_incomplete_tail(self) -> None:
        """Send trailing incomplete operators (e.g. `;/`) into the dead state."""
        tokens = self.trace.tokens
        if not tokens:
            return
        last = tokens[-1]
        if last.type not in INCOMPLETE_AT_EOF:
            return
        message = incomplete_eof_message(last)
        tip = None
        if last.type == TokenType.SLASH:
            tip = (
                "After a finished statement ending with `;`, do not leave a lone `/`. "
                "Either remove it, start a comment with `//`, or write a full expression."
            )
        elif last.type == TokenType.EQUAL:
            tip = "Finish the assignment with a value, e.g. `int a = 10;`"
        else:
            tip = f"Token `{last.lexeme}` cannot end the program. Complete the expression or remove the extra operator."
        raise _DeadEnd(
            "✗",
            message,
            tip=tip,
            error_lexeme=last.lexeme,
            error_line=last.line,
            error_column=last.column,
        )

    # --- state helpers ---

    def _new_state(self, kind: str, label: str | None = None) -> FAState:
        sid = f"q{self._state_n}"
        self._state_n += 1
        return FAState(sid, kind, label or sid)

    def _new_final(self, accept_info: str) -> FAState:
        self._final_n += 1
        sid = f"q{self._state_n}"
        self._state_n += 1
        # Keep q-numbering, mark as final (double circle in the diagram)
        return FAState(sid, "final", sid, accept_info=accept_info)

    def _edge(self, symbol: str, to_id: str) -> None:
        self.trace.transitions.append(FATransition(self._cursor, symbol, to_id))
        self._cursor = to_id

    def _step(self, ch: str, *, kind: str = "normal") -> FAState:
        state = self._new_state(kind)
        self.trace.states.append(state)
        self._edge(_display_char(ch), state.id)
        return state

    def _accept(self, ch: str | None, accept_info: str) -> FAState:
        state = self._new_final(accept_info)
        self.trace.states.append(state)
        if ch is not None:
            self._edge(_display_char(ch), state.id)
        else:
            # Acceptance without consuming (should be rare); use eps
            self._edge("eps", state.id)
        return state

    def _return_to_start(self) -> None:
        """After a final state, open a fresh start node for the next lexeme."""
        start = self._new_state("start")
        self.trace.states.append(start)
        self._edge("eps", start.id)

    # --- source cursor (mirrors Lexer) ---

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _peek(self) -> str:
        if self._at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _add_token(self, type_: str, lexeme: str, value=None, *, line: int, column: int) -> None:
        self.trace.tokens.append(Token(type_, lexeme, value, line, column))

    def _dead(
        self,
        ch: str,
        message: str,
        *,
        tip: str | None = None,
        error_lexeme: str | None = None,
        error_line: int | None = None,
        error_column: int | None = None,
    ) -> None:
        raise _DeadEnd(
            _display_char(ch),
            message,
            tip=tip or tip_for_lexical_error(message, symbol=ch),
            error_lexeme=error_lexeme if error_lexeme is not None else ch,
            error_line=error_line if error_line is not None else self.line,
            error_column=error_column if error_column is not None else max(1, self.column - 1),
        )

    # --- scanning ---

    def _scan_token(self) -> None:
        ch = self._advance()

        # Whitespace: stay conceptually at start (no FA noise)
        if ch in " \t\r\n":
            if ch == "\n":
                self.line += 1
                self.column = 1
            return

        start_line, start_col = self.line, self.column - 1
        lexeme_start = self.current - 1

        if ch == "+":
            if self._match("+"):
                self._step(ch)
                self._accept("+", "PLUSPLUS")
                self._add_token(TokenType.PLUSPLUS, "++", line=start_line, column=start_col)
            else:
                self._accept(ch, "PLUS")
                self._add_token(TokenType.PLUS, "+", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "-":
            if self._match("-"):
                self._step(ch)
                self._accept("-", "MINUSMINUS")
                self._add_token(TokenType.MINUSMINUS, "--", line=start_line, column=start_col)
            else:
                self._accept(ch, "MINUS")
                self._add_token(TokenType.MINUS, "-", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "*":
            self._accept(ch, "STAR")
            self._add_token(TokenType.STAR, "*", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "/":
            if self._match("/"):
                self._step(ch)
                while not self._at_end() and self._peek() != "\n":
                    self._step(self._advance())
                self._mark_final("LINE_COMMENT")
                text = self.source[lexeme_start:self.current]
                self._add_token(TokenType.LINE_COMMENT, text, line=start_line, column=start_col)
                self._return_to_start()
                return
            if self._match("*"):
                self._step(ch)
                self._step("*")
                self._block_comment(start_line, start_col, lexeme_start)
                return
            self._accept(ch, "SLASH")
            self._add_token(TokenType.SLASH, "/", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "=":
            if self._match("="):
                self._step(ch)
                self._accept("=", "EQEQ")
                self._add_token(TokenType.EQEQ, "==", line=start_line, column=start_col)
            else:
                self._accept(ch, "EQUAL")
                self._add_token(TokenType.EQUAL, "=", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "!":
            if self._match("="):
                self._step(ch)
                self._accept("=", "BANG_EQUAL")
                self._add_token(TokenType.BANG_EQUAL, "!=", line=start_line, column=start_col)
            else:
                self._accept(ch, "BANG")
                self._add_token(TokenType.BANG, "!", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "<":
            if self._match("="):
                self._step(ch)
                self._accept("=", "LESS_EQUAL")
                self._add_token(TokenType.LESS_EQUAL, "<=", line=start_line, column=start_col)
            else:
                self._accept(ch, "LESS")
                self._add_token(TokenType.LESS, "<", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == ">":
            if self._match("="):
                self._step(ch)
                self._accept("=", "GREATER_EQUAL")
                self._add_token(TokenType.GREATER_EQUAL, ">=", line=start_line, column=start_col)
            else:
                self._accept(ch, "GREATER")
                self._add_token(TokenType.GREATER, ">", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "&":
            if self._match("&"):
                self._step(ch)
                self._accept("&", "ANDAND")
                self._add_token(TokenType.ANDAND, "&&", line=start_line, column=start_col)
                self._return_to_start()
                return
            self._step(ch)
            self._mark_warn("INCOMPLETE &&")
            self._dead(
                "✗",
                f"Unexpected character '&' at line {self.line}, column {self.column - 1} (did you mean '&&'?)",
                error_lexeme="&",
            )
        if ch == "|":
            if self._match("|"):
                self._step(ch)
                self._accept("|", "OROR")
                self._add_token(TokenType.OROR, "||", line=start_line, column=start_col)
                self._return_to_start()
                return
            self._step(ch)
            self._mark_warn("INCOMPLETE ||")
            self._dead(
                "✗",
                f"Unexpected character '|' at line {self.line}, column {self.column - 1} (did you mean '||'?)",
                error_lexeme="|",
            )
        if ch == "(":
            self._accept(ch, "LPAREN")
            self._add_token(TokenType.LPAREN, "(", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == ")":
            self._accept(ch, "RPAREN")
            self._add_token(TokenType.RPAREN, ")", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "{":
            self._accept(ch, "LBRACE")
            self._add_token(TokenType.LBRACE, "{", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "}":
            self._accept(ch, "RBRACE")
            self._add_token(TokenType.RBRACE, "}", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "[":
            self._accept(ch, "LBRACKET")
            self._add_token(TokenType.LBRACKET, "[", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == "]":
            self._accept(ch, "RBRACKET")
            self._add_token(TokenType.RBRACKET, "]", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == ",":
            self._accept(ch, "COMMA")
            self._add_token(TokenType.COMMA, ",", line=start_line, column=start_col)
            self._return_to_start()
            return
        if ch == ";":
            self._accept(ch, "SEMICOLON")
            self._add_token(TokenType.SEMICOLON, ";", line=start_line, column=start_col)
            self._return_to_start()
            return

        if ch == '"':
            self._string(start_line, start_col, lexeme_start)
            return
        if ch.isdigit():
            self._number(ch, start_line, start_col, lexeme_start)
            return
        if ch.isalpha() or ch == "_":
            self._identifier(ch, start_line, start_col, lexeme_start)
            return

        self._step(ch)
        self._mark_warn(f"ILLEGAL: {ch}")
        self._dead(
            "✗",
            f"Unexpected character '{ch}' at line {start_line}, column {start_col}",
            error_lexeme=ch,
            error_line=start_line,
            error_column=start_col,
        )

    def _block_comment(self, start_line: int, start_col: int, lexeme_start: int) -> None:
        while not self._at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._step(self._advance())
                self._accept("/", "BLOCK_COMMENT")
                text = self.source[lexeme_start:self.current]
                self._add_token(TokenType.BLOCK_COMMENT, text, line=start_line, column=start_col)
                self._return_to_start()
                return
            c = self._advance()
            self._step(c)
            if c == "\n":
                self.line += 1
                self.column = 1
        text = self.source[lexeme_start:self.current]
        self._mark_warn("UNTERMINATED COMMENT")
        self._dead(
            "EOF",
            f"Unterminated block comment starting at line {start_line}, column {start_col}",
            error_lexeme=text or "/*",
            error_line=start_line,
            error_column=start_col,
        )

    def _string(self, start_line: int, start_col: int, lexeme_start: int) -> None:
        self._step('"')
        value_chars: list[str] = []
        while not self._at_end() and self._peek() != '"':
            c = self._advance()
            if c == "\n":
                self._step(c)
                text = self.source[lexeme_start:self.current]
                self._mark_warn("UNTERMINATED STRING")
                self._dead(
                    "✗",
                    f"Unterminated string at line {start_line}, column {start_col}",
                    error_lexeme=text.rstrip("\n") or '"',
                    error_line=start_line,
                    error_column=start_col,
                )
            self._step(c)
            value_chars.append(c)
        if self._at_end():
            text = self.source[lexeme_start:self.current]
            self._mark_warn("UNTERMINATED STRING")
            self._dead(
                "EOF",
                f"Unterminated string at line {start_line}, column {start_col}",
                error_lexeme=text or '"',
                error_line=start_line,
                error_column=start_col,
            )
        self._advance()
        self._accept('"', "STRING")
        text = self.source[lexeme_start:self.current]
        self._add_token(TokenType.STRING, text, "".join(value_chars), line=start_line, column=start_col)
        self._return_to_start()

    def _mark_final(self, accept_info: str) -> None:
        """Promote the current state to an accepting (final) state."""
        for state in reversed(self.trace.states):
            if state.id == self._cursor:
                state.kind = "final"
                state.accept_info = accept_info
                self._final_n += 1
                return

    def _mark_warn(self, accept_info: str) -> None:
        """Promote the current state to a warning state (near-miss / rejected word)."""
        for state in reversed(self.trace.states):
            if state.id == self._cursor:
                state.kind = "warn"
                state.accept_info = accept_info
                return

    def _number(self, first: str, start_line: int, start_col: int, lexeme_start: int) -> None:
        self._step(first)
        while self._peek().isdigit():
            self._step(self._advance())
        if self._peek() == "." and self._peek_next().isdigit():
            self._step(self._advance())
            while self._peek().isdigit():
                self._step(self._advance())

        # Digit-leading identifier such as `3rdvalue`
        if self._peek().isalpha() or self._peek() == "_":
            while self._peek().isalnum() or self._peek() == "_":
                self._step(self._advance())
            text = self.source[lexeme_start:self.current]
            self._mark_warn(f"INVALID IDENT: {text}")
            self._dead(
                "✗",
                (
                    f"Invalid identifier '{text}' at line {start_line}, column {start_col}. "
                    f"Identifiers cannot start with a digit"
                ),
                error_lexeme=text,
                error_line=start_line,
                error_column=start_col,
            )

        # Extra decimal point such as `1.2.3` or trailing `.`
        if self._peek() == ".":
            self._step(self._advance())
            while self._peek().isdigit():
                self._step(self._advance())
            text = self.source[lexeme_start:self.current]
            self._mark_warn(f"BAD NUMBER: {text}")
            self._dead(
                "✗",
                (
                    f"Malformed number '{text}' at line {start_line}, column {start_col}. "
                    f"A number may contain at most one decimal point"
                ),
                error_lexeme=text,
                error_line=start_line,
                error_column=start_col,
            )

        text = self.source[lexeme_start:self.current]
        self._mark_final("NUMBER")
        self._add_token(TokenType.NUMBER, text, float(text), line=start_line, column=start_col)
        self._return_to_start()

    def _identifier(self, first: str, start_line: int, start_col: int, lexeme_start: int) -> None:
        # q0 -i-> q1 -n-> q2 -t-> FINAL  (as in the user's example)
        self._step(first)
        while self._peek().isalnum() or self._peek() == "_":
            self._step(self._advance())
        text = self.source[lexeme_start:self.current]
        if text in KEYWORDS:
            self._mark_final(f"KEYWORD: {text}")
            self._add_token(
                TokenType.RESERVED_KEYWORD, text, text, line=start_line, column=start_col
            )
            self._return_to_start()
            return

        suggestion = suggest_keyword(text)
        if suggestion is not None:
            # Keep the scanned path visible, then reject into DEAD.
            self._mark_warn(f"UNKNOWN: {text}")
            if suggestion == "print":
                example = f"`{suggestion}(a);`"
            elif suggestion == "while":
                example = "`while (i < 10) { ... }`"
            elif suggestion == "for":
                example = "`for (int i = 0; i < 10; i++) { ... }`"
            elif suggestion == "do":
                example = "`do { ... } while (cond);`"
            elif suggestion in {"if", "else", "true", "false"}:
                example = f"`{suggestion} (...)`" if suggestion == "if" else f"`{suggestion}`"
            else:
                example = f"`{suggestion} a = 10;`"
            tip = (
                f"Unrecognized word '{text}'. This looks like a misspelled keyword. "
                f"Did you mean `{suggestion}`? Example: {example}"
            )
            raise _DeadEnd(
                "✗",
                (
                    f"Unrecognized word '{text}' at line {start_line}, column {start_col}. "
                    f"Did you mean '{suggestion}'?"
                ),
                tip=tip,
                error_lexeme=text,
                error_line=start_line,
                error_column=start_col,
            )

        self._mark_final(f"IDENT: {text}")
        self._add_token(TokenType.IDENT, text, text, line=start_line, column=start_col)
        self._return_to_start()


class _DeadEnd(Exception):
    def __init__(
        self,
        symbol: str,
        message: str,
        *,
        tip: str | None = None,
        error_lexeme: str | None = None,
        error_line: int | None = None,
        error_column: int | None = None,
    ) -> None:
        self.symbol = symbol
        self.message = message
        self.tip = tip
        self.error_lexeme = error_lexeme
        self.error_line = error_line
        self.error_column = error_column
        super().__init__(message)


def _display_char(ch: str) -> str:
    if ch == " ":
        return "␣"
    if ch == "\t":
        return "\\t"
    if ch == "\n":
        return "\\n"
    if ch == "\r":
        return "\\r"
    if ch == "\0":
        return "EOF"
    return ch
