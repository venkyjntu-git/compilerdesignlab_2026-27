"""
TinyCStr Level 3 Parser (Stages 3a -> 3b)

Read docs/level3_grammar_reference.md and docs/sly_help3.md before
editing this file.

The Level 1 and Level 2 grammar is complete (carried over from Week 7) --
leave it alone. Your work is in the "LEVEL 3" TODOs, staged:

  Stage 3a -- plain `if ( expr ) stmt` (no else) and blocks `{ ... }`.
              One new grammar pattern, no ambiguity to resolve.
  Stage 3b -- `else`, `while ( expr ) stmt`, global declarations, and
              the dangling-else ambiguity, resolved EXPLICITLY.

Get Stage 3a's tests passing (tests/test10.tc) before starting 3b.
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
        # TODO(week-8, stage-3b): resolve the dangling-else conflict. Add
        # TWO entries at the very TOP of this tuple, in this order:
        #     ('nonassoc', 'IFX'),     <- dummy token, never produced by the lexer
        #     ('nonassoc', 'ELSE'),
        # and put `%prec IFX` at the end of the no-else if rule's string.
        # The ORDER of these two lines is the whole fix -- read
        # docs/sly_help3.md #4 first, including what happens if you swap them.
        ('right', 'QUESTION', 'COLON'),
        ('left', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'UCAST'),
    )

    def __init__(self):
        self.had_error = False

    # ------------------------------------------------------------------
    # Program structure
    # ------------------------------------------------------------------
    # TODO(week-8, stage-3b): global declarations. Replace this
    # `program : func_def` rule with
    #
    #     program          : global_decl_list func_def
    #     global_decl_list : global_decl_list decl
    #                      | empty
    #
    # (same shape as decl_stmt_list below -- reuse the existing `decl`
    # rules, don't write new ones). In the `program` action, add each
    # SymbolTableEntry from value[0] to prog.getGlobalSymbolTable(), then
    # add the function. See docs/sly_help3.md #5 for why `int a;` and
    # `int main(){` don't conflict even though both start with INT.
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
    # TODO(week-8, stage-3a): two new `stmt` alternatives, `if_stmt` and
    # `block`, each just returning value[0] -- same pattern as the
    # `assign` / `print_stmt` alternatives just above.
    #
    # TODO(week-8, stage-3a): the block rule
    #     block : LBRACE stmt_list RBRACE      -> Block(value[1], lineno=value.lineno)
    # Reuse the existing stmt_list. A block holds statements only -- no
    # declarations inside a block at Level 3 (docs/level3_grammar_reference.md).
    #
    # TODO(week-8, stage-3a): the no-else if rule
    #     if_stmt : IF LPAREN expr RPAREN stmt -> If(value[2], value[4], lineno=value.lineno)
    # Note the branch is a `stmt`, not a stmt_list: one statement, or one
    # block. That is what makes the statement grammar recursive.
    # (In Stage 3b you will append `%prec IFX` to this rule's string.)

    # ------------------------------------------------------------------
    # LEVEL 3, Stage 3b -- else, while
    # ------------------------------------------------------------------
    # TODO(week-8, stage-3b): the if-else rule
    #     if_stmt : IF LPAREN expr RPAREN stmt ELSE stmt
    #               -> If(value[2], value[4], value[6], lineno=value.lineno)
    # As soon as this rule exists, SLY prints "WARNING: 1 shift/reduce
    # conflict". Do not ignore it: docs/sly_help3.md #3-#4 explains what
    # it is and how to remove it.
    #
    # TODO(week-8, stage-3b): the while loop -- one more `stmt`
    # alternative (`while_stmt`) plus
    #     while_stmt : WHILE LPAREN expr RPAREN stmt
    #                  -> While(value[2], value[4], lineno=value.lineno)

    # ------------------------------------------------------------------
    # LEVEL 1 / LEVEL 2 statements and expressions -- unchanged, do not modify
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
