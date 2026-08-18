"""
TinyCStr Level 2 Lexer (Stages 2a -> 2c)

Read docs/level2_token_reference.md and docs/sly_help2.md
before editing this file.

goto "LEVEL 2" section: add the new keywords, literal tokens, and 
operator tokens for Stages 2a, 2b, and
2c, staged the same way Week 2's Stage 1a/1b split worked -- get Stage
2a's tests passing before starting Stage 2b, and so on.
"""
from sly import Lexer
import sys


class TinyCStrLexer(Lexer):
    tokens = {
        # ---- LEVEL 1 (unchanged) ----
        INT, ID, NUMBER, PRINT, ASSIGN, SEMICOLON, LBRACE, RBRACE, COMMA,
        PLUS, MINUS, TIMES, DIVIDE, REMAINDER, LPAREN, RPAREN,
        # ---- LEVEL 2 (this week) ----
        DOUBLE, REAL_CONST, CHAR, STRING, CHAR_CONST, STRING_CONST,
        LT, GT, LE, GE, EQ, NE, 
        QUESTION, COLON 
        # week-5, stage-2a: add DOUBLE, REAL_CONST to this set.
        # week-5, stage-2b: add CHAR, STRING, CHARLIT, STRINGLIT,
        #   LT, GT, LE, GE, EQ, NE to this set.
        # week-5, stage-2c): add QUESTION, COLON to this set.
    }

    ignore = ' \t'
    ignore_COMMENT = r'//.*'

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    # ------------------------------------------------------------------
    # LEVEL 1 -- unchanged, do not modify
    # ------------------------------------------------------------------
    keywords = {
        'int': 'INT',
        'print': 'PRINT',
        # TODO(week-5, stage-2a): add 'double': 'DOUBLE'
        # TODO(week-5, stage-2b): add 'char': 'CHAR', 'string': 'STRING'
    }

    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def ID(self, t):
        t.type = self.keywords.get(t.value, 'ID')
        return t

    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t
    
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

    # ------------------------------------------------------------------
    # LEVEL 2, Stage 2a -- real constants
    # ------------------------------------------------------------------
    # TODO(week-5, stage-2a): real , e.g. "3.14". Must
    # be a FUNCTION-style rule (not a plain string attribute) so you can
    # convert the matched text to a real Python float before the token
    # reaches the parser -- see docs/sly_help2.md #1 for why
    # this has to be function-style, not just a style preference.
    #
    # @_(r'\d+\.\d+')
    # def REAL_CONST(self, t):
    #     t.value = float(t.value)
    #     return t

    # ------------------------------------------------------------------
    # LEVEL 2, Stage 2b -- char/string constants, relational operators
    # ------------------------------------------------------------------
    # TODO(week-5, stage-2b): CHAR_CONST -- a single character in single
    # quotes, e.g. 'x'. Function-style rule, strip the surrounding
    # quotes before returning (t.value = t.value[1:-1]).
    #
    # TODO(week-5, stage-2b): STRING_CONST -- zero or more non-quote
    # characters in double quotes, e.g. "hello". Function-style rule,
    # strip the surrounding quotes the same way. (No escape-sequence
    # handling needed for Level 2 -- \" inside a string is out of scope.)
    #
    # TODO(week-5, stage-2b): six relational operators as plain string
    # attributes: LT (<), GT (>), LE (<=), GE (>=), EQ (==), NE (!=).
    # See docs/sly_help2.md #2 for why you do NOT need to
    # worry about `<=` being mis-tokenized as `<` then `=` -- SLY's
    # ordering already handles it correctly as long as these stay plain
    # string attributes (not function rules).

    # ------------------------------------------------------------------
    # LEVEL 2, Stage 2c -- ternary operator tokens
    # ------------------------------------------------------------------
    # TODO(week-5, stage-2c): QUESTION (?) and COLON (:) as plain string
    # attributes. That's the entire lexer change for Stage 2c 

    def __init__(self, error_sink=None):
        self.error_sink = error_sink if error_sink is not None else sys.stdout

    def error(self, t):
        print(f"ERROR {t.value[0]} {self.lineno}", file=self.error_sink)
        self.index += 1
