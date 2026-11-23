"""
TinyCStr -- AST to Three-Address Code (triple form) generator.

REFERENCE IMPLEMENTATION, fully complete through Level 2 (this was
Week 7's exercise, now carried forward as infrastructure).

WEEK 8 NOTE: Level 3 statements (If / While / Block) are NOT handled
here yet -- control-flow 3AC (labels, conditional jumps) is Week 9's
subject. main.py checks for Level 3 constructs BEFORE calling this
generator and reports "planned for Week 9" instead, so gen_stmt()'s
final `raise` is only reachable if that gate is bypassed.
"""
from SymbolTable import DataType
from ast_nodes import Const, Var, Assign, Print, BinOp, RelOp, Cast, Ternary
from three_address_code import (
    TripleTAC, BinOpTriple, AssignTriple, PrintTriple,
    RelOpTriple, CastTriple, SelectTriple,
)


class TACGenerator:
    def __init__(self):
        self.program = TripleTAC()

    def generate(self, function):
        """Walks function.getStatementsAstList() in order and returns the finished TripleTAC."""
        for stmt in function.getStatementsAstList():
            self.gen_stmt(stmt)
        return self.program

    # ------------------------------------------------------------------
    # LEVEL 1
    # ------------------------------------------------------------------
    def gen_stmt(self, stmt):
        if isinstance(stmt, Assign):
            operand = self.gen_expr(stmt.expr)
            self.program.append(AssignTriple(stmt.var.name, operand))
        elif isinstance(stmt, Print):
            operand = self.gen_expr(stmt.expr)
            self.program.append(PrintTriple(operand))
        else:
            raise ValueError(f"unexpected statement type: {type(stmt)} "
                             f"(control-flow 3AC is Week 9)")

    def gen_expr(self, node):
        """
        NOTE on Const: string/char literal VALUES are wrapped in their
        ORIGINAL quote characters so tac_to_mips.py's literal_kind() can
        tell them apart from a variable name (see docs of Week 7).
        """
        if isinstance(node, Const):
            if node.type == DataType.STRING:
                return f'"{node.value}"'
            elif node.type == DataType.CHAR:
                return f"'{node.value}'"
            else:
                return str(node.value)
        elif isinstance(node, Var):
            return node.name
        elif isinstance(node, BinOp):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            return self.program.append(BinOpTriple(node.op, left, right, node.result_type))
        # ------------------------------------------------------------------
        # LEVEL 2 (Week 7)
        # ------------------------------------------------------------------
        elif isinstance(node, RelOp):
            return self.gen_relop(node)
        elif isinstance(node, Cast):
            return self.gen_cast(node)
        elif isinstance(node, Ternary):
            return self.gen_ternary(node)
        else:
            raise ValueError(f"unexpected expr node type: {type(node)}")

    def gen_relop(self, node):
        # operand type, not node.result_type (which is always INT for a comparison)
        left = self.gen_expr(node.left)
        right = self.gen_expr(node.right)
        return self.program.append(RelOpTriple(node.op, left, right, node.left.result_type))

    def gen_cast(self, node):
        arg = self.gen_expr(node.expr)
        return self.program.append(CastTriple(node.expr.result_type, node.target_type, arg))

    def gen_ternary(self, node):
        # ONE flat SelectTriple -- branching happens only in tac_to_mips.py
        cond = self.gen_expr(node.cond)
        then_val = self.gen_expr(node.then_expr)
        else_val = self.gen_expr(node.else_expr)
        return self.program.append(
            SelectTriple(cond, node.cond.result_type, then_val, else_val, node.result_type))


def generate_for_function(function):
    """Convenience wrapper: generate() a fresh TACGenerator for one function."""
    return TACGenerator().generate(function)
