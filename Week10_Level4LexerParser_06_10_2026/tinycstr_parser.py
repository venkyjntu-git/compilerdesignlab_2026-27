"""
TinyCStr Level 4 Parser (Stages 4a -> 4b)

Read docs/level4_grammar_reference.md and docs/sly_help4.md before
editing this file.

The Level 1-3 grammar is complete (Week 8's exercise). One PROVIDED
change this week: every declaration now goes through a single `type`
nonterminal -- docs/sly_help4.md #2 shows the 4 conflicts the old
INT/DOUBLE/CHAR/STRING-specific decl rules cause once functions exist.

Your work is in the "LEVEL 4" TODOs, staged:
  Stage 4a -- several functions (including `void` ones) with NO
              parameters, and calls `f()` as a statement or expression.
  Stage 4b -- parameter lists, prototypes, call arguments, `return`.
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
    # Program structure
    # ------------------------------------------------------------------
    # TODO(week-10, stage-4a): a program has ONE OR MORE functions.
    # Replace this rule with
    #     program       : global_decl_list func_def_list
    #     func_def_list : func_def_list func_def
    #                   | func_def
    # and in the action add EVERY function to the Program (prog.addFunction).
    #
    # TODO(week-10, stage-4b): global_decl_list items can now also be
    # prototypes. Add the alternative
    #     global_decl_list : global_decl_list func_proto   -> value[0] + [value[1]]
    # and in the program action, route each item: a FunctionPrototype goes
    # to prog.addPrototype(item), a SymbolTableEntry to the global table.
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

    # ------------------------------------------------------------------
    # Types -- PROVIDED (WEEK 10 change): one `type` nonterminal for all
    # declarations, so `int a;` and `int f(...)` share the prefix `type ID`
    # and are told apart by the NEXT token (docs/sly_help4.md #2).
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
    # Functions
    # ------------------------------------------------------------------
    # This is Week 8's single-function rule, already rewritten with `type`
    # (so that it doesn't conflict with `decl`). It accepts `int main(){...}`.
    #
    # TODO(week-10, stage-4a): split it into a shared HEADER plus a body:
    #     func_head : type ID LPAREN RPAREN   -> (value[0], value[1], [], value.lineno)
    #               | VOID ID LPAREN RPAREN   -> (DataType.VOID, value[1], [], value.lineno)
    #     func_def  : func_head LBRACE decl_stmt_list stmt_list RBRACE
    # In func_def's action, unpack the tuple and build
    #     Function(rtype, name, params, lineno=lineno)
    # (Why a separate func_head? In Stage 4b a prototype is that SAME
    # header followed by `;` instead of a body.)
    #
    # TODO(week-10, stage-4b): parameters. In both func_head rules, replace
    # `LPAREN RPAREN` with `LPAREN params_opt RPAREN` (and use value[3] as
    # the params), then add
    #     params_opt : param_list | empty                 -> list (or [])
    #     param_list : param_list COMMA param | param     -> list of params
    #     param      : type ID   -> (value[0], value[1])
    #                | type      -> (value[0], None)       unnamed: prototypes only
    #     func_proto : func_head SEMICOLON
    #                  -> FunctionPrototype(rtype, name, params, lineno=lineno)
    # Do NOT write separate "prototype parameter" and "definition
    # parameter" rules -- docs/sly_help4.md #3 shows the reduce/reduce
    # conflict that causes. Unnamed parameters in a definition are a
    # SEMANTIC error, reported by the provided type checker.
    @_('type ID LPAREN RPAREN LBRACE decl_stmt_list stmt_list RBRACE')
    def func_def(self, value):
        func = Function(value[0], value[1], lineno=value.lineno)
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

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------
    @_('assign', 'print_stmt', 'if_stmt', 'block', 'while_stmt')
    def stmt(self, value):
        return value[0]

    # TODO(week-10, stage-4a): a call used as a statement, `f();`
    #     stmt      : call_stmt                         -> value[0]
    #     call_stmt : call SEMICOLON                    -> value[0]
    # The FunctionCall node itself goes into the statement list -- no
    # wrapper node (docs/level4_grammar_reference.md).
    #
    # TODO(week-10, stage-4b): return
    #     stmt        : return_stmt                     -> value[0]
    #     return_stmt : RETURN expr SEMICOLON           -> Return(value[1], lineno=value.lineno)
    #                 | RETURN SEMICOLON                -> Return(None, lineno=value.lineno)

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

    # ------------------------------------------------------------------
    # Calls
    # ------------------------------------------------------------------
    # TODO(week-10, stage-4a): the call itself, with no arguments yet:
    #     call : ID LPAREN RPAREN     -> FunctionCall(value[0], [], lineno=value.lineno)
    # and a call is also an expression:
    #     expr : call                 -> value[0]
    #
    # TODO(week-10, stage-4b): arguments. Replace the rule above with
    #     call     : ID LPAREN args_opt RPAREN   -> FunctionCall(value[0], value[2], ...)
    #     args_opt : arg_list | empty
    #     arg_list : arg_list COMMA expr | expr
    # Each argument is a full `expr`, so `square(square(2))` and
    # `add(a*2, b)` work with no extra rules.

    # ------------------------------------------------------------------
    # Expressions -- Levels 1-3, unchanged
    # ------------------------------------------------------------------
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
