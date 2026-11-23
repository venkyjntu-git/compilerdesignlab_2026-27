"""
TinyCStr -- AST to Three-Address Code (triple form) generator.

Read docs/control_flow_3ac_reference.md before editing this file, and
draw the CFG for tests/test12.tc by hand FIRST (README, step 2).

Level 1 + Level 2 (expressions, Assign, Print) are complete -- do not
modify. Your work this week is the "LEVEL 3" section: a fresh-label
allocator, and turning Block / If / While into labels and jumps
(LabelTriple, GotoTriple, IfFalseTriple from three_address_code.py).

Label-order convention, which the golden files depend on: a statement
allocates ALL of its labels first, before generating any of its
children (its condition, branches or body).
"""
from SymbolTable import DataType
from ast_nodes import (Const, Var, Assign, Print, BinOp, RelOp, Cast, Ternary,
                       If, While, Block)
from three_address_code import (
    TripleTAC, BinOpTriple, AssignTriple, PrintTriple,
    RelOpTriple, CastTriple, SelectTriple,
    LabelTriple, GotoTriple, IfFalseTriple,
)


class TACGenerator:
    def __init__(self):
        self.program = TripleTAC()
        self.label_counter = 0

    def generate(self, function):
        for stmt in function.getStatementsAstList():
            self.gen_stmt(stmt)
        return self.program

    def new_label(self):
        """
        TODO(week-9): the fresh-label allocator. Return "L0" on the first
        call, "L1" on the second, and so on -- never the same label twice
        within one function. self.label_counter (set up in __init__) is
        there for you to use.
        """
        raise NotImplementedError("implement TACGenerator.new_label()")

    def gen_stmt(self, stmt):
        if isinstance(stmt, Assign):
            operand = self.gen_expr(stmt.expr)
            self.program.append(AssignTriple(stmt.var.name, operand))
        elif isinstance(stmt, Print):
            operand = self.gen_expr(stmt.expr)
            self.program.append(PrintTriple(operand))
        # ------------------------------------------------------------------
        # LEVEL 3 (Week 9)
        # ------------------------------------------------------------------
        elif isinstance(stmt, Block):
            self.gen_block(stmt)
        elif isinstance(stmt, If):
            self.gen_if(stmt)
        elif isinstance(stmt, While):
            self.gen_while(stmt)
        else:
            raise ValueError(f"unexpected statement type: {type(stmt)}")

    def gen_block(self, stmt):
        """
        TODO(week-9): a Block produces no triples of its own -- just
        gen_stmt() each statement in stmt.stmts, in order. (Do this one
        first: it is one line, and test10/test12 need it.)
        """
        raise NotImplementedError("implement TACGenerator.gen_block()")

    def gen_if(self, stmt):
        """
        TODO(week-9): two shapes, depending on stmt.else_stmt.

        No else (stmt.else_stmt is None) -- ONE label:
                if_false <cond> goto Lend
                <then_stmt>
            Lend:

        With else -- TWO labels, allocated in this order: Lelse, then Lend:
                if_false <cond> goto Lelse
                <then_stmt>
                goto Lend
            Lelse:
                <else_stmt>
            Lend:

        Building blocks:
            cond = self.gen_expr(stmt.cond)       # operand holding the condition
            self.program.append(IfFalseTriple(cond, stmt.cond.result_type, label))
            self.program.append(GotoTriple(label))
            self.program.append(LabelTriple(label))
            self.gen_stmt(stmt.then_stmt)         # recursion handles ANY nesting
        stmt.cond.result_type was stamped by the type checker -- it is
        DOUBLE for `if (d)` with a double d, which MIPS must test differently.

        Allocate the labels with self.new_label() BEFORE generating the
        condition or either branch (the label-order convention above).
        """
        raise NotImplementedError("implement TACGenerator.gen_if()")

    def gen_while(self, stmt):
        """
        TODO(week-9): TWO labels, allocated in this order: Ltop, then Lend.

            Ltop:
                if_false <cond> goto Lend
                <body>
                goto Ltop
            Lend:

        Note Ltop goes BEFORE the condition: the condition is re-evaluated
        on every iteration, so the back edge (goto Ltop) must jump to the
        code that computes it, not past it. Compare with your hand-drawn
        CFG for tests/test12.tc.
        """
        raise NotImplementedError("implement TACGenerator.gen_while()")

    # ------------------------------------------------------------------
    # Expressions -- Level 1 + Level 2, unchanged since Week 7
    # ------------------------------------------------------------------
    def gen_expr(self, node):
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
        elif isinstance(node, RelOp):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            return self.program.append(RelOpTriple(node.op, left, right, node.left.result_type))
        elif isinstance(node, Cast):
            arg = self.gen_expr(node.expr)
            return self.program.append(CastTriple(node.expr.result_type, node.target_type, arg))
        elif isinstance(node, Ternary):
            cond = self.gen_expr(node.cond)
            then_val = self.gen_expr(node.then_expr)
            else_val = self.gen_expr(node.else_expr)
            return self.program.append(
                SelectTriple(cond, node.cond.result_type, then_val, else_val, node.result_type))
        else:
            raise ValueError(f"unexpected expr node type: {type(node)}")


def generate_for_function(function):
    """Convenience wrapper: generate() a fresh TACGenerator for one function."""
    return TACGenerator().generate(function)
