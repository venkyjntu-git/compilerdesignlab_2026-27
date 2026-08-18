"""
TinyCStr Level 1 -- AST to Three-Address Code (triple form) generator.

This walks a Function's statement AST and builds a TripleTAC (see
three_address_code.py). With triples, an intermediate result's "name" is
just whatever index TripleTAC.append() gives it, so there's nothing to
allocate.

This file is provided for Week 5 -- you do not need to modify it -- 
your work this week is entirely in tinycstr_lexer.py/tinycstr_parser.py.
"""
from ast_nodes import Const, Var, Assign, Print, BinOp
from three_address_code import TripleTAC, BinOpTriple, AssignTriple, PrintTriple


class TACGenerator:
    def __init__(self):
        self.program = TripleTAC()

    def generate(self, function):
        """
        Provided -- the entry point. Walks function.getStatementsAstList()
        in order and returns the finished TripleTAC. You should not
        need to change this method; implement gen_stmt() and gen_expr()
        below instead.
        """
        for stmt in function.getStatementsAstList():
            self.gen_stmt(stmt)
        return self.program

    def gen_stmt(self, stmt):
        if isinstance(stmt, Assign):
            operand = self.gen_expr(stmt.expr)
            self.program.append(AssignTriple(stmt.var.name, operand))
        if isinstance(stmt, Print):
            operand = self.gen_expr(stmt.expr)
            self.program.append(PrintTriple(operand))
        
    def gen_expr(self, node):
        if isinstance(node, Const):
            return str(node.value)
        elif isinstance(node, Var):
            return node.name
        elif isinstance(node, BinOp):
            left  = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            return self.program.append(BinOpTriple(node.op, left, right))
            
