from __future__ import annotations

import re
import threading
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import filedialog, messagebox, ttk

from .analysis import AnalysisResult, analyze_source
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
from .automaton import AutomatonTrace, FAState
from .lexer import KEYWORDS
from .tokens import Token, TokenType


# --- Theme palettes ---
@dataclass(frozen=True)
class UiTheme:
    """Visual palette for the simulator window."""

    key: str
    label: str
    bg: str
    panel: str
    accent: str
    accent_hover: str
    success: str
    success_hover: str
    error: str
    muted: str
    border: str
    text: str
    text_strong: str
    code_bg: str
    code_fg: str
    gutter_bg: str
    gutter_fg: str
    canvas_bg: str
    tip_bg: str
    tip_fg: str
    status_bg: str
    status_fg: str
    header_sub: str
    header_arrow: str
    stage_idle_bg: str
    stage_idle_fg: str
    stage_pass_bg: str
    stage_pass_fg: str
    stage_fail_bg: str
    stage_fail_fg: str
    stream_bg: str
    summary_bg: str
    zoom_btn_bg: str
    select_bg: str
    insert_bg: str
    syn_keyword: str
    syn_type: str
    syn_string: str
    syn_number: str
    syn_comment: str
    syn_ident: str
    syn_operator: str
    syn_bool: str
    # FA / diagram node fills (readable on both light and dark canvases)
    fa_start: str = "#dbeafe"
    fa_normal: str = "#ffffff"
    fa_final: str = "#bbf7d0"
    fa_warn: str = "#fde68a"
    fa_dead: str = "#fecaca"
    fa_outline: str = "#111827"
    fa_label: str = "#111827"
    diag_fill: str = "#ffffff"
    diag_outline: str = "#111827"
    diag_text: str = "#111827"
    diag_edge: str = "#64748b"
    tree_error_bg: str = "#fee2e2"
    tree_error_fg: str = "#991b1b"
    heading_bg: str = "#e2e8f0"
    heading_fg: str = "#334155"
    scroll_bg: str = "#cbd5e1"
    scroll_trough: str = "#f1f5f9"
    scroll_arrow: str = "#334155"
    check_select: str = "#ffffff"


def _theme_default() -> UiTheme:
    return UiTheme(
        key="default",
        label="Default UI",
        bg="#f0f2f5",
        panel="#ffffff",
        accent="#2563eb",
        accent_hover="#1d4ed8",
        success="#16a34a",
        success_hover="#047857",
        error="#dc2626",
        muted="#64748b",
        border="#e2e8f0",
        text="#475569",
        text_strong="#334155",
        code_bg="#1e293b",
        code_fg="#e2e8f0",
        gutter_bg="#0f172a",
        gutter_fg="#64748b",
        canvas_bg="#fafafa",
        tip_bg="#fff7ed",
        tip_fg="#9a3412",
        status_bg="#e2e8f0",
        status_fg="#475569",
        header_sub="#bfdbfe",
        header_arrow="#93c5fd",
        stage_idle_bg="#dbeafe",
        stage_idle_fg="#64748b",
        stage_pass_bg="#bbf7d0",
        stage_pass_fg="#166534",
        stage_fail_bg="#fecaca",
        stage_fail_fg="#991b1b",
        stream_bg="#f8fafc",
        summary_bg="#f8fafc",
        zoom_btn_bg="#e2e8f0",
        select_bg="#475569",
        insert_bg="#ffffff",
        syn_keyword="#c792ea",
        syn_type="#82aaff",
        syn_string="#c3e88d",
        syn_number="#f78c6c",
        syn_comment="#546e7a",
        syn_ident="#89ddff",
        syn_operator="#89ddff",
        syn_bool="#f07178",
        heading_bg="#e2e8f0",
        heading_fg="#334155",
        scroll_bg="#cbd5e1",
        scroll_trough="#f1f5f9",
        scroll_arrow="#334155",
        check_select="#ffffff",
    )


def _theme_dark() -> UiTheme:
    return UiTheme(
        key="dark",
        label="Dark Mode",
        bg="#0b1220",
        panel="#111827",
        accent="#3b82f6",
        accent_hover="#2563eb",
        success="#22c55e",
        success_hover="#16a34a",
        error="#f87171",
        muted="#94a3b8",
        border="#1f2937",
        text="#cbd5e1",
        text_strong="#e2e8f0",
        code_bg="#020617",
        code_fg="#e2e8f0",
        gutter_bg="#020617",
        gutter_fg="#64748b",
        canvas_bg="#0f172a",
        tip_bg="#422006",
        tip_fg="#fdba74",
        status_bg="#020617",
        status_fg="#94a3b8",
        header_sub="#93c5fd",
        header_arrow="#60a5fa",
        stage_idle_bg="#1e3a5f",
        stage_idle_fg="#93c5fd",
        stage_pass_bg="#14532d",
        stage_pass_fg="#86efac",
        stage_fail_bg="#7f1d1d",
        stage_fail_fg="#fecaca",
        stream_bg="#0f172a",
        summary_bg="#0f172a",
        zoom_btn_bg="#1f2937",
        select_bg="#334155",
        insert_bg="#e2e8f0",
        syn_keyword="#c792ea",
        syn_type="#82aaff",
        syn_string="#c3e88d",
        syn_number="#f78c6c",
        syn_comment="#64748b",
        syn_ident="#89ddff",
        syn_operator="#7dd3fc",
        syn_bool="#f07178",
        fa_start="#1e3a5f",
        fa_normal="#1f2937",
        fa_final="#14532d",
        fa_warn="#78350f",
        fa_dead="#7f1d1d",
        fa_outline="#e2e8f0",
        fa_label="#f8fafc",
        diag_fill="#1f2937",
        diag_outline="#94a3b8",
        diag_text="#e2e8f0",
        diag_edge="#64748b",
        tree_error_bg="#7f1d1d",
        tree_error_fg="#fecaca",
        heading_bg="#1f2937",
        heading_fg="#e2e8f0",
        scroll_bg="#334155",
        scroll_trough="#0f172a",
        scroll_arrow="#cbd5e1",
        check_select="#0f172a",
    )


THEMES: dict[str, UiTheme] = {
    "default": _theme_default(),
    "dark": _theme_dark(),
}

# Back-compat aliases used during initial widget construction (then overridden by _apply_theme).
_DEFAULT = THEMES["default"]
BG = _DEFAULT.bg
PANEL = _DEFAULT.panel
ACCENT = _DEFAULT.accent
ACCENT_HOVER = _DEFAULT.accent_hover
SUCCESS = _DEFAULT.success
ERROR = _DEFAULT.error
MUTED = _DEFAULT.muted
BORDER = _DEFAULT.border
CODE_BG = _DEFAULT.code_bg
CODE_FG = _DEFAULT.code_fg
GUTTER_BG = _DEFAULT.gutter_bg
GUTTER_FG = _DEFAULT.gutter_fg
SYN_KEYWORD = _DEFAULT.syn_keyword
SYN_TYPE = _DEFAULT.syn_type
SYN_STRING = _DEFAULT.syn_string
SYN_NUMBER = _DEFAULT.syn_number
SYN_COMMENT = _DEFAULT.syn_comment
SYN_IDENT = _DEFAULT.syn_ident
SYN_OPERATOR = _DEFAULT.syn_operator
SYN_BOOL = _DEFAULT.syn_bool

_ABOUT_MANUAL = """\
PNC LANGUAGE ANALYSIS SIMULATOR
User Manual / FAQ
================================

WHAT IS THIS SOFTWARE?
----------------------
This is an instructional simulation tool for learning how compilers begin:
lexical analysis (scanner) and syntax analysis (parser).

You write programs in the educational PNC language (.pnc files). The simulator
shows how source text becomes tokens, how those tokens are checked against a
grammar, and how an Abstract Syntax Tree (AST) is built. Optional execution
lets you see runtime output, but teaching analysis is the primary goal.

Think of this window as the "user manual sticker" on a new appliance — it tells
you what the machine can do, what it cannot do, and which knobs are available.


WHAT IT CAN DO
--------------
• Lexical analysis — tokenize source into keywords, identifiers, literals, operators
• Syntax analysis — validate statements against a context-free grammar
• Educational error tips — misspellings, illegal characters, malformed literals,
  missing semicolons, unmatched brackets, empty conditions, and similar mistakes
• Finite Automaton (FA) diagram of how lexemes were recognized (including Warn/Dead)
• Token table + token stream views
• AST tree view and AST diagram view
• Optional program execution (print / variables / control flow)
• Themes: Default, Dark, and optional Minimalism layout


LANGUAGE FEATURES SUPPORTED (CAN)
---------------------------------
Data types:
  int, double, string, boolean
  one-dimensional arrays: int[], double[], string[], boolean[]

Keywords recognized:
  int, double, string, boolean, print, if, else, while, for, do, true, false

Statements:
  typed variable declaration          int x = 10;
  reassignment after declaration      x = 20;
  print                               print(x);
  if / else / else if                 if (cond) { ... } else { ... }
  while                               while (cond) { ... }
  do-while                            do { ... } while (cond);
  for                                 for (init; cond; update) { ... }
  increment / decrement               i++;  ++i;  i--;  --i;
  array declare / index / update      int[] a = {1,2,3};  a[0]++;

Operators:
  Arithmetic:   +  -  *  /
  Comparison:   ==  !=  <  <=  >  >=
  Logical:      !  &&  ||
  Update:       ++  --
  Assignment:   =
  Grouping:     ( )  [ ]  { }
  Punctuation:  ;  ,

Comments (Java-style):
  // line comment
  /* block comment */


WHAT IT CANNOT DO (LIMITATIONS / OUT OF SCOPE)
----------------------------------------------
• Object-oriented programming (classes, objects, inheritance, methods)
• Functions / procedures (other than the built-in print)
• Advanced data structures (linked lists, trees, stacks, queues, maps, graphs)
• Multi-dimensional arrays (int[][] is not supported)
• break / continue
• Pointers, references, dynamic memory management
• File I/O, networking, concurrency, GUIs from PNC code
• Generics, templates, packages/modules, imports
• Multi-line string literals
• if / else / loops without curly braces { }
• A full general-purpose language runtime

These limits keep the tool focused on introductory lexical & syntax analysis.


HOW TO USE THE SIMULATOR
------------------------
1. Type or Open a .pnc file in the Source Code panel
2. Click Analyze — see Tokens, AST, and Summary
3. Click Analyze + Execute — also run the optional execution phase
4. Switch Tokens view between Table and Diagram (FA)
5. Switch AST view between Tree and Diagram
6. Use UI Style (top) to choose Default or Dark
7. Enable Minimalism for a cleaner, less chrome-heavy layout
8. Open this manual anytime with "Know more about this software"


ERROR REPORTING PHILOSOPHY
--------------------------
Lexical mistakes (misspelled keywords like primt, identifiers starting with digits,
illegal characters like $, unclosed strings, malformed numbers like 1.2.3) are
reported in the Tokens tab and reflected in the FA diagram (Warn / Dead states).

Syntax mistakes (missing ;, unmatched brackets, wrong statement shape, empty
control conditions) are reported in the AST tab with recovery tips so you know
what to fix.


TIPS
----
• Prefer Java-inspired style: types first, semicolons, braces around bodies
• Identifiers must start with a letter or underscore: value1  OK   1value  BAD
• Array initializers need braces: int[] a = {1, 2, 3};
• do-while must end with a semicolon after the condition
• Infinite loops (e.g. while (true) { print("hi"); }) are stopped by a runtime
  safety limit so the simulator does not freeze or crash

For the formal grammar, see GRAMMAR.md and SYNTAX_NOTES.md in the project folder.
"""

_TYPE_KEYWORDS = frozenset({"int", "double", "string", "boolean"})
_BOOL_KEYWORDS = frozenset({"true", "false"})
_CONTROL_KEYWORDS = frozenset({"print", "if", "else", "while", "for", "do"})

# Soft tokenizer for live highlighting (tolerant of incomplete source while typing).
_HIGHLIGHT_RE = re.compile(
    r"(?P<line_comment>//[^\n]*)"
    r"|(?P<block_comment>/\*.*?(?:\*/|$))"
    r'|(?P<string>"[^"\n]*(?:"|$))'
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
    r"|(?P<ident>\b[A-Za-z_][A-Za-z0-9_]*\b)"
    r"|(?P<operator>\+\+|--|==|!=|<=|>=|&&|\|\||[+\-*/%<>=!;(){}\[\],])",
    re.DOTALL,
)

# Diagram layout
_DIAG_H_GAP = 36
_DIAG_V_GAP = 72
_DIAG_PAD_X = 18
_DIAG_PAD_Y = 10
_DIAG_MARGIN = 40
_DIAG_FONT = ("Segoe UI", 10)
_DIAG_EDGE_FONT = ("Segoe UI", 8)
_DIAG_ZOOM_MIN = 0.4
_DIAG_ZOOM_MAX = 2.5
_DIAG_ZOOM_STEP = 1.15

# FA diagram layout
_FA_RADIUS = 18
_FA_GAP = 56
_FA_ROW_GAP = 90
_FA_MARGIN = 36
_FA_WRAP = 8

_BINARY_OP_NAMES = {
    "+": "Addition",
    "-": "Subtraction",
    "*": "Multiplication",
    "/": "Division",
    "%": "Modulo",
    "==": "Equality",
    "!=": "Inequality",
    "<": "LessThan",
    ">": "GreaterThan",
    "<=": "LessEqual",
    ">=": "GreaterEqual",
    "&&": "LogicalAnd",
    "||": "LogicalOr",
}


@dataclass
class _DiagramNode:
    label: str
    children: list[tuple[str, _DiagramNode]] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    box_w: float = 0.0
    box_h: float = 0.0
    subtree_w: float = 0.0


class SimulatorApp(tk.Tk):
    def __init__(self, initial_source: str = "", initial_path: str | None = None) -> None:
        super().__init__()
        self.title("PNC Language Analysis Simulator")
        self.geometry("1180x720")
        self.minsize(960, 600)

        self.theme = THEMES["default"]
        self._theme_key = tk.StringVar(value="default")
        self._minimal_var = tk.BooleanVar(value=False)
        self._stage_pass_state: tuple[int | None, int | None] = (None, None)

        self.configure(bg=self.theme.bg)

        self._current_path = initial_path
        self._stage_labels: list[tk.Label] = []
        self._stage_arrows: list[tk.Label] = []
        self._ast_statements: list[Stmt] = []
        self._ast_view_mode = tk.StringVar(value="tree")
        self._diagram_zoom = 1.0
        self._zoom_label_var = tk.StringVar(value="100%")
        self._token_view_mode = tk.StringVar(value="table")
        self._fa_trace: AutomatonTrace | None = None
        self._fa_zoom = 1.0
        self._fa_zoom_label_var = tk.StringVar(value="100%")
        self._analysis_busy = False
        self._ttk_style = ttk.Style(self)
        try:
            self._ttk_style.theme_use("clam")
        except tk.TclError:
            pass

        self._build_ui()
        self._apply_theme()
        if initial_source:
            self.source_text.insert("1.0", initial_source)
            if initial_path:
                self.status_var.set(f"Loaded: {initial_path}")
        else:
            self._load_default_example()
        self._refresh_editor_chrome()

    def _build_ui(self) -> None:
        self._build_header()
        self._build_toolbar()
        self._build_main_panels()
        self._build_status_bar()

    def _build_header(self) -> None:
        t = self.theme
        self._header = tk.Frame(self, bg=t.accent, padx=16, pady=12)
        self._header.pack(fill=tk.X)

        top_row = tk.Frame(self._header, bg=t.accent)
        top_row.pack(fill=tk.X)
        self._header_top = top_row

        left_titles = tk.Frame(top_row, bg=t.accent)
        left_titles.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._header_titles = left_titles

        self._header_title = tk.Label(
            left_titles,
            text="PNC Language Analysis Simulator",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg=t.accent,
        )
        self._header_title.pack(anchor=tk.W)

        self._header_subtitle = tk.Label(
            left_titles,
            text="Scanner-Parser Architecture  |  Lexical & Syntax Analysis Demonstration",
            font=("Segoe UI", 10),
            fg=t.header_sub,
            bg=t.accent,
        )
        self._header_subtitle.pack(anchor=tk.W, pady=(2, 0))

        controls = tk.Frame(top_row, bg=t.accent)
        controls.pack(side=tk.RIGHT, anchor=tk.N)
        self._header_controls = controls

        self._ui_style_label = tk.Label(
            controls, text="UI Style:", font=("Segoe UI", 9), fg="white", bg=t.accent
        )
        self._ui_style_label.pack(side=tk.LEFT, padx=(0, 4))

        self._theme_display = tk.StringVar(value="Default UI")
        self._theme_combo = ttk.Combobox(
            controls,
            textvariable=self._theme_display,
            values=("Default UI", "Dark Mode"),
            state="readonly",
            width=12,
            font=("Segoe UI", 9),
        )
        self._theme_combo.pack(side=tk.LEFT, padx=(0, 8))
        self._theme_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_theme_changed())

        self._minimal_check = tk.Checkbutton(
            controls,
            text="Minimalism",
            variable=self._minimal_var,
            command=self._on_theme_changed,
            font=("Segoe UI", 9),
            fg="white",
            bg=t.accent,
            activebackground=t.accent,
            activeforeground="white",
            selectcolor=t.check_select,
            highlightthickness=0,
            cursor="hand2",
        )
        self._minimal_check.pack(side=tk.LEFT, padx=(0, 10))

        self._about_btn = tk.Button(
            controls,
            text="Know more about this software",
            command=self._show_about,
            font=("Segoe UI", 9),
            padx=10,
            pady=3,
            cursor="hand2",
            bg="white",
            fg=t.accent,
            activebackground="#eff6ff",
            activeforeground=t.accent,
            relief=tk.FLAT,
        )
        self._about_btn.pack(side=tk.LEFT)

        self._flow = tk.Frame(self._header, bg=t.accent)
        self._flow.pack(anchor=tk.W, pady=(8, 0))
        stages = ["Source", "Lexer", "Parser", "AST", "Summary"]
        for i, name in enumerate(stages):
            if i > 0:
                arrow = tk.Label(
                    self._flow, text=" --> ", font=("Segoe UI", 9), fg=t.header_arrow, bg=t.accent
                )
                arrow.pack(side=tk.LEFT)
                self._stage_arrows.append(arrow)
            lbl = tk.Label(
                self._flow,
                text=f" {name} ",
                font=("Segoe UI", 9, "bold"),
                fg=t.stage_idle_fg,
                bg=t.stage_idle_bg,
                padx=6,
                pady=2,
            )
            lbl.pack(side=tk.LEFT)
            self._stage_labels.append(lbl)

    def _build_toolbar(self) -> None:
        t = self.theme
        self._toolbar = tk.Frame(
            self, bg=t.panel, padx=12, pady=8, highlightbackground=t.border, highlightthickness=1
        )
        self._toolbar.pack(fill=tk.X, padx=12, pady=(12, 0))

        btn_style = {"font": ("Segoe UI", 9), "padx": 12, "pady": 4, "cursor": "hand2"}

        self._btn_open = tk.Button(
            self._toolbar, text="Open .pnc File", command=self._open_file, bg=t.panel, **btn_style
        )
        self._btn_open.pack(side=tk.LEFT, padx=(0, 6))
        self._btn_analyze = tk.Button(
            self._toolbar,
            text="Analyze",
            command=lambda: self._run_analysis(False),
            bg=t.accent,
            fg="white",
            activebackground=t.accent_hover,
            activeforeground="white",
            **btn_style,
        )
        self._btn_analyze.pack(side=tk.LEFT, padx=(0, 6))
        self._btn_execute = tk.Button(
            self._toolbar,
            text="Analyze + Execute",
            command=lambda: self._run_analysis(True),
            bg=t.success,
            fg="white",
            activebackground=t.success_hover,
            activeforeground="white",
            **btn_style,
        )
        self._btn_execute.pack(side=tk.LEFT, padx=(0, 6))
        self._btn_clear = tk.Button(
            self._toolbar, text="Clear", command=self._clear_all, bg=t.panel, **btn_style
        )
        self._btn_clear.pack(side=tk.LEFT)

    def _build_main_panels(self) -> None:
        t = self.theme
        self._paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6, bg=t.border, bd=0)
        self._paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # --- Left: Source editor ---
        self._left_panel = tk.Frame(self._paned, bg=t.panel, highlightbackground=t.border, highlightthickness=1)
        self._paned.add(self._left_panel, minsize=340)

        self._source_label = tk.Label(
            self._left_panel,
            text="  Source Code (.pnc)",
            font=("Segoe UI", 10, "bold"),
            bg=t.panel,
            fg=t.text_strong,
            anchor=tk.W,
        )
        self._source_label.pack(fill=tk.X, padx=8, pady=(8, 4))

        self._editor_frame = tk.Frame(self._left_panel, bg=t.code_bg)
        self._editor_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.line_numbers = tk.Text(
            self._editor_frame,
            width=4,
            padx=6,
            pady=8,
            takefocus=0,
            borderwidth=0,
            highlightthickness=0,
            background=t.gutter_bg,
            foreground=t.gutter_fg,
            font=("Consolas", 11),
            state=tk.DISABLED,
            wrap=tk.NONE,
            cursor="arrow",
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.source_text = tk.Text(
            self._editor_frame,
            wrap=tk.NONE,
            font=("Consolas", 11),
            bg=t.code_bg,
            fg=t.code_fg,
            insertbackground=t.insert_bg,
            selectbackground=t.select_bg,
            padx=8,
            pady=8,
            undo=True,
            borderwidth=0,
            highlightthickness=0,
        )
        yscroll = ttk.Scrollbar(self._editor_frame, orient=tk.VERTICAL, command=self._sync_scroll)
        self._editor_yscroll = yscroll
        self.source_text.configure(yscrollcommand=self._on_text_yscroll)
        self.source_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._configure_syntax_tags()
        self.source_text.bind("<<Modified>>", self._on_source_modified)
        self.source_text.bind("<MouseWheel>", self._on_mousewheel)
        self.line_numbers.bind("<MouseWheel>", self._on_mousewheel)
        # Linux scroll bindings
        self.source_text.bind("<Button-4>", self._on_mousewheel)
        self.source_text.bind("<Button-5>", self._on_mousewheel)
        self.line_numbers.bind("<Button-4>", self._on_mousewheel)
        self.line_numbers.bind("<Button-5>", self._on_mousewheel)

        # --- Right: Results notebook ---
        self._right_panel = tk.Frame(self._paned, bg=t.panel, highlightbackground=t.border, highlightthickness=1)
        self._paned.add(self._right_panel, minsize=480)

        self.notebook = ttk.Notebook(self._right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._build_tokens_tab()
        self._build_ast_tab()
        self._build_summary_tab()
        self._build_output_tab()

    def _build_tokens_tab(self) -> None:
        t = self.theme
        self._tokens_frame = tk.Frame(self.notebook, bg=t.panel)
        self.notebook.add(self._tokens_frame, text="  Tokens  ")

        self.lexical_status = tk.Label(
            self._tokens_frame,
            text="Lexical analysis: waiting...",
            font=("Segoe UI", 10),
            bg=t.panel,
            fg=t.muted,
            anchor=tk.W,
        )
        self.lexical_status.pack(fill=tk.X, padx=10, pady=(8, 2))

        self.lexical_tip = tk.Label(
            self._tokens_frame,
            text="",
            font=("Segoe UI", 9),
            bg=t.tip_bg,
            fg=t.tip_fg,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=520,
            padx=8,
            pady=6,
        )
        # Packed only when a tip is available

        self._token_toggle = tk.Frame(self._tokens_frame, bg=t.panel)
        self._token_toggle.pack(fill=tk.X, padx=10, pady=(0, 6))
        self._token_view_label = tk.Label(
            self._token_toggle, text="View:", font=("Segoe UI", 9), bg=t.panel, fg=t.muted
        )
        self._token_view_label.pack(side=tk.LEFT)
        self._token_radio_table = tk.Radiobutton(
            self._token_toggle,
            text="Table",
            variable=self._token_view_mode,
            value="table",
            command=self._switch_token_view,
            font=("Segoe UI", 9),
            bg=t.panel,
            fg=t.text_strong,
            activebackground=t.panel,
            activeforeground=t.text_strong,
            selectcolor=t.check_select,
            highlightthickness=0,
        )
        self._token_radio_table.pack(side=tk.LEFT, padx=(8, 4))
        self._token_radio_diagram = tk.Radiobutton(
            self._token_toggle,
            text="Diagram",
            variable=self._token_view_mode,
            value="diagram",
            command=self._switch_token_view,
            font=("Segoe UI", 9),
            bg=t.panel,
            fg=t.text_strong,
            activebackground=t.panel,
            activeforeground=t.text_strong,
            selectcolor=t.check_select,
            highlightthickness=0,
        )
        self._token_radio_diagram.pack(side=tk.LEFT)

        self.fa_zoom_controls = tk.Frame(self._token_toggle, bg=t.panel)
        self._fa_zoom_label = tk.Label(
            self.fa_zoom_controls, text="Zoom:", font=("Segoe UI", 9), bg=t.panel, fg=t.muted
        )
        self._fa_zoom_label.pack(side=tk.LEFT, padx=(0, 4))
        self._fa_zoom_minus = tk.Button(
            self.fa_zoom_controls,
            text="−",
            width=3,
            font=("Segoe UI", 9, "bold"),
            command=lambda: self._set_fa_zoom(self._fa_zoom / _DIAG_ZOOM_STEP),
            bg=t.zoom_btn_bg,
            fg=t.text_strong,
            relief=tk.FLAT,
            cursor="hand2",
        )
        self._fa_zoom_minus.pack(side=tk.LEFT, padx=1)
        self._fa_zoom_pct = tk.Label(
            self.fa_zoom_controls,
            textvariable=self._fa_zoom_label_var,
            font=("Segoe UI", 9),
            bg=t.panel,
            fg=t.text_strong,
            width=5,
        )
        self._fa_zoom_pct.pack(side=tk.LEFT, padx=2)
        self._fa_zoom_plus = tk.Button(
            self.fa_zoom_controls,
            text="+",
            width=3,
            font=("Segoe UI", 9, "bold"),
            command=lambda: self._set_fa_zoom(self._fa_zoom * _DIAG_ZOOM_STEP),
            bg=t.zoom_btn_bg,
            fg=t.text_strong,
            relief=tk.FLAT,
            cursor="hand2",
        )
        self._fa_zoom_plus.pack(side=tk.LEFT, padx=1)
        self._fa_zoom_reset = tk.Button(
            self.fa_zoom_controls,
            text="Reset",
            font=("Segoe UI", 8),
            command=lambda: self._set_fa_zoom(1.0),
            bg=t.zoom_btn_bg,
            fg=t.text_strong,
            relief=tk.FLAT,
            cursor="hand2",
            padx=6,
        )
        self._fa_zoom_reset.pack(side=tk.LEFT, padx=(6, 0))

        self.token_body = tk.Frame(self._tokens_frame, bg=t.panel)
        self.token_body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))
        self.token_body.grid_rowconfigure(0, weight=1)
        self.token_body.grid_columnconfigure(0, weight=1)

        # --- Table view ---
        self.token_table_frame = tk.Frame(self.token_body, bg=t.panel)
        self.token_table_frame.grid(row=0, column=0, sticky="nsew")

        table_frame = tk.Frame(self.token_table_frame, bg=t.panel)
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("num", "type", "lexeme", "value", "line")
        self.token_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for col, heading, width in [
            ("num", "#", 40),
            ("type", "Token Type", 100),
            ("lexeme", "Lexeme", 140),
            ("value", "Value", 160),
            ("line", "Line", 50),
        ]:
            self.token_tree.heading(col, text=heading)
            self.token_tree.column(col, width=width, minwidth=40)
        self.token_tree.tag_configure(
            "error_token", background=t.tree_error_bg, foreground=t.tree_error_fg
        )

        ts = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.token_tree.yview)
        self.token_tree.configure(yscrollcommand=ts.set)
        self.token_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ts.pack(side=tk.RIGHT, fill=tk.Y)

        self._stream_label = tk.Label(
            self.token_table_frame,
            text="Token Stream:",
            font=("Segoe UI", 9, "bold"),
            bg=t.panel,
            fg=t.text_strong,
            anchor=tk.W,
        )
        self._stream_label.pack(fill=tk.X, pady=(8, 2))
        self.stream_text = tk.Text(
            self.token_table_frame,
            height=3,
            font=("Consolas", 9),
            bg=t.stream_bg,
            fg=t.text_strong,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.stream_text.tag_configure("error_token", foreground=t.error, font=("Consolas", 9, "bold"))
        self.stream_text.pack(fill=tk.X, pady=(0, 4))

        # --- FA Diagram view ---
        self.token_diagram_frame = tk.Frame(self.token_body, bg=t.panel)
        self.token_diagram_frame.grid(row=0, column=0, sticky="nsew")

        self._fa_legend = tk.Frame(self.token_diagram_frame, bg=t.panel)
        self._fa_legend.pack(fill=tk.X, pady=(0, 4))
        self._fa_legend_title = tk.Label(
            self._fa_legend,
            text="Finite Automaton  |",
            font=("Segoe UI", 9, "bold"),
            bg=t.panel,
            fg=t.text_strong,
        )
        self._fa_legend_title.pack(side=tk.LEFT)
        self._fa_legend_swatches: list[tk.Label] = []
        for text, color in [
            (" Start ", t.fa_start),
            (" State ", t.fa_normal),
            (" Final ", t.fa_final),
            (" Warn ", t.fa_warn),
            (" Dead ", t.fa_dead),
        ]:
            sw = tk.Label(
                self._fa_legend,
                text=text,
                font=("Segoe UI", 8),
                bg=color,
                fg=t.fa_label,
                relief=tk.SOLID,
                bd=1,
            )
            sw.pack(side=tk.LEFT, padx=3)
            self._fa_legend_swatches.append(sw)

        fa_canvas_wrap = tk.Frame(self.token_diagram_frame, bg=t.panel)
        fa_canvas_wrap.pack(fill=tk.BOTH, expand=True)
        self._fa_canvas_wrap = fa_canvas_wrap
        fa_canvas_wrap.grid_rowconfigure(0, weight=1)
        fa_canvas_wrap.grid_columnconfigure(0, weight=1)

        self.fa_canvas = tk.Canvas(
            fa_canvas_wrap, bg=t.canvas_bg, highlightthickness=1, highlightbackground=t.border
        )
        fa_vsb = ttk.Scrollbar(fa_canvas_wrap, orient=tk.VERTICAL, command=self.fa_canvas.yview)
        fa_hsb = ttk.Scrollbar(fa_canvas_wrap, orient=tk.HORIZONTAL, command=self.fa_canvas.xview)
        self.fa_canvas.configure(yscrollcommand=fa_vsb.set, xscrollcommand=fa_hsb.set)
        self.fa_canvas.grid(row=0, column=0, sticky="nsew")
        fa_vsb.grid(row=0, column=1, sticky="ns")
        fa_hsb.grid(row=1, column=0, sticky="ew")

        self.fa_canvas.bind("<Enter>", lambda _e: self.fa_canvas.focus_set())
        self.fa_canvas.bind("<MouseWheel>", self._on_fa_mousewheel)
        self.fa_canvas.bind("<Control-MouseWheel>", self._on_fa_mousewheel)
        self.fa_canvas.bind("<Button-4>", self._on_fa_mousewheel)
        self.fa_canvas.bind("<Button-5>", self._on_fa_mousewheel)

        self._switch_token_view()

    def _build_ast_tab(self) -> None:
        t = self.theme
        self._ast_frame = tk.Frame(self.notebook, bg=t.panel)
        self.notebook.add(self._ast_frame, text="  AST  ")

        self.syntax_status = tk.Label(
            self._ast_frame,
            text="Syntax analysis: waiting...",
            font=("Segoe UI", 10),
            bg=t.panel,
            fg=t.muted,
            anchor=tk.W,
        )
        self.syntax_status.pack(fill=tk.X, padx=10, pady=(8, 2))

        self.syntax_tip = tk.Label(
            self._ast_frame,
            text="",
            font=("Segoe UI", 9),
            bg=t.tip_bg,
            fg=t.tip_fg,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=520,
            padx=8,
            pady=6,
        )
        # Packed only when a tip is available

        self._ast_toggle = tk.Frame(self._ast_frame, bg=t.panel)
        self._ast_toggle.pack(fill=tk.X, padx=10, pady=(0, 6))
        self._ast_view_label = tk.Label(
            self._ast_toggle, text="View:", font=("Segoe UI", 9), bg=t.panel, fg=t.muted
        )
        self._ast_view_label.pack(side=tk.LEFT)
        self._ast_radio_tree = tk.Radiobutton(
            self._ast_toggle,
            text="Tree",
            variable=self._ast_view_mode,
            value="tree",
            command=self._switch_ast_view,
            font=("Segoe UI", 9),
            bg=t.panel,
            fg=t.text_strong,
            activebackground=t.panel,
            activeforeground=t.text_strong,
            selectcolor=t.check_select,
            highlightthickness=0,
        )
        self._ast_radio_tree.pack(side=tk.LEFT, padx=(8, 4))
        self._ast_radio_diagram = tk.Radiobutton(
            self._ast_toggle,
            text="Diagram",
            variable=self._ast_view_mode,
            value="diagram",
            command=self._switch_ast_view,
            font=("Segoe UI", 9),
            bg=t.panel,
            fg=t.text_strong,
            activebackground=t.panel,
            activeforeground=t.text_strong,
            selectcolor=t.check_select,
            highlightthickness=0,
        )
        self._ast_radio_diagram.pack(side=tk.LEFT)

        self.zoom_controls = tk.Frame(self._ast_toggle, bg=t.panel)
        self._ast_zoom_label = tk.Label(
            self.zoom_controls, text="Zoom:", font=("Segoe UI", 9), bg=t.panel, fg=t.muted
        )
        self._ast_zoom_label.pack(side=tk.LEFT, padx=(0, 4))
        self._ast_zoom_minus = tk.Button(
            self.zoom_controls,
            text="−",
            width=3,
            font=("Segoe UI", 9, "bold"),
            command=lambda: self._set_diagram_zoom(self._diagram_zoom / _DIAG_ZOOM_STEP),
            bg=t.zoom_btn_bg,
            fg=t.text_strong,
            relief=tk.FLAT,
            cursor="hand2",
        )
        self._ast_zoom_minus.pack(side=tk.LEFT, padx=1)
        self._ast_zoom_pct = tk.Label(
            self.zoom_controls,
            textvariable=self._zoom_label_var,
            font=("Segoe UI", 9),
            bg=t.panel,
            fg=t.text_strong,
            width=5,
        )
        self._ast_zoom_pct.pack(side=tk.LEFT, padx=2)
        self._ast_zoom_plus = tk.Button(
            self.zoom_controls,
            text="+",
            width=3,
            font=("Segoe UI", 9, "bold"),
            command=lambda: self._set_diagram_zoom(self._diagram_zoom * _DIAG_ZOOM_STEP),
            bg=t.zoom_btn_bg,
            fg=t.text_strong,
            relief=tk.FLAT,
            cursor="hand2",
        )
        self._ast_zoom_plus.pack(side=tk.LEFT, padx=1)
        self._ast_zoom_reset = tk.Button(
            self.zoom_controls,
            text="Reset",
            font=("Segoe UI", 8),
            command=lambda: self._set_diagram_zoom(1.0),
            bg=t.zoom_btn_bg,
            fg=t.text_strong,
            relief=tk.FLAT,
            cursor="hand2",
            padx=6,
        )
        self._ast_zoom_reset.pack(side=tk.LEFT, padx=(6, 0))

        self.ast_body = tk.Frame(self._ast_frame, bg=t.panel)
        self.ast_body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.ast_body.grid_rowconfigure(0, weight=1)
        self.ast_body.grid_columnconfigure(0, weight=1)

        # --- Tree view (existing expandable Treeview) ---
        self.ast_tree_frame = tk.Frame(self.ast_body, bg=t.panel)
        self.ast_tree_frame.grid(row=0, column=0, sticky="nsew")
        self.ast_tree = ttk.Treeview(self.ast_tree_frame, show="tree", height=18)
        ast_scroll = ttk.Scrollbar(self.ast_tree_frame, orient=tk.VERTICAL, command=self.ast_tree.yview)
        self.ast_tree.configure(yscrollcommand=ast_scroll.set)
        self.ast_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ast_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Diagram view (top-down parsing diagram) ---
        self.ast_diagram_frame = tk.Frame(self.ast_body, bg=t.panel)
        self.ast_diagram_frame.grid(row=0, column=0, sticky="nsew")
        self.ast_canvas = tk.Canvas(
            self.ast_diagram_frame, bg=t.canvas_bg, highlightthickness=1, highlightbackground=t.border
        )
        diag_vsb = ttk.Scrollbar(self.ast_diagram_frame, orient=tk.VERTICAL, command=self.ast_canvas.yview)
        diag_hsb = ttk.Scrollbar(self.ast_diagram_frame, orient=tk.HORIZONTAL, command=self.ast_canvas.xview)
        self.ast_canvas.configure(yscrollcommand=diag_vsb.set, xscrollcommand=diag_hsb.set)
        self.ast_canvas.grid(row=0, column=0, sticky="nsew")
        diag_vsb.grid(row=0, column=1, sticky="ns")
        diag_hsb.grid(row=1, column=0, sticky="ew")
        self.ast_diagram_frame.grid_rowconfigure(0, weight=1)
        self.ast_diagram_frame.grid_columnconfigure(0, weight=1)

        self.ast_canvas.bind("<Enter>", lambda _e: self.ast_canvas.focus_set())
        self.ast_canvas.bind("<MouseWheel>", self._on_diagram_mousewheel)
        self.ast_canvas.bind("<Control-MouseWheel>", self._on_diagram_mousewheel)
        self.ast_canvas.bind("<Button-4>", self._on_diagram_mousewheel)  # Linux zoom in
        self.ast_canvas.bind("<Button-5>", self._on_diagram_mousewheel)  # Linux zoom out

        self._switch_ast_view()

    def _build_summary_tab(self) -> None:
        t = self.theme
        self._summary_frame = tk.Frame(self.notebook, bg=t.panel)
        self.notebook.add(self._summary_frame, text="  Summary  ")

        self.summary_text = tk.Text(
            self._summary_frame,
            font=("Consolas", 11),
            bg=t.summary_bg,
            fg=t.text_strong,
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=12,
            pady=12,
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_output_tab(self) -> None:
        t = self.theme
        self._output_frame = tk.Frame(self.notebook, bg=t.panel)
        self.notebook.add(self._output_frame, text="  Execution Output  ")

        self.output_status = tk.Label(
            self._output_frame,
            text="Optional execution: not run",
            font=("Segoe UI", 10),
            bg=t.panel,
            fg=t.muted,
            anchor=tk.W,
        )
        self.output_status.pack(fill=tk.X, padx=10, pady=(8, 4))

        self.output_text = tk.Text(
            self._output_frame,
            font=("Consolas", 11),
            bg=t.code_bg,
            fg=t.code_fg,
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=12,
            pady=12,
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    def _build_status_bar(self) -> None:
        t = self.theme
        self._status_bar = tk.Frame(self, bg=t.status_bg, padx=12, pady=4)
        self._status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var = tk.StringVar(
            value="Ready — enter source code or open a .pnc file, then click Analyze."
        )
        self._status_label = tk.Label(
            self._status_bar,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=t.status_bg,
            fg=t.status_fg,
            anchor=tk.W,
        )
        self._status_label.pack(fill=tk.X)

    def _configure_syntax_tags(self) -> None:
        t = self.theme
        font_normal = ("Consolas", 11)
        specs = {
            "syn_keyword": t.syn_keyword,
            "syn_type": t.syn_type,
            "syn_bool": t.syn_bool,
            "syn_string": t.syn_string,
            "syn_number": t.syn_number,
            "syn_comment": t.syn_comment,
            "syn_ident": t.syn_ident,
            "syn_operator": t.syn_operator,
        }
        for tag, color in specs.items():
            self.source_text.tag_configure(
                tag, foreground=color, background=t.code_bg, font=font_normal
            )
        self._syntax_tags = tuple(specs.keys())

    def _sync_scroll(self, *args) -> None:
        self.source_text.yview(*args)
        self.line_numbers.yview(*args)

    def _on_text_yscroll(self, first: str, last: str) -> None:
        self.line_numbers.yview_moveto(first)
        self._editor_yscroll.set(first, last)

    def _on_mousewheel(self, event: tk.Event) -> str:
        # Windows / macOS use delta; Linux uses Button-4/5
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self.source_text.yview_scroll(-1, "units")
            self.line_numbers.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            self.source_text.yview_scroll(1, "units")
            self.line_numbers.yview_scroll(1, "units")
        return "break"

    def _on_source_modified(self, _event: object | None = None) -> None:
        if self.source_text.edit_modified():
            self.source_text.edit_modified(False)
            self.after_idle(self._refresh_editor_chrome)

    def _refresh_editor_chrome(self) -> None:
        self._update_line_numbers()
        self._apply_syntax_highlighting()

    def _update_line_numbers(self) -> None:
        last_line = int(self.source_text.index("end-1c").split(".")[0])
        width = max(3, len(str(last_line)))
        numbers = "\n".join(str(i) for i in range(1, last_line + 1))
        self.line_numbers.configure(state=tk.NORMAL, width=width)
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.configure(state=tk.DISABLED)
        # Keep gutter scroll aligned with the editor
        self.line_numbers.yview_moveto(self.source_text.yview()[0])

    def _apply_syntax_highlighting(self) -> None:
        text = self.source_text.get("1.0", "end-1c")
        for tag in self._syntax_tags:
            self.source_text.tag_remove(tag, "1.0", tk.END)

        for match in _HIGHLIGHT_RE.finditer(text):
            start, end = match.span()
            if start == end:
                continue
            kind = match.lastgroup
            if kind is None:
                continue
            tag = self._tag_for_match(kind, match.group())
            if tag is None:
                continue
            self.source_text.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

    def _tag_for_match(self, kind: str, lexeme: str) -> str | None:
        if kind in ("line_comment", "block_comment"):
            return "syn_comment"
        if kind == "string":
            return "syn_string"
        if kind == "number":
            return "syn_number"
        if kind == "operator":
            return "syn_operator"
        if kind == "ident":
            if lexeme in _TYPE_KEYWORDS:
                return "syn_type"
            if lexeme in _BOOL_KEYWORDS:
                return "syn_bool"
            if lexeme in _CONTROL_KEYWORDS or lexeme in KEYWORDS:
                return "syn_keyword"
            return "syn_ident"
        return None

    def _load_default_example(self) -> None:
        default = 'int a = 5;\nint b = 10;\nprint(a + b);\nprint("Hello World");'
        self.source_text.insert("1.0", default)

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open PNC Source File",
            filetypes=[("PNC files", "*.pnc"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            messagebox.showerror("Open Failed", str(e))
            return
        self.source_text.delete("1.0", tk.END)
        self.source_text.insert("1.0", content)
        self._current_path = path
        self.status_var.set(f"Loaded: {path}")
        self._refresh_editor_chrome()

    def _clear_all(self) -> None:
        self.source_text.delete("1.0", tk.END)
        self._current_path = None
        self._clear_results()
        self.status_var.set("Cleared.")
        self._refresh_editor_chrome()
    def _clear_results(self) -> None:
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        self._set_text(self.stream_text, "")
        self.fa_canvas.delete("all")
        self._fa_trace = None
        for item in self.ast_tree.get_children():
            self.ast_tree.delete(item)
        self.ast_canvas.delete("all")
        self._ast_statements = []
        self._set_text(self.summary_text, "")
        self._set_text(self.output_text, "")
        self.lexical_status.config(text="Lexical analysis: waiting...", fg=self.theme.muted)
        self._hide_lexical_tip()
        self.syntax_status.config(text="Syntax analysis: waiting...", fg=self.theme.muted)
        self._hide_syntax_tip()
        self.output_status.config(text="Optional execution: not run", fg=self.theme.muted)
        for lbl in self._stage_labels:
            lbl.config(bg=self.theme.stage_idle_bg, fg=self.theme.stage_idle_fg)
        self._stage_pass_state = (None, None)

    def _set_analysis_busy(self, busy: bool) -> None:
        """Disable toolbar actions while analysis/execution runs off the UI thread."""
        self._analysis_busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for btn in (
            getattr(self, "_btn_open", None),
            getattr(self, "_btn_analyze", None),
            getattr(self, "_btn_execute", None),
            getattr(self, "_btn_clear", None),
        ):
            if btn is not None:
                btn.config(state=state)

    def _run_analysis(self, run_execution: bool) -> None:
        if self._analysis_busy:
            return

        source = self.source_text.get("1.0", tk.END).strip()
        if not source:
            messagebox.showwarning("No Source", "Please enter or open PNC source code first.")
            return

        self._clear_results()
        self.status_var.set(
            "Analyzing + executing..." if run_execution else "Analyzing..."
        )
        self._set_analysis_busy(True)
        self.update_idletasks()

        def worker() -> None:
            error: BaseException | None = None
            result: AnalysisResult | None = None
            try:
                result = analyze_source(source, run_execution=run_execution)
            except BaseException as exc:  # noqa: BLE001 — surface any worker failure in UI
                error = exc
            self.after(
                0,
                lambda r=result, e=error: self._finish_analysis(r, run_execution, e),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_analysis(
        self,
        result: AnalysisResult | None,
        run_execution: bool,
        error: BaseException | None,
    ) -> None:
        self._set_analysis_busy(False)
        if error is not None:
            messagebox.showerror("Analysis Error", str(error))
            self.status_var.set("Analysis failed.")
            return
        assert result is not None
        self._display_result(result, run_execution)

    def _display_result(self, result: AnalysisResult, run_execution: bool) -> None:
        if result.lexical_error:
            self._highlight_stages(failed_at=1)  # Lexer stage index in header strip
        elif result.syntax_error:
            self._highlight_stages(failed_at=2)
        else:
            self._highlight_stages(failed_at=None, completed=4)

        if result.lexical_error:
            partial_note = (
                f" — partial tokens ({result.token_count})"
                if result.token_count
                else ""
            )
            dead_note = " — FA reached DEAD state" if result.automaton and result.automaton.has_dead_state else ""
            warn_note = ""
            if result.automaton and any(s.kind == "warn" for s in result.automaton.states):
                warn_note = " — Warn state before Dead"
            self.lexical_status.config(
                text=f"Lexical analysis: FAILED — {result.lexical_error}{partial_note}{dead_note}{warn_note}",
                fg=self.theme.error,
            )
            self._show_lexical_tip(result.lexical_tip)
            self.syntax_status.config(text="Syntax analysis: skipped (lexical error)", fg=self.theme.muted)
            self._hide_syntax_tip()
            self._populate_tokens(result.tokens)
            self._populate_stream(result.tokens)
            self._populate_automaton(result.automaton)
            self._set_summary(result, run_execution)
            self.status_var.set("Lexical error — check Tokens table and FA diagram (Warn/Dead).")
            self.notebook.select(0)
            return

        self.lexical_status.config(
            text=f"Lexical analysis: PASSED — {result.token_count} token(s) produced",
            fg=self.theme.success,
        )
        self._hide_lexical_tip()
        self._populate_tokens(result.tokens)
        self._populate_stream(result.tokens)
        self._populate_automaton(result.automaton)

        if result.syntax_error:
            partial_note = (
                f" — partial AST ({result.statement_count} node(s))"
                if result.statements
                else " — no complete statements recovered"
            )
            self.syntax_status.config(
                text=f"Syntax analysis: FAILED — {result.syntax_error}{partial_note}",
                fg=self.theme.error,
            )
            self._show_syntax_tip(result.syntax_tip)
            self._populate_ast(result.statements)
            self._set_summary(result, run_execution)
            self.status_var.set("Syntax error — partial AST shown with fix tip.")
            self.notebook.select(1)
            return

        self.syntax_status.config(
            text=f"Syntax analysis: PASSED — {result.statement_count} statement(s), AST built",
            fg=self.theme.success,
        )
        self._hide_syntax_tip()
        self._populate_ast(result.statements)

        if run_execution:
            if result.execution_ok:
                self.output_status.config(text="Optional execution: PASSED", fg=self.theme.success)
            else:
                short = (result.execution_error or "runtime error").split(".")[0]
                self.output_status.config(
                    text=f"Optional execution: FAILED — {short}.",
                    fg=self.theme.error,
                )
            self._set_text(self.output_text, self._format_execution_panel(result))
            self.notebook.select(3)
        else:
            self.output_status.config(text="Optional execution: skipped", fg=self.theme.muted)
            self.notebook.select(2)

        self._set_summary(result, run_execution)
        self.status_var.set("Analysis complete.")

    def _highlight_stages(self, *, failed_at: int | None = None, completed: int = 0) -> None:
        """Color the header pipeline strip.

        Stages: 0=Source, 1=Lexer, 2=Parser, 3=AST, 4=Summary
        On failure, stages before `failed_at` are green, the failed stage is red,
        and later stages stay muted.
        """
        self._stage_pass_state = (failed_at, completed if failed_at is None else None)
        t = self.theme
        for i, lbl in enumerate(self._stage_labels):
            if failed_at is not None:
                if i < failed_at:
                    lbl.config(bg=t.stage_pass_bg, fg=t.stage_pass_fg)
                elif i == failed_at:
                    lbl.config(bg=t.stage_fail_bg, fg=t.stage_fail_fg)
                else:
                    lbl.config(bg=t.stage_idle_bg, fg=t.stage_idle_fg)
            elif i <= completed:
                lbl.config(bg=t.stage_pass_bg, fg=t.stage_pass_fg)
            else:
                lbl.config(bg=t.stage_idle_bg, fg=t.stage_idle_fg)

    def _populate_tokens(self, tokens: list[Token]) -> None:
        display = [t for t in tokens if t.type != TokenType.EOF]
        for i, token in enumerate(display, start=1):
            value = "" if token.value is None else repr(token.value)
            tags = ("error_token",) if token.type == TokenType.ERROR else ()
            self.token_tree.insert(
                "",
                tk.END,
                values=(i, token.type, token.lexeme, value, token.line),
                tags=tags,
            )

    def _populate_stream(self, tokens: list[Token]) -> None:
        display = [t for t in tokens if t.type != TokenType.EOF]
        self.stream_text.config(state=tk.NORMAL)
        self.stream_text.delete("1.0", tk.END)
        if not display:
            self.stream_text.insert("1.0", "(empty)")
        else:
            for i, token in enumerate(display):
                if i:
                    self.stream_text.insert(tk.END, "  ->  ")
                chunk = f"[{token.type}: {token.lexeme!r}]"
                if token.type == TokenType.ERROR:
                    self.stream_text.insert(tk.END, chunk, ("error_token",))
                else:
                    self.stream_text.insert(tk.END, chunk)
        self.stream_text.config(state=tk.DISABLED)

    def _show_lexical_tip(self, tip: str | None) -> None:
        if tip:
            self.lexical_tip.config(text=f"Tip: {tip}")
            if not self.lexical_tip.winfo_ismapped():
                self.lexical_tip.pack(fill=tk.X, padx=10, pady=(0, 6), after=self.lexical_status)
        else:
            self._hide_lexical_tip()

    def _hide_lexical_tip(self) -> None:
        self.lexical_tip.config(text="")
        if self.lexical_tip.winfo_ismapped():
            self.lexical_tip.pack_forget()

    def _switch_token_view(self) -> None:
        if self._token_view_mode.get() == "diagram":
            self.token_diagram_frame.tkraise()
            self.fa_zoom_controls.pack(side=tk.RIGHT)
        else:
            self.token_table_frame.tkraise()
            self.fa_zoom_controls.pack_forget()

    def _populate_automaton(self, trace: AutomatonTrace | None) -> None:
        self._fa_trace = trace
        self._draw_fa_diagram(trace)

    def _fa_s(self, value: float) -> float:
        return value * self._fa_zoom

    def _set_fa_zoom(self, zoom: float) -> None:
        zoom = max(_DIAG_ZOOM_MIN, min(_DIAG_ZOOM_MAX, zoom))
        if abs(zoom - self._fa_zoom) < 1e-6:
            self._fa_zoom_label_var.set(f"{int(round(self._fa_zoom * 100))}%")
            return
        self._fa_zoom = zoom
        self._fa_zoom_label_var.set(f"{int(round(self._fa_zoom * 100))}%")
        if self._fa_trace is not None:
            self._draw_fa_diagram(self._fa_trace)

    def _on_fa_mousewheel(self, event: tk.Event) -> str:
        if self._token_view_mode.get() != "diagram":
            return ""
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self._set_fa_zoom(self._fa_zoom * _DIAG_ZOOM_STEP)
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            self._set_fa_zoom(self._fa_zoom / _DIAG_ZOOM_STEP)
        return "break"

    def _draw_fa_diagram(self, trace: AutomatonTrace | None) -> None:
        self.fa_canvas.delete("all")
        if trace is None or not trace.states:
            self.fa_canvas.create_text(
                _FA_MARGIN, _FA_MARGIN, text="(no automaton)", anchor=tk.NW, fill=self.theme.muted, font=("Segoe UI", 10)
            )
            self.fa_canvas.configure(scrollregion=(0, 0, 200, 80))
            return

        positions = self._layout_fa_states(trace.states)
        # Draw edges first so nodes sit on top
        for edge in trace.transitions:
            if edge.from_id not in positions or edge.to_id not in positions:
                continue
            self._draw_fa_edge(positions[edge.from_id], positions[edge.to_id], edge.symbol)

        for state in trace.states:
            x, y = positions[state.id]
            self._draw_fa_state(state, x, y)

        bbox = self.fa_canvas.bbox("all")
        if bbox:
            pad = self._fa_s(_FA_MARGIN)
            self.fa_canvas.configure(scrollregion=(0, 0, bbox[2] + pad, bbox[3] + pad))

    def _layout_fa_states(self, states: list[FAState]) -> dict[str, tuple[float, float]]:
        positions: dict[str, tuple[float, float]] = {}
        margin = self._fa_s(_FA_MARGIN)
        gap = self._fa_s(_FA_GAP)
        row_gap = self._fa_s(_FA_ROW_GAP)
        wrap = _FA_WRAP
        for i, state in enumerate(states):
            row, col = divmod(i, wrap)
            # Snake layout so wrapped rows stay readable left-to-right then right-to-left
            if row % 2 == 1:
                col = wrap - 1 - col
            x = margin + col * gap
            y = margin + row * row_gap + self._fa_s(20)
            positions[state.id] = (x, y)
        return positions

    def _draw_fa_state(self, state: FAState, x: float, y: float) -> None:
        t = self.theme
        r = self._fa_s(_FA_RADIUS)
        if state.kind == "dead":
            fill, outline = t.fa_dead, t.stage_fail_fg
        elif state.kind == "warn":
            fill, outline = t.fa_warn, "#b45309"
        elif state.kind == "final":
            fill, outline = t.fa_final, t.stage_pass_fg
        elif state.kind == "start":
            fill, outline = t.fa_start, t.accent
        else:
            fill, outline = t.fa_normal, t.fa_outline

        width = max(1.5, self._fa_s(1.5))
        self.fa_canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=outline, width=width)
        if state.kind == "final":
            inner = r - self._fa_s(4)
            self.fa_canvas.create_oval(
                x - inner, y - inner, x + inner, y + inner, outline=outline, width=width
            )

        font_size = max(7, int(round(9 * self._fa_zoom)))
        self.fa_canvas.create_text(
            x, y, text=state.label, font=("Segoe UI", font_size, "bold"), fill=t.fa_label
        )

        if state.accept_info:
            info_size = max(6, int(round(7 * self._fa_zoom)))
            if state.kind == "final":
                info_color = t.stage_pass_fg
            elif state.kind == "dead":
                info_color = t.stage_fail_fg
            elif state.kind == "warn":
                info_color = "#b45309"
            else:
                info_color = t.text_strong
            self.fa_canvas.create_text(
                x, y + r + self._fa_s(10),
                text=state.accept_info,
                font=("Segoe UI", info_size),
                fill=info_color,
            )

    def _draw_fa_edge(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        symbol: str,
    ) -> None:
        x1, y1 = start
        x2, y2 = end
        r = self._fa_s(_FA_RADIUS)
        dx, dy = x2 - x1, y2 - y1
        dist = (dx * dx + dy * dy) ** 0.5 or 1.0
        ux, uy = dx / dist, dy / dist
        sx, sy = x1 + ux * r, y1 + uy * r
        ex, ey = x2 - ux * r, y2 - uy * r
        line_w = max(1.0, self._fa_s(1.4))
        arrow = (
            max(6, int(round(8 * self._fa_zoom))),
            max(7, int(round(10 * self._fa_zoom))),
            max(3, int(round(4 * self._fa_zoom))),
        )
        self.fa_canvas.create_line(
            sx, sy, ex, ey, fill=self.theme.fa_outline, width=line_w, arrow=tk.LAST, arrowshape=arrow
        )
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        # Offset label perpendicular to the edge
        ox, oy = -uy * self._fa_s(12), ux * self._fa_s(12)
        label = symbol
        font_size = max(7, int(round(8 * self._fa_zoom)))
        self.fa_canvas.create_text(
            mx + ox, my + oy, text=label, font=("Segoe UI", font_size), fill=self.theme.accent
        )

    def _populate_ast(self, statements: list[Stmt]) -> None:
        self._ast_statements = list(statements)
        for item in self.ast_tree.get_children():
            self.ast_tree.delete(item)
        root = self.ast_tree.insert("", tk.END, text="Program", open=True)
        for i, stmt in enumerate(statements):
            is_last = i == len(statements) - 1
            self._insert_stmt(root, stmt, is_last)
        self._draw_ast_diagram(statements)

    def _switch_ast_view(self) -> None:
        if self._ast_view_mode.get() == "diagram":
            self.ast_diagram_frame.tkraise()
            self.zoom_controls.pack(side=tk.RIGHT)
        else:
            self.ast_tree_frame.tkraise()
            self.zoom_controls.pack_forget()

    def _diag_s(self, value: float) -> float:
        return value * self._diagram_zoom

    def _diag_node_font(self) -> tuple[str, int]:
        return ("Segoe UI", max(6, int(round(10 * self._diagram_zoom))))

    def _diag_edge_font(self) -> tuple[str, int]:
        return ("Segoe UI", max(6, int(round(8 * self._diagram_zoom))))

    def _set_diagram_zoom(self, zoom: float) -> None:
        zoom = max(_DIAG_ZOOM_MIN, min(_DIAG_ZOOM_MAX, zoom))
        if abs(zoom - self._diagram_zoom) < 1e-6:
            self._zoom_label_var.set(f"{int(round(self._diagram_zoom * 100))}%")
            return
        self._diagram_zoom = zoom
        self._zoom_label_var.set(f"{int(round(self._diagram_zoom * 100))}%")
        if self._ast_statements:
            self._draw_ast_diagram(self._ast_statements)

    def _on_diagram_mousewheel(self, event: tk.Event) -> str:
        if self._ast_view_mode.get() != "diagram":
            return ""
        # Windows / macOS: event.delta; Linux: Button-4 / Button-5
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self._set_diagram_zoom(self._diagram_zoom * _DIAG_ZOOM_STEP)
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            self._set_diagram_zoom(self._diagram_zoom / _DIAG_ZOOM_STEP)
        return "break"

    def _show_syntax_tip(self, tip: str | None) -> None:
        if tip:
            self.syntax_tip.config(text=f"Tip: {tip}")
            if not self.syntax_tip.winfo_ismapped():
                self.syntax_tip.pack(fill=tk.X, padx=10, pady=(0, 6), after=self.syntax_status)
        else:
            self._hide_syntax_tip()

    def _hide_syntax_tip(self) -> None:
        self.syntax_tip.config(text="")
        if self.syntax_tip.winfo_ismapped():
            self.syntax_tip.pack_forget()

    def _insert_stmt(self, parent: str, stmt: Stmt, is_last: bool) -> None:
        if isinstance(stmt, VarDeclStmt):
            node = self.ast_tree.insert(
                parent, tk.END, text=f"VarDeclStmt: {stmt.datatype} {stmt.name}", open=True
            )
            self._insert_expr(node, stmt.value, True)
        elif isinstance(stmt, AssignStmt):
            node = self.ast_tree.insert(parent, tk.END, text="AssignStmt", open=True)
            self._insert_expr(node, stmt.target, False)
            self._insert_expr(node, stmt.value, True)
        elif isinstance(stmt, ExprStmt):
            node = self.ast_tree.insert(parent, tk.END, text="ExprStmt", open=True)
            self._insert_expr(node, stmt.expr, True)
        elif isinstance(stmt, PrintStmt):
            node = self.ast_tree.insert(parent, tk.END, text="PrintStmt", open=True)
            self._insert_expr(node, stmt.expr, True)
        elif isinstance(stmt, BlockStmt):
            node = self.ast_tree.insert(parent, tk.END, text="BlockStmt", open=True)
            for i, inner in enumerate(stmt.statements):
                self._insert_stmt(node, inner, i == len(stmt.statements) - 1)
        elif isinstance(stmt, IfStmt):
            node = self.ast_tree.insert(parent, tk.END, text="IfStmt", open=True)
            self._insert_expr(node, stmt.condition, False)
            has_else = stmt.else_branch is not None
            self._insert_stmt(node, stmt.then_branch, not has_else)
            if has_else and stmt.else_branch is not None:
                self._insert_stmt(node, stmt.else_branch, True)
        elif isinstance(stmt, WhileStmt):
            node = self.ast_tree.insert(parent, tk.END, text="WhileStmt", open=True)
            self._insert_expr(node, stmt.condition, False)
            self._insert_stmt(node, stmt.body, True)
        elif isinstance(stmt, DoWhileStmt):
            node = self.ast_tree.insert(parent, tk.END, text="DoWhileStmt", open=True)
            self._insert_stmt(node, stmt.body, False)
            self._insert_expr(node, stmt.condition, True)
        elif isinstance(stmt, ForStmt):
            node = self.ast_tree.insert(parent, tk.END, text="ForStmt", open=True)
            if stmt.initializer is not None:
                self._insert_stmt(node, stmt.initializer, False)
            if stmt.condition is not None:
                self._insert_expr(node, stmt.condition, False)
            if stmt.update is not None:
                self._insert_expr(node, stmt.update, False)
            self._insert_stmt(node, stmt.body, True)

    def _insert_expr(self, parent: str, expr: Expr, is_last: bool) -> None:
        if isinstance(expr, NumberLiteral):
            self.ast_tree.insert(parent, tk.END, text=f"NumberLiteral: {expr.value}")
        elif isinstance(expr, StringLiteral):
            self.ast_tree.insert(parent, tk.END, text=f"StringLiteral: {expr.value!r}")
        elif isinstance(expr, BoolLiteral):
            self.ast_tree.insert(parent, tk.END, text=f"BoolLiteral: {expr.value}")
        elif isinstance(expr, Variable):
            self.ast_tree.insert(parent, tk.END, text=f"Variable: {expr.name}")
        elif isinstance(expr, IncompleteExpr):
            self.ast_tree.insert(parent, tk.END, text=f"IncompleteExpr: {expr.placeholder}")
        elif isinstance(expr, ArrayLiteral):
            node = self.ast_tree.insert(parent, tk.END, text="ArrayLiteral", open=True)
            for i, el in enumerate(expr.elements):
                self._insert_expr(node, el, i == len(expr.elements) - 1)
        elif isinstance(expr, IndexExpr):
            node = self.ast_tree.insert(parent, tk.END, text="IndexExpr", open=True)
            self._insert_expr(node, expr.array, False)
            self._insert_expr(node, expr.index, True)
        elif isinstance(expr, AssignExpr):
            node = self.ast_tree.insert(parent, tk.END, text="AssignExpr", open=True)
            self._insert_expr(node, expr.target, False)
            self._insert_expr(node, expr.value, True)
        elif isinstance(expr, UpdateExpr):
            kind = "prefix" if expr.prefix else "postfix"
            node = self.ast_tree.insert(
                parent, tk.END, text=f"UpdateExpr ({kind} {expr.op.lexeme})", open=True
            )
            self._insert_expr(node, expr.target, True)
        elif isinstance(expr, UnaryExpr):
            node = self.ast_tree.insert(parent, tk.END, text=f"UnaryExpr ({expr.op.lexeme})", open=True)
            self._insert_expr(node, expr.right, True)
        elif isinstance(expr, BinaryExpr):
            node = self.ast_tree.insert(parent, tk.END, text=f"BinaryExpr ({expr.op.lexeme})", open=True)
            self._insert_expr(node, expr.left, False)
            self._insert_expr(node, expr.right, True)

    # --- Top-down syntax-tree diagram ---

    def _draw_ast_diagram(self, statements: list[Stmt]) -> None:
        self.ast_canvas.delete("all")
        margin = self._diag_s(_DIAG_MARGIN)
        if not statements:
            self.ast_canvas.create_text(
                margin, margin, text="(empty program)", anchor=tk.NW, fill=self.theme.muted, font=self._diag_node_font()
            )
            self.ast_canvas.configure(scrollregion=(0, 0, 200, 80))
            return

        root = self._build_diagram_tree(statements)
        self._measure_diagram(root)
        self._layout_diagram(root, margin, margin)
        self._render_diagram(root)

        bbox = self.ast_canvas.bbox("all")
        if bbox:
            self.ast_canvas.configure(
                scrollregion=(0, 0, bbox[2] + margin, bbox[3] + margin)
            )

    def _build_diagram_tree(self, statements: list[Stmt]) -> _DiagramNode:
        if len(statements) == 1:
            return self._stmt_to_diagram(statements[0])
        children = [(f"stmt{i + 1}", self._stmt_to_diagram(s)) for i, s in enumerate(statements)]
        return _DiagramNode("Program", children)

    def _stmt_to_diagram(self, stmt: Stmt) -> _DiagramNode:
        if isinstance(stmt, VarDeclStmt):
            return _DiagramNode(
                f"Declare ({stmt.datatype} {stmt.name})",
                [
                    ("name", _DiagramNode(f"Identifier: {stmt.name}")),
                    ("value", self._expr_to_diagram(stmt.value)),
                ],
            )
        if isinstance(stmt, AssignStmt):
            return _DiagramNode(
                "Assign (=)",
                [
                    ("target", self._expr_to_diagram(stmt.target)),
                    ("value", self._expr_to_diagram(stmt.value)),
                ],
            )
        if isinstance(stmt, ExprStmt):
            return _DiagramNode("ExprStmt", [("expr", self._expr_to_diagram(stmt.expr))])
        if isinstance(stmt, PrintStmt):
            return _DiagramNode("Print", [("expr", self._expr_to_diagram(stmt.expr))])
        if isinstance(stmt, BlockStmt):
            children = [
                (f"stmt{i + 1}", self._stmt_to_diagram(inner))
                for i, inner in enumerate(stmt.statements)
            ]
            return _DiagramNode("Block", children or [("body", _DiagramNode("(empty)"))])
        if isinstance(stmt, IfStmt):
            children: list[tuple[str, _DiagramNode]] = [
                ("condition", self._expr_to_diagram(stmt.condition)),
                ("then", self._stmt_to_diagram(stmt.then_branch)),
            ]
            if stmt.else_branch is not None:
                children.append(("else", self._stmt_to_diagram(stmt.else_branch)))
            return _DiagramNode("If", children)
        if isinstance(stmt, WhileStmt):
            return _DiagramNode(
                "While",
                [
                    ("condition", self._expr_to_diagram(stmt.condition)),
                    ("body", self._stmt_to_diagram(stmt.body)),
                ],
            )
        if isinstance(stmt, DoWhileStmt):
            return _DiagramNode(
                "DoWhile",
                [
                    ("body", self._stmt_to_diagram(stmt.body)),
                    ("condition", self._expr_to_diagram(stmt.condition)),
                ],
            )
        if isinstance(stmt, ForStmt):
            children = []
            if stmt.initializer is not None:
                children.append(("init", self._stmt_to_diagram(stmt.initializer)))
            if stmt.condition is not None:
                children.append(("condition", self._expr_to_diagram(stmt.condition)))
            if stmt.update is not None:
                children.append(("update", self._expr_to_diagram(stmt.update)))
            children.append(("body", self._stmt_to_diagram(stmt.body)))
            return _DiagramNode("For", children)
        return _DiagramNode(type(stmt).__name__)

    def _expr_to_diagram(self, expr: Expr) -> _DiagramNode:
        if isinstance(expr, NumberLiteral):
            value = int(expr.value) if expr.value == int(expr.value) else expr.value
            return _DiagramNode(f"Literal: {value}")
        if isinstance(expr, StringLiteral):
            return _DiagramNode(f"Literal: {expr.value!r}")
        if isinstance(expr, BoolLiteral):
            return _DiagramNode(f"Literal: {str(expr.value).lower()}")
        if isinstance(expr, Variable):
            return _DiagramNode(f"Identifier: {expr.name}")
        if isinstance(expr, IncompleteExpr):
            return _DiagramNode(f"Incomplete: {expr.placeholder}")
        if isinstance(expr, ArrayLiteral):
            children = [
                (f"elem{i + 1}", self._expr_to_diagram(el))
                for i, el in enumerate(expr.elements)
            ]
            return _DiagramNode("ArrayLiteral", children or [("empty", _DiagramNode("{}"))])
        if isinstance(expr, IndexExpr):
            return _DiagramNode(
                "Index",
                [
                    ("array", self._expr_to_diagram(expr.array)),
                    ("index", self._expr_to_diagram(expr.index)),
                ],
            )
        if isinstance(expr, AssignExpr):
            return _DiagramNode(
                "AssignExpr",
                [
                    ("target", self._expr_to_diagram(expr.target)),
                    ("value", self._expr_to_diagram(expr.value)),
                ],
            )
        if isinstance(expr, UpdateExpr):
            kind = "prefix" if expr.prefix else "postfix"
            return _DiagramNode(
                f"Update ({kind} {expr.op.lexeme})",
                [("target", self._expr_to_diagram(expr.target))],
            )
        if isinstance(expr, UnaryExpr):
            name = f"Unary ({expr.op.lexeme})"
            return _DiagramNode(name, [("operand", self._expr_to_diagram(expr.right))])
        if isinstance(expr, BinaryExpr):
            op = expr.op.lexeme
            title = _BINARY_OP_NAMES.get(op, "Binary")
            return _DiagramNode(
                f"{title} ({op})",
                [
                    ("left", self._expr_to_diagram(expr.left)),
                    ("right", self._expr_to_diagram(expr.right)),
                ],
            )
        return _DiagramNode(type(expr).__name__)

    def _measure_diagram(self, node: _DiagramNode) -> None:
        text_id = self.ast_canvas.create_text(0, 0, text=node.label, font=self._diag_node_font())
        bbox = self.ast_canvas.bbox(text_id)
        self.ast_canvas.delete(text_id)
        if bbox:
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:
            tw, th = max(len(node.label) * 7 * self._diagram_zoom, 48 * self._diagram_zoom), 16 * self._diagram_zoom
        node.box_w = tw + self._diag_s(_DIAG_PAD_X) * 2
        node.box_h = th + self._diag_s(_DIAG_PAD_Y) * 2

        if not node.children:
            node.subtree_w = node.box_w
            return

        for _, child in node.children:
            self._measure_diagram(child)

        h_gap = self._diag_s(_DIAG_H_GAP)
        children_w = sum(c.subtree_w for _, c in node.children) + h_gap * (len(node.children) - 1)
        node.subtree_w = max(node.box_w, children_w)

    def _layout_diagram(self, node: _DiagramNode, left: float, top: float) -> None:
        node.y = top
        node.x = left + node.subtree_w / 2.0

        if not node.children:
            return

        h_gap = self._diag_s(_DIAG_H_GAP)
        v_gap = self._diag_s(_DIAG_V_GAP)
        children_w = sum(c.subtree_w for _, c in node.children) + h_gap * (len(node.children) - 1)
        child_left = left + max(0.0, (node.subtree_w - children_w) / 2.0)
        child_top = top + node.box_h + v_gap

        for _, child in node.children:
            self._layout_diagram(child, child_left, child_top)
            child_left += child.subtree_w + h_gap

    def _render_diagram(self, node: _DiagramNode) -> None:
        for edge_label, child in node.children:
            self._draw_diagram_edge(node, child, edge_label)
            self._render_diagram(child)
        self._draw_diagram_box(node)

    def _draw_diagram_box(self, node: _DiagramNode) -> None:
        x1 = node.x - node.box_w / 2
        y1 = node.y
        x2 = node.x + node.box_w / 2
        y2 = node.y + node.box_h
        radius = self._diag_s(8)
        line_w = max(1.0, self._diag_s(1.5))
        self._round_rect(x1, y1, x2, y2, radius, fill=self.theme.diag_fill, outline=self.theme.diag_outline, width=line_w)
        self.ast_canvas.create_text(
            node.x,
            node.y + node.box_h / 2,
            text=node.label,
            font=self._diag_node_font(),
            fill=self.theme.diag_text,
        )

    def _draw_diagram_edge(self, parent: _DiagramNode, child: _DiagramNode, label: str) -> None:
        x1 = parent.x
        y1 = parent.y + parent.box_h
        x2 = child.x
        y2 = child.y
        line_w = max(1.0, self._diag_s(1.5))
        arrow = (
            max(6, int(round(9 * self._diagram_zoom))),
            max(7, int(round(11 * self._diagram_zoom))),
            max(3, int(round(4 * self._diagram_zoom))),
        )
        self.ast_canvas.create_line(
            x1, y1, x2, y2, fill=self.theme.diag_outline, width=line_w, arrow=tk.LAST, arrowshape=arrow
        )
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        dx = x2 - x1
        offset = self._diag_s(14) if dx >= 0 else -self._diag_s(14)
        self.ast_canvas.create_text(
            mx + offset, my - self._diag_s(4), text=label, font=self._diag_edge_font(), fill=self.theme.diag_edge
        )

    def _round_rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float,
        **kwargs,
    ) -> None:
        r = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
        points = [
            x1 + r, y1,
            x1 + r, y1,
            x2 - r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1 + r,
            x1, y1,
        ]
        self.ast_canvas.create_polygon(points, smooth=True, **kwargs)

    def _set_summary(self, result: AnalysisResult, run_execution: bool) -> None:
        if result.lexical_error:
            syntax_status = "SKIPPED (lexical error)"
        elif result.syntax_valid:
            syntax_status = "PASSED"
        else:
            syntax_status = "FAILED"
        lines = [
            "Pipeline Summary",
            "=" * 40,
            f"Tokens produced:     {result.token_count}",
            f"Statements parsed:   {result.statement_count}",
            f"Syntax validation:   {syntax_status}",
        ]
        if result.lexical_error:
            lines.append(f"Lexical error:       {result.lexical_error}")
            if result.lexical_tip:
                lines.append(f"Tip:                 {result.lexical_tip}")
            if result.token_count:
                lines.append(f"Partial tokens:      {result.token_count} (includes ERROR if present)")
            if result.automaton:
                if any(s.kind == "warn" for s in result.automaton.states):
                    lines.append("FA result:           WARN state then DEAD")
                elif result.automaton.has_dead_state:
                    lines.append("FA result:           DEAD state reached")
        if result.syntax_error:
            lines.append(f"Syntax error:        {result.syntax_error}")
            if result.syntax_tip:
                lines.append(f"Tip:                 {result.syntax_tip}")
            if result.statements:
                lines.append(f"Partial AST nodes:   {result.statement_count}")
        if run_execution:
            status = "PASSED" if result.execution_ok else "FAILED"
            lines.append(f"Execution:           {status}")
            if result.execution_error:
                lines.append(f"Runtime error:       {result.execution_error}")
        else:
            lines.append("Execution:           SKIPPED")
        self._set_text(self.summary_text, "\n".join(lines))

    @staticmethod
    def _format_execution_panel(result: AnalysisResult) -> str:
        """Build the Execution Output tab text, capped for Tk Text responsiveness."""
        max_display_chars = 12_000
        body = result.execution_output or ""
        if not body and result.execution_ok:
            body = "(no output)"
        if len(body) > max_display_chars:
            omitted = len(body) - max_display_chars
            body = (
                body[:max_display_chars]
                + f"\n... [display truncated — {omitted:,} more character(s) omitted]\n"
            )
        if result.execution_error:
            if body and not body.endswith("\n"):
                body += "\n"
            body += f"\n--- Runtime stopped ---\n{result.execution_error}\n"
        return body or "(no output)"

    @staticmethod
    def _set_text(widget: tk.Text, content: str) -> None:
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.config(state=tk.DISABLED)

    def _on_theme_changed(self) -> None:
        display_to_key = {
            "Default UI": "default",
            "Dark Mode": "dark",
        }
        key = display_to_key.get(self._theme_display.get(), "default")
        # Migrate away from removed Neon option if it somehow remains selected
        if self._theme_display.get() == "Neon UI":
            key = "dark"
        self._theme_key.set(key)
        self.theme = THEMES[key]
        self._apply_theme()

    def _apply_theme(self) -> None:
        t = self.theme
        minimal = bool(self._minimal_var.get())
        self.configure(bg=t.bg)

        # Keep display combo in sync
        self._theme_display.set(t.label)

        # Combobox dropdown list (popdown) colors
        self.option_add("*TCombobox*Listbox.background", t.panel)
        self.option_add("*TCombobox*Listbox.foreground", t.text_strong)
        self.option_add("*TCombobox*Listbox.selectBackground", t.accent)
        self.option_add("*TCombobox*Listbox.selectForeground", "white")

        # Header
        for w in (
            self._header,
            self._header_top,
            self._header_titles,
            self._header_controls,
            self._flow,
        ):
            w.configure(bg=t.accent)
        self._header.configure(bg=t.accent, pady=(8 if minimal else 12))
        self._header_title.configure(
            bg=t.accent, fg="white", font=("Segoe UI", 14 if minimal else 16, "bold")
        )
        self._header_subtitle.configure(bg=t.accent, fg=t.header_sub)
        self._ui_style_label.configure(bg=t.accent, fg="white")
        self._minimal_check.configure(
            bg=t.accent,
            fg="white",
            activebackground=t.accent,
            activeforeground="white",
            selectcolor=t.check_select,
        )
        self._about_btn.configure(
            bg="white" if t.key == "default" else t.panel,
            fg=t.accent if t.key == "default" else t.text_strong,
            activebackground=t.stream_bg,
            activeforeground=t.accent,
        )
        for arrow in self._stage_arrows:
            arrow.configure(bg=t.accent, fg=t.header_arrow)

        failed_at, completed = self._stage_pass_state
        if failed_at is not None:
            self._highlight_stages(failed_at=failed_at)
        elif completed is not None:
            self._highlight_stages(completed=completed)
        else:
            for lbl in self._stage_labels:
                lbl.configure(bg=t.stage_idle_bg, fg=t.stage_idle_fg)

        # Minimal: hide subtitle + pipeline strip
        if minimal:
            self._header_subtitle.pack_forget()
            self._flow.pack_forget()
        else:
            if not self._header_subtitle.winfo_ismapped():
                self._header_subtitle.pack(anchor=tk.W, pady=(2, 0))
            if not self._flow.winfo_ismapped():
                self._flow.pack(anchor=tk.W, pady=(8, 0))

        # Toolbar
        pad = 6 if minimal else 12
        self._toolbar.configure(
            bg=t.panel,
            highlightbackground=t.border,
            highlightthickness=0 if minimal else 1,
            padx=pad,
            pady=4 if minimal else 8,
        )
        self._toolbar.pack_configure(padx=pad, pady=(pad, 0))
        self._btn_open.configure(bg=t.panel, fg=t.text_strong, activebackground=t.stream_bg)
        self._btn_clear.configure(bg=t.panel, fg=t.text_strong, activebackground=t.stream_bg)
        self._btn_analyze.configure(
            bg=t.accent, fg="white", activebackground=t.accent_hover, activeforeground="white"
        )
        self._btn_execute.configure(
            bg=t.success, fg="white", activebackground=t.success_hover, activeforeground="white"
        )

        # Main panels
        self._paned.configure(bg=t.bg, sashwidth=6)
        self._paned.pack_configure(padx=pad, pady=pad)
        border_w = 0 if minimal else 1
        for panel in (self._left_panel, self._right_panel):
            panel.configure(bg=t.panel, highlightbackground=t.border, highlightthickness=border_w)
        self._source_label.configure(bg=t.panel, fg=t.text_strong)
        self._editor_frame.configure(bg=t.code_bg)
        self.line_numbers.configure(background=t.gutter_bg, foreground=t.gutter_fg)
        self.source_text.configure(
            bg=t.code_bg,
            fg=t.code_fg,
            insertbackground=t.insert_bg,
            selectbackground=t.select_bg,
        )
        self._configure_syntax_tags()
        self._apply_syntax_highlighting()

        # Notebook / treeview / scrollbar / combobox ttk styles
        style = self._ttk_style
        style.configure("TNotebook", background=t.panel, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=t.zoom_btn_bg,
            foreground=t.text_strong,
            padding=(10, 4) if not minimal else (8, 2),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", t.accent), ("active", t.border)],
            foreground=[("selected", "white"), ("active", t.text_strong)],
        )
        style.configure(
            "Treeview",
            background=t.panel,
            foreground=t.text_strong,
            fieldbackground=t.panel,
            borderwidth=0,
            rowheight=22 if not minimal else 20,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", t.accent)],
            foreground=[("selected", "white")],
        )
        style.configure(
            "Treeview.Heading",
            background=t.heading_bg,
            foreground=t.heading_fg,
            relief="flat",
            borderwidth=1,
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "Treeview.Heading",
            background=[("active", t.border)],
            foreground=[("active", t.heading_fg)],
        )
        style.configure(
            "TCombobox",
            fieldbackground=t.panel,
            background=t.panel,
            foreground=t.text_strong,
            arrowcolor=t.text_strong,
            bordercolor=t.border,
            lightcolor=t.border,
            darkcolor=t.border,
            insertcolor=t.text_strong,
            relief="flat",
            padding=4,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", t.panel), ("disabled", t.zoom_btn_bg)],
            foreground=[("readonly", t.text_strong)],
            background=[("readonly", t.panel), ("active", t.panel)],
            arrowcolor=[("readonly", t.text_strong), ("disabled", t.muted)],
            selectbackground=[("readonly", t.panel)],
            selectforeground=[("readonly", t.text_strong)],
        )
        for orient in ("Vertical", "Horizontal"):
            style.configure(
                f"{orient}.TScrollbar",
                background=t.scroll_bg,
                troughcolor=t.scroll_trough,
                bordercolor=t.border,
                arrowcolor=t.scroll_arrow,
                darkcolor=t.border,
                lightcolor=t.border,
                arrowsize=14,
                relief="flat",
                borderwidth=0,
            )
            style.map(
                f"{orient}.TScrollbar",
                background=[("active", t.muted), ("pressed", t.accent)],
                arrowcolor=[("disabled", t.muted)],
            )
        # Tokens tab
        for frame in (
            self._tokens_frame,
            self._token_toggle,
            self.fa_zoom_controls,
            self.token_body,
            self.token_table_frame,
            self.token_diagram_frame,
            self._fa_legend,
            self._fa_canvas_wrap,
        ):
            frame.configure(bg=t.panel)
        self.lexical_status.configure(bg=t.panel)
        self.lexical_tip.configure(bg=t.tip_bg, fg=t.tip_fg)
        self._token_view_label.configure(bg=t.panel, fg=t.muted)
        for rb in (self._token_radio_table, self._token_radio_diagram):
            rb.configure(
                bg=t.panel,
                fg=t.text_strong,
                activebackground=t.panel,
                activeforeground=t.text_strong,
                selectcolor=t.check_select,
            )
        self._fa_zoom_label.configure(bg=t.panel, fg=t.muted)
        self._fa_zoom_pct.configure(bg=t.panel, fg=t.text_strong)
        for btn in (self._fa_zoom_minus, self._fa_zoom_plus, self._fa_zoom_reset):
            btn.configure(bg=t.zoom_btn_bg, fg=t.text_strong, activebackground=t.border)
        self._stream_label.configure(bg=t.panel, fg=t.text_strong)
        self.stream_text.configure(bg=t.stream_bg, fg=t.text_strong)
        self.stream_text.tag_configure("error_token", foreground=t.error, font=("Consolas", 9, "bold"))
        self.token_tree.tag_configure(
            "error_token", background=t.tree_error_bg, foreground=t.tree_error_fg
        )
        self._fa_legend_title.configure(bg=t.panel, fg=t.text_strong)
        for sw, color in zip(
            self._fa_legend_swatches,
            (t.fa_start, t.fa_normal, t.fa_final, t.fa_warn, t.fa_dead),
            strict=True,
        ):
            sw.configure(bg=color, fg=t.fa_label)
        if minimal:
            self._fa_legend.pack_forget()
        elif not self._fa_legend.winfo_ismapped():
            self._fa_legend.pack(fill=tk.X, pady=(0, 4), before=self._fa_canvas_wrap)
        self.fa_canvas.configure(bg=t.canvas_bg, highlightbackground=t.border)

        # AST tab
        for frame in (
            self._ast_frame,
            self._ast_toggle,
            self.zoom_controls,
            self.ast_body,
            self.ast_tree_frame,
            self.ast_diagram_frame,
        ):
            frame.configure(bg=t.panel)
        self.syntax_status.configure(bg=t.panel)
        self.syntax_tip.configure(bg=t.tip_bg, fg=t.tip_fg)
        self._ast_view_label.configure(bg=t.panel, fg=t.muted)
        for rb in (self._ast_radio_tree, self._ast_radio_diagram):
            rb.configure(
                bg=t.panel,
                fg=t.text_strong,
                activebackground=t.panel,
                activeforeground=t.text_strong,
                selectcolor=t.check_select,
            )
        self._ast_zoom_label.configure(bg=t.panel, fg=t.muted)
        self._ast_zoom_pct.configure(bg=t.panel, fg=t.text_strong)
        for btn in (self._ast_zoom_minus, self._ast_zoom_plus, self._ast_zoom_reset):
            btn.configure(bg=t.zoom_btn_bg, fg=t.text_strong, activebackground=t.border)
        self.ast_canvas.configure(bg=t.canvas_bg, highlightbackground=t.border)

        # Summary / output / status
        self._summary_frame.configure(bg=t.panel)
        self.summary_text.configure(bg=t.summary_bg, fg=t.text_strong)
        self._output_frame.configure(bg=t.panel)
        self.output_status.configure(bg=t.panel)
        self.output_text.configure(bg=t.code_bg, fg=t.code_fg)
        self._status_bar.configure(bg=t.status_bg, pady=2 if minimal else 4)
        self._status_label.configure(bg=t.status_bg, fg=t.status_fg)

        # Redraw diagrams with new palette
        if self._fa_trace is not None:
            self._draw_fa_diagram(self._fa_trace)
        if self._ast_statements:
            self._draw_ast_diagram(self._ast_statements)

        mode = t.label + (" + Minimal" if minimal else "")
        current = self.status_var.get()
        if current.startswith(("Ready", "Theme:", "Cleared")):
            self.status_var.set(f"Theme: {mode}")
    def _show_about(self) -> None:
        t = self.theme
        win = tk.Toplevel(self)
        win.title("Know more about this software")
        win.geometry("720x560")
        win.minsize(520, 400)
        win.configure(bg=t.panel)
        win.transient(self)

        header = tk.Frame(win, bg=t.accent, padx=16, pady=12)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="PNC Language Analysis Simulator — User Manual",
            font=("Segoe UI", 13, "bold"),
            bg=t.accent,
            fg="white",
        ).pack(anchor=tk.W)
        tk.Label(
            header,
            text="Capabilities, keywords, data types, scopes & limitations",
            font=("Segoe UI", 9),
            bg=t.accent,
            fg=t.header_sub,
        ).pack(anchor=tk.W, pady=(2, 0))

        body = tk.Frame(win, bg=t.panel)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        text = tk.Text(
            body,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=t.summary_bg,
            fg=t.text_strong,
            padx=12,
            pady=12,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=t.border,
        )
        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.insert("1.0", _ABOUT_MANUAL)
        text.configure(state=tk.DISABLED)

        footer = tk.Frame(win, bg=t.panel, padx=12, pady=8)
        footer.pack(fill=tk.X)
        tk.Button(
            footer,
            text="Close",
            command=win.destroy,
            font=("Segoe UI", 9),
            padx=16,
            pady=4,
            cursor="hand2",
            bg=t.accent,
            fg="white",
            activebackground=t.accent_hover,
            activeforeground="white",
            relief=tk.FLAT,
        ).pack(side=tk.RIGHT)


def launch_gui(initial_source: str = "", initial_path: str | None = None) -> None:
    app = SimulatorApp(initial_source=initial_source, initial_path=initial_path)
    app.mainloop()


def launch_gui_with_file(path: str) -> None:
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        messagebox.showerror("File Not Found", f"Could not find: {path}")
        launch_gui()
        return
    if p.suffix.lower() != ".pnc":
        messagebox.showwarning("Not a PNC File", f"Expected a .pnc file, got {p.suffix!r}")
        launch_gui()
        return
    source = p.read_text(encoding="utf-8")
    launch_gui(initial_source=source, initial_path=str(p))
