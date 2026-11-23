"""
TinyCStr Level 4 Lexer (Stages 4a -> 4b)

Levels 1-3 are complete (Week 8's exercise). Your work: two keywords, in
the `keywords` table -- the same mechanism as Week 8's if/else/while.
"""
from sly import Lexer
import sys


class TinyCStrLexer(Lexer):
    tokens = {
        # ---- LEVEL 1 ----
        INT, ID, NUMBER, PRINT, ASSIGN, SEMICOLON, LBRACE, RBRACE, COMMA,
        PLUS, MINUS, TIMES, DIVIDE, REMAINDER, LPAREN, RPAREN,
        # ---- LEVEL 2 ----
        DOUBLE, REAL_CONST,
        CHAR, STRING, CHAR_CONST, STRING_CONST, LT, GT, LE, GE, EQ, NE,
        QUESTION, COLON,
        # ---- LEVEL 3 ----
        IF, ELSE, WHILE,
        # ---- LEVEL 4 (this week) -- already declared for you ----
        VOID, RETURN,
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
        # LEVEL 3, Stage 3a
        'if': 'IF',
        # LEVEL 3, Stage 3b
        'else': 'ELSE',
        'while': 'WHILE',
        # TODO(week-10, stage-4a): add 'void': 'VOID'
        # TODO(week-10, stage-4b): add 'return': 'RETURN'
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
