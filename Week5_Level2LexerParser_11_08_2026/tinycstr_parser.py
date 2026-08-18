"""
TinyCStr Level 2 Parser (Stages 2a -> 2c)

Read docs/level2_token_reference.md and docs/sly_help2.md
before editing this file.

 "LEVEL 2": staged 2a -> 2b -> 2c. Get each stage's tests passing before starting
the next.

"""
from sly import Parser

from tinycstr_lexer import TinyCStrLexer
from ast_nodes import Const, Var, Assign, Print, BinOp, RelOp, Cast, Ternary
from SymbolTable import SymbolTableEntry, DataType
from Function import Function
from Program import Program


class TinyCStrParser(Parser):
    tokens = TinyCStrLexer.tokens

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        # TODO(week-5, stage-2b): relational operators less precedence than
        # arithmetic so their precedence entry must be
        # ADDED ABOVE the two lines already here, not below -- remember
        # SLY's tuple order is low-to-high, entries LOWER in the tuple
        # having more predecence. See docs/sly_help2.md #3.
        #
        # TODO(week-5, stage-2c): ternary less predence than
        # relational -- its precedence entry goes even further above
        # (i.e. is the very FIRST entry in the tuple). See
        # docs/sly_help2.md #4.
        #
        # TODO(week-5, stage-2c): cast higher precedence than everything
        # else (it's essentially a unary, prefix operator) -- needs a
        # dummpy precedence token added as the LAST (highest) entry
        # in this tuple. See docs/sly_help2.md #5 for the
        # exact idiom (SLY's %prec mechanism)
    )

    def __init__(self):
        self.had_error = False

    @_('func_def')
    def program(self, value):
        prog = Program()
        prog.addFunction(value[0])
        return prog

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

    # TODO(week-5, stage-2a): add a `decl` alternative for
    # `DOUBLE id_list SEMICOLON`, producing SymbolTableEntry objects
    # with DataType.DOUBLE -- same shape as the INT rule just above,
    # different keyword token and DataType value.
    #
    # TODO(week-5, stage-2b): add two more `decl` alternatives, for
    # `CHAR id_list SEMICOLON` (DataType.CHAR) and
    # `STRING id_list SEMICOLON` (DataType.STRING).

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

    @_('ID ASSIGN expr SEMICOLON')
    def assign(self, value):
        return Assign(Var(value[0]), value[2])

    @_('PRINT expr SEMICOLON')
    def print_stmt(self, value):
        return Print(value[1])

    @_('NUMBER')
    def expr(self, value):
        return Const(value[0], DataType.INT)

    @_('ID')
    def expr(self, value):
        return Var(value[0])

    @_('expr PLUS expr')
    def expr(self, value):
        return BinOp('+', value[0], value[2])

    @_('expr MINUS expr')
    def expr(self, value):
        return BinOp('-', value[0], value[2])

    @_('expr TIMES expr')
    def expr(self, value):
        return BinOp('*', value[0], value[2])

    @_('expr DIVIDE expr')
    def expr(self, value):
        return BinOp('/', value[0], value[2])

    @_('LPAREN expr RPAREN')
    def expr(self, value):
        return value[1]

    # ------------------------------------------------------------------
    # LEVEL 2, Stage 2a -- real constants
    # ------------------------------------------------------------------
    # TODO(week-5, stage-2a): add an `expr` alternative for ,
    # producing Const(<value>, <doubletype>) -- REAL_CONST's token value is
    # already a Python float (the lexer converts it)


    # ------------------------------------------------------------------
    # LEVEL 2, Stage 2b -- char/string constants, relational operators
    # ------------------------------------------------------------------
    # TODO(week-5, stage-2b): add `expr` alternatives for CHAR_CONST and
    # STRING_CONST, each producing Const(<the token's already-unquoted value>,type).
    #
    # TODO(week-5, stage-2b): add SIX `expr` alternatives, one per
    # relational operator (`expr LT expr`, `expr GT expr`, `expr LE expr`,
    # `expr GE expr`, `expr EQ expr`, `expr NE expr`), each producing
    # RelOp(<the operator as a string, e.g. '<'>, value[0], value[2]) --
    # same pattern as the four BinOp rules above.

    # ------------------------------------------------------------------
    # LEVEL 2, Stage 2c -- casts and ternary
    # ------------------------------------------------------------------
    # TODO(week-5, stage-2c): add TWO `expr` alternatives for casts:
    #   `LPAREN DOUBLE RPAREN expr` -> Cast(DataType.DOUBLE, value[3])
    #   `LPAREN INT RPAREN expr`    -> Cast(DataType.INT, value[3])
    # Both need the `%prec` dummpy-token suffix from the precedence
    
    # TODO(week-5, stage-2c): add ONE `expr` alternative for the ternary
    # operator: `expr QUESTION expr COLON expr` ->
    # Ternary(value[0], value[2], value[4])
    
    def error(self, token):
        self.had_error = True
        if token:
            print(f"[parser] Syntax error near '{token.value}' at line {token.lineno}")
        else:
            print("[parser] Syntax error at end of input")
