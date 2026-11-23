"""
TinyCStr Level 3 Lexer (Stages 3a -> 3b)

Read docs/level3_grammar_reference.md and docs/sly_help3.md before
editing this file.

Levels 1 and 2 are complete (carried over from Week 7) -- leave them
alone. Your work is in the "LEVEL 3" TODOs below: three new keywords,
staged 3a -> 3b the same way Week 5 staged 2a -> 2b -> 2c.
"""
from sly import Lexer
import sys


class TinyCStrLexer(Lexer):
    tokens = {
        # ---- LEVEL 1 (unchanged) ----
        INT, ID, NUMBER, PRINT, ASSIGN, SEMICOLON, LBRACE, RBRACE, COMMA,
        PLUS, MINUS, TIMES, DIVIDE, REMAINDER, LPAREN, RPAREN,
        # ---- LEVEL 2 (unchanged) ----
        DOUBLE, REAL_CONST,
        CHAR, STRING, CHAR_CONST, STRING_CONST, LT, GT, LE, GE, EQ, NE,
        QUESTION, COLON,
        # ---- LEVEL 3 (this week) -- already declared for you ----
        IF, ELSE, WHILE,
    }

    ignore = ' \t'
    ignore_COMMENT = r'//.*'

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    keywords = {
        'int': 'INT',
        'print': 'PRINT',
        'double': 'DOUBLE',
        'char': 'CHAR',
        'string': 'STRING',
        # TODO(week-8, stage-3a): add 'if': 'IF'
        #
        # TODO(week-8, stage-3b): add 'else': 'ELSE' and 'while': 'WHILE'
        #
        # That is the ENTIRE lexer change for Level 3. Do NOT write
        # separate rules like `IF = r'if'` -- see docs/sly_help3.md #1 for
        # why that would wrongly split an identifier such as `iffy` or
        # `whileCount` into a keyword plus an identifier.
    }

    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def ID(self, t):
        t.type = self.keywords.get(t.value, 'ID')
        return t

    @_(r'\d+\.\d+')
    def REAL_CONST(self, t):
        t.value = float(t.value)
        return t

    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    @_(r"'.'")
    def CHAR_CONST(self, t):
        t.value = t.value[1:-1]
        return t

    @_(r'"[^"]*"')
    def STRING_CONST(self, t):
        t.value = t.value[1:-1]
        return t

    LE = r'<='
    GE = r'>='
    EQ = r'=='
    NE = r'!='
    LT = r'<'
    GT = r'>'
    ASSIGN = r'='
    SEMICOLON = r';'
    LBRACE = r'\{'
    RBRACE = r'\}'
    COMMA = r','
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    REMAINDER = r'%'
    LPAREN = r'\('
    RPAREN = r'\)'
    QUESTION = r'\?'
    COLON = r':'

    def __init__(self, error_sink=None):
        self.error_sink = error_sink if error_sink is not None else sys.stdout

    def error(self, t):
        print(f"ERROR {t.value[0]} {self.lineno}", file=self.error_sink)
        self.index += 1
