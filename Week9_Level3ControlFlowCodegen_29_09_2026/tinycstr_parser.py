"""
TinyCStr Level 3 Parser -- REFERENCE IMPLEMENTATION, fully complete.

Level 2 parser (Stages 1 + 2a + 2b + 2c) plus Level 3:
  Stage 3a -- plain `if ( expr ) stmt` and block statements `{ ... }`
  Stage 3b -- `else`, `while ( expr ) stmt`, global declarations, and
              the dangling-else ambiguity resolved via %prec.
"""
from sly import Parser

from tinycstr_lexer import TinyCStrLexer
from ast_nodes import (Const, Var, Assign, Print, BinOp, RelOp, Cast, Ternary,
                       If, While, Block)
from SymbolTable import SymbolTableEntry, DataType
from Function import Function
from Program import Program


class TinyCStrParser(Parser):
    tokens = TinyCStrLexer.tokens

    precedence = (
        # LEVEL 3, Stage 3b -- dangling else. IFX is a dummy token (never
        # produced by the lexer) given to the no-else `if` rule via %prec.
        # ELSE is listed AFTER (= higher than) IFX, so on the conflict
        # "reduce `IF ( expr ) stmt` or shift ELSE?" SLY shifts: the else
        # binds to the NEAREST unmatched if, as in C.
        ('nonassoc', 'IFX'),
        ('nonassoc', 'ELSE'),
        # LEVEL 2
        ('right', 'QUESTION', 'COLON'),
        ('left', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'UCAST'),
    )

    def __init__(self):
        self.had_error = False

    # ------------------------------------------------------------------
    # Program structure -- LEVEL 3, Stage 3b: optional global declarations
    # before the (single, for Level 3) function definition.
    # ------------------------------------------------------------------
    @_('global_decl_list func_def')
    def program(self, value):
        prog = Program()
        for entry in value[0]:
            prog.getGlobalSymbolTable().addSymbol(entry)
        prog.addFunction(value[1])
        return prog

    @_('global_decl_list decl')
    def global_decl_list(self, value):
        return value[0] + value[1]

    @_('empty')
    def global_decl_list(self, value):
        return []

    @_('INT ID LPAREN RPAREN LBRACE decl_stmt_list stmt_list RBRACE')
    def func_def(self, value):
        func = Function(DataType.INT, value[1])
        for entry in value[5]:
            func.getLocalSymbolTable().addSymbol(entry)
        for stmt in value[6]:
            func.addStatement(stmt)
        return func

    @_('decl_stmt_list decl')
    def decl_stmt_list(self, value):
        return value[0] + value[1]

    @_('empty')
    def decl_stmt_list(self, value):
        return []

    @_('stmt_list stmt')
    def stmt_list(self, value):
        return value[0] + [value[1]]

    @_('empty')
    def stmt_list(self, value):
        return []

    @_('')
    def empty(self, value):
        pass

    @_('INT id_list SEMICOLON')
    def decl(self, value):
        return [SymbolTableEntry(name, DataType.INT) for name in value[1]]

    @_('DOUBLE id_list SEMICOLON')
    def decl(self, value):
        return [SymbolTableEntry(name, DataType.DOUBLE) for name in value[1]]

    @_('CHAR id_list SEMICOLON')
    def decl(self, value):
        return [SymbolTableEntry(name, DataType.CHAR) for name in value[1]]

    @_('STRING id_list SEMICOLON')
    def decl(self, value):
        return [SymbolTableEntry(name, DataType.STRING) for name in value[1]]

    @_('id_list COMMA ID')
    def id_list(self, value):
        return value[0] + [value[2]]

    @_('ID')
    def id_list(self, value):
        return [value[0]]

    @_('assign')
    def stmt(self, value):
        return value[0]

    @_('print_stmt')
    def stmt(self, value):
        return value[0]

    # ------------------------------------------------------------------
    # LEVEL 3, Stage 3a -- plain if (no else), block statements
    # ------------------------------------------------------------------
    @_('if_stmt')
    def stmt(self, value):
        return value[0]

    @_('block')
    def stmt(self, value):
        return value[0]

    @_('LBRACE stmt_list RBRACE')
    def block(self, value):
        return Block(value[1], lineno=value.lineno)

    @_('IF LPAREN expr RPAREN stmt %prec IFX')
    def if_stmt(self, value):
        return If(value[2], value[4], lineno=value.lineno)

    # ------------------------------------------------------------------
    # LEVEL 3, Stage 3b -- else, while
    # ------------------------------------------------------------------
    @_('IF LPAREN expr RPAREN stmt ELSE stmt')
    def if_stmt(self, value):
        return If(value[2], value[4], value[6], lineno=value.lineno)

    @_('while_stmt')
    def stmt(self, value):
        return value[0]

    @_('WHILE LPAREN expr RPAREN stmt')
    def while_stmt(self, value):
        return While(value[2], value[4], lineno=value.lineno)

    # ------------------------------------------------------------------
    # LEVEL 1 / LEVEL 2 statements and expressions (unchanged)
    # ------------------------------------------------------------------
    @_('ID ASSIGN expr SEMICOLON')
    def assign(self, value):
        return Assign(Var(value[0], lineno=value.lineno), value[2], lineno=value.lineno)

    @_('PRINT expr SEMICOLON')
    def print_stmt(self, value):
        return Print(value[1], lineno=value.lineno)

    @_('NUMBER')
    def expr(self, value):
        return Const(value[0], DataType.INT, lineno=value.lineno)

    @_('ID')
    def expr(self, value):
        return Var(value[0], lineno=value.lineno)

    @_('expr PLUS expr')
    def expr(self, value):
        return BinOp('+', value[0], value[2], lineno=value.lineno)

    @_('expr MINUS expr')
    def expr(self, value):
        return BinOp('-', value[0], value[2], lineno=value.lineno)

    @_('expr TIMES expr')
    def expr(self, value):
        return BinOp('*', value[0], value[2], lineno=value.lineno)

    @_('expr DIVIDE expr')
    def expr(self, value):
        return BinOp('/', value[0], value[2], lineno=value.lineno)

    @_('LPAREN expr RPAREN')
    def expr(self, value):
        return value[1]

    @_('REAL_CONST')
    def expr(self, value):
        return Const(value[0], DataType.DOUBLE, lineno=value.lineno)

    @_('CHAR_CONST')
    def expr(self, value):
        return Const(value[0], DataType.CHAR, lineno=value.lineno)

    @_('STRING_CONST')
    def expr(self, value):
        return Const(value[0], DataType.STRING, lineno=value.lineno)

    @_('expr LT expr')
    def expr(self, value):
        return RelOp('<', value[0], value[2], lineno=value.lineno)

    @_('expr GT expr')
    def expr(self, value):
        return RelOp('>', value[0], value[2], lineno=value.lineno)

    @_('expr LE expr')
    def expr(self, value):
        return RelOp('<=', value[0], value[2], lineno=value.lineno)

    @_('expr GE expr')
    def expr(self, value):
        return RelOp('>=', value[0], value[2], lineno=value.lineno)

    @_('expr EQ expr')
    def expr(self, value):
        return RelOp('==', value[0], value[2], lineno=value.lineno)

    @_('expr NE expr')
    def expr(self, value):
        return RelOp('!=', value[0], value[2], lineno=value.lineno)

    @_('LPAREN DOUBLE RPAREN expr %prec UCAST')
    def expr(self, value):
        return Cast(DataType.DOUBLE, value[3], lineno=value.lineno)

    @_('LPAREN INT RPAREN expr %prec UCAST')
    def expr(self, value):
        return Cast(DataType.INT, value[3], lineno=value.lineno)

    @_('expr QUESTION expr COLON expr')
    def expr(self, value):
        return Ternary(value[0], value[2], value[4], lineno=value.lineno)

    def error(self, token):
        self.had_error = True
        if token:
            print(f"[parser] Syntax error near '{token.value}' at line {token.lineno}")
        else:
            print("[parser] Syntax error at end of input")
