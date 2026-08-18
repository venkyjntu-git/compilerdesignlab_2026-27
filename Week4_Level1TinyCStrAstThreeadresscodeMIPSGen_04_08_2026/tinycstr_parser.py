"""
TinyCStr Level 1 Parser -- fully implemented.

Use this file as-is; you do not need to modify it
this week.

"""
from sly import Parser

from tinycstr_lexer import TinyCStrLexer
from ast_nodes import Num, Var, Assign, Print, BinOp
from SymbolTable import SymbolTableEntry, DataType
from Function import Function
from Program import Program


class TinyCStrParser(Parser):
    tokens = TinyCStrLexer.tokens

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
    )

    def __init__(self):
        self.had_error = False

    @_('func_def')
    def program(self, p):
        prog = Program()
        prog.addFunction(p.func_def)
        return prog

    @_('INT ID LPAREN RPAREN LBRACE decl_stmt_list stmt_list RBRACE')
    def func_def(self, p):
        func = Function(DataType.INT, p.ID)
        for entry in p.decl_stmt_list:
            func.getLocalSymbolTable().addSymbol(entry)
        for stmt in p.stmt_list:
            func.addStatement(stmt)
        return func

    @_('decl_stmt_list decl')
    def decl_stmt_list(self, p):
        return p.decl_stmt_list + p.decl

    @_('empty')
    def decl_stmt_list(self, p):
        return []

    @_('stmt_list stmt')
    def stmt_list(self, p):
        return p.stmt_list + [p.stmt]

    @_('empty')
    def stmt_list(self, p):
        return []

    @_('')
    def empty(self, p):
        pass

    @_('INT id_list SEMICOLON')
    def decl(self, p):
        return [SymbolTableEntry(name, DataType.INT) for name in p.id_list]

    @_('id_list COMMA ID')
    def id_list(self, p):
        return p.id_list + [p.ID]

    @_('ID')
    def id_list(self, p):
        return [p.ID]

    @_('assign')
    def stmt(self, p):
        return p.assign

    @_('print_stmt')
    def stmt(self, p):
        return p.print_stmt

    @_('ID ASSIGN expr SEMICOLON')
    def assign(self, p):
        return Assign(Var(p.ID), p.expr)

    @_('PRINT expr SEMICOLON')
    def print_stmt(self, p):
        return Print(p.expr)

    @_('NUMBER')
    def expr(self, p):
        return Num(int(p.NUMBER))

    @_('ID')
    def expr(self, p):
        return Var(p.ID)

    @_('expr PLUS expr')
    def expr(self, p):
        return BinOp('+', p.expr0, p.expr1)

    @_('expr MINUS expr')
    def expr(self, p):
        return BinOp('-', p.expr0, p.expr1)

    @_('expr TIMES expr')
    def expr(self, p):
        return BinOp('*', p.expr0, p.expr1)

    @_('expr DIVIDE expr')
    def expr(self, p):
        return BinOp('/', p.expr0, p.expr1)

    @_('LPAREN expr RPAREN')
    def expr(self, p):
        return p.expr

    def error(self, token):
        self.had_error = True
        if token:
            print(f"[parser] Syntax error near '{token.value}' at line {token.lineno}")
        else:
            print("[parser] Syntax error at end of input")
