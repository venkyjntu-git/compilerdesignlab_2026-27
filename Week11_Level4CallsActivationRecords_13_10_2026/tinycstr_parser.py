"""
TinyCStr Level 4 Parser -- REFERENCE IMPLEMENTATION, fully complete.

Level 3 parser plus Level 4:
  Stage 4a -- several functions (incl. `void` ones) with NO parameters,
              and calls `f()` as a statement or an expression.
  Stage 4b -- typed parameter lists, prototypes (`int add(int,int);`),
              call arguments, and `return`.
"""
from sly import Parser

from tinycstr_lexer import TinyCStrLexer
from ast_nodes import (Const, Var, Assign, Print, BinOp, RelOp, Cast, Ternary,
                       If, While, Block, FunctionCall, Return)
from SymbolTable import SymbolTableEntry, DataType
from Function import Function
from Program import Program, FunctionPrototype


class TinyCStrParser(Parser):
    tokens = TinyCStrLexer.tokens

    precedence = (
        ('nonassoc', 'IFX'),
        ('nonassoc', 'ELSE'),
        ('right', 'QUESTION', 'COLON'),
        ('left', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'UCAST'),
    )

    def __init__(self):
        self.had_error = False

    # ------------------------------------------------------------------
    # Program structure -- LEVEL 4
    #   program          : global_decl_list func_def_list
    #   global_decl_list : (global variable decls and prototypes)*
    #   func_def_list    : func_def+
    # ------------------------------------------------------------------
    @_('global_decl_list func_def_list')
    def program(self, value):
        prog = Program()
        for item in value[0]:
            if isinstance(item, FunctionPrototype):
                prog.addPrototype(item)
            else:
                prog.getGlobalSymbolTable().addSymbol(item)
        for func in value[1]:
            prog.addFunction(func)
        return prog

    @_('global_decl_list decl')
    def global_decl_list(self, value):
        return value[0] + value[1]

    @_('global_decl_list func_proto')       # Stage 4b
    def global_decl_list(self, value):
        return value[0] + [value[1]]

    @_('empty')
    def global_decl_list(self, value):
        return []

    @_('func_def_list func_def')
    def func_def_list(self, value):
        return value[0] + [value[1]]

    @_('func_def')
    def func_def_list(self, value):
        return [value[0]]

    # ------------------------------------------------------------------
    # Types. WEEK 10: every declaration now goes through ONE `type`
    # nonterminal (docs/sly_help4.md #2 explains the conflict that the old
    # INT/DOUBLE/CHAR/STRING-specific decl rules would cause).
    # ------------------------------------------------------------------
    @_('INT')
    def type(self, value):
        return DataType.INT

    @_('DOUBLE')
    def type(self, value):
        return DataType.DOUBLE

    @_('CHAR')
    def type(self, value):
        return DataType.CHAR

    @_('STRING')
    def type(self, value):
        return DataType.STRING

    @_('type id_list SEMICOLON')
    def decl(self, value):
        return [SymbolTableEntry(name, value[0]) for name in value[1]]

    @_('id_list COMMA ID')
    def id_list(self, value):
        return value[0] + [value[2]]

    @_('ID')
    def id_list(self, value):
        return [value[0]]

    # ------------------------------------------------------------------
    # Functions -- a shared header, then either `;` (prototype) or a body
    # func_head's value is a tuple (return_type, name, params, lineno).
    # ------------------------------------------------------------------
    @_('type ID LPAREN params_opt RPAREN')
    def func_head(self, value):
        return (value[0], value[1], value[3], value.lineno)

    @_('VOID ID LPAREN params_opt RPAREN')
    def func_head(self, value):
        return (DataType.VOID, value[1], value[3], value.lineno)

    @_('param_list')                        # Stage 4b
    def params_opt(self, value):
        return value[0]

    @_('empty')
    def params_opt(self, value):
        return []

    @_('param_list COMMA param')
    def param_list(self, value):
        return value[0] + [value[2]]

    @_('param')
    def param_list(self, value):
        return [value[0]]

    @_('type ID')
    def param(self, value):
        return (value[0], value[1])

    @_('type')
    def param(self, value):
        return (value[0], None)              # unnamed -- legal in a prototype only

    @_('func_head SEMICOLON')               # Stage 4b
    def func_proto(self, value):
        rtype, name, params, lineno = value[0]
        return FunctionPrototype(rtype, name, params, lineno=lineno)

    @_('func_head LBRACE decl_stmt_list stmt_list RBRACE')
    def func_def(self, value):
        rtype, name, params, lineno = value[0]
        func = Function(rtype, name, params, lineno=lineno)
        for entry in value[2]:
            func.getLocalSymbolTable().addSymbol(entry)
        for stmt in value[3]:
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

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------
    @_('assign', 'print_stmt', 'if_stmt', 'block', 'while_stmt',
       'call_stmt', 'return_stmt')
    def stmt(self, value):
        return value[0]

    @_('LBRACE stmt_list RBRACE')
    def block(self, value):
        return Block(value[1], lineno=value.lineno)

    @_('IF LPAREN expr RPAREN stmt %prec IFX')
    def if_stmt(self, value):
        return If(value[2], value[4], lineno=value.lineno)

    @_('IF LPAREN expr RPAREN stmt ELSE stmt')
    def if_stmt(self, value):
        return If(value[2], value[4], value[6], lineno=value.lineno)

    @_('WHILE LPAREN expr RPAREN stmt')
    def while_stmt(self, value):
        return While(value[2], value[4], lineno=value.lineno)

    @_('ID ASSIGN expr SEMICOLON')
    def assign(self, value):
        return Assign(Var(value[0], lineno=value.lineno), value[2], lineno=value.lineno)

    @_('PRINT expr SEMICOLON')
    def print_stmt(self, value):
        return Print(value[1], lineno=value.lineno)

    # LEVEL 4, Stage 4a -- a call used as a statement: the FunctionCall node itself
    @_('call SEMICOLON')
    def call_stmt(self, value):
        return value[0]

    # LEVEL 4, Stage 4b -- return
    @_('RETURN expr SEMICOLON')
    def return_stmt(self, value):
        return Return(value[1], lineno=value.lineno)

    @_('RETURN SEMICOLON')
    def return_stmt(self, value):
        return Return(None, lineno=value.lineno)

    # ------------------------------------------------------------------
    # Calls -- Stage 4a: `f()`; Stage 4b: arguments
    # ------------------------------------------------------------------
    @_('ID LPAREN args_opt RPAREN')
    def call(self, value):
        return FunctionCall(value[0], value[2], lineno=value.lineno)

    @_('arg_list')
    def args_opt(self, value):
        return value[0]

    @_('empty')
    def args_opt(self, value):
        return []

    @_('arg_list COMMA expr')
    def arg_list(self, value):
        return value[0] + [value[2]]

    @_('expr')
    def arg_list(self, value):
        return [value[0]]

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------
    @_('call')
    def expr(self, value):
        return value[0]

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
