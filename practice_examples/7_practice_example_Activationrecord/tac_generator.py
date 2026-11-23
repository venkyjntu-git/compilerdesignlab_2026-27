"""
AST to Three-Address Code (triples), one TripleProgram per FUNCTION.

The new part is the call. For f(e1, e2):
  1. generate the code for ALL arguments first (an argument may itself
     contain a call, which must be finished before f's PARAMs start),
  2. then PARAM e1, PARAM e2 -- consecutively, right before
  3. CALL f, 2 -- a TripleRef to this triple is the call's value.
"""
from ast_nodes import Num, Var, BinOp, Call, Assign, Print, Return
from three_address_code import (TripleProgram, BinOpTriple, AssignTriple, PrintTriple,
                                ParamTriple, CallTriple, ReturnTriple)


class TACGenerator:
    def __init__(self):
        self.program = TripleProgram()

    def gen_function(self, function):
        for stmt in function.body:
            self.gen_stmt(stmt)
        return self.program

    def gen_stmt(self, stmt):
        if isinstance(stmt, Assign):
            self.program.append(AssignTriple(stmt.var.name, self.gen_expr(stmt.expr)))
        elif isinstance(stmt, Print):
            self.program.append(PrintTriple(self.gen_expr(stmt.expr)))
        elif isinstance(stmt, Return):
            self.program.append(ReturnTriple(self.gen_expr(stmt.expr)))

    def gen_expr(self, node):
        if isinstance(node, Num):
            return str(node.value)
        if isinstance(node, Var):
            return node.name
        if isinstance(node, BinOp):
            left, right = self.gen_expr(node.left), self.gen_expr(node.right)
            return self.program.append(BinOpTriple(node.op, left, right))
        if isinstance(node, Call):
            operands = [self.gen_expr(arg) for arg in node.args]     # 1. all arguments
            for operand in operands:                                 # 2. the PARAMs
                self.program.append(ParamTriple(operand))
            return self.program.append(CallTriple(node.name, len(operands)))   # 3. CALL


def generate_for_program(program):
    """Returns a list of (Function, TripleProgram), one per function."""
    return [(f, TACGenerator().gen_function(f)) for f in program.functions]
