"""
TinyCStr Level 1 Lexer -- REFERENCE IMPLEMENTATION for Week 3.

This is a verified, working Level 1 lexer (Stages 1a + 1b). It is provided
here, already complete, so that Week 3 is graded on PARSER correctness
in isolation -- if your own Week 2 tinycstr_lexer.py still has a bug,
importing your own copy here would make a lexer bug look like a parser
bug. Use this file as-is; you do not need to modify it
this week.
"""
from sly import Lexer
import sys


class TinyCStrLexer(Lexer):
    tokens = {
        INT, ID, NUMBER, PRINT, ASSIGN, SEMICOLON, LBRACE, RBRACE, COMMA,
        PLUS, MINUS, TIMES, DIVIDE, REMAINDER, LPAREN, RPAREN,
    }
    ignore = ' \t'
    ignore_COMMENT = r'//.*'

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    keywords = {'int': 'INT', 'print': 'PRINT'}

    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def ID(self, t):
        t.type = self.keywords.get(t.value, 'ID')
        return t

    NUMBER = r'\d+'
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

    def __init__(self, error_sink=None):
        self.error_sink = error_sink if error_sink is not None else sys.stdout

    def error(self, t):
        print(f"ERROR {t.value[0]} {self.lineno}", file=self.error_sink)
        self.index += 1
