"""
TinyCStr -- AST to Three-Address Code (triple form) generator.

REFERENCE IMPLEMENTATION, fully complete through Level 3.

Level 3 (Week 9): If / While / Block statements become LABELS and JUMPS
(LabelTriple, GotoTriple, IfFalseTriple). Label order convention, which
the golden files depend on: a statement allocates ALL of its labels
first, before generating any of its children -- see
docs/control_flow_3ac_reference.md.
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
        """Fresh-label allocator: L0, L1, L2, ... -- never the same label twice."""
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

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
            for s in stmt.stmts:
                self.gen_stmt(s)
        elif isinstance(stmt, If):
            self.gen_if(stmt)
        elif isinstance(stmt, While):
            self.gen_while(stmt)
        else:
            raise ValueError(f"unexpected statement type: {type(stmt)}")

    def gen_if(self, stmt):
        if stmt.else_stmt is None:
            #     if_false cond goto Lend
            #     <then>
            # Lend:
            l_end = self.new_label()
            cond = self.gen_expr(stmt.cond)
            self.program.append(IfFalseTriple(cond, stmt.cond.result_type, l_end))
            self.gen_stmt(stmt.then_stmt)
            self.program.append(LabelTriple(l_end))
        else:
            #     if_false cond goto Lelse
            #     <then>
            #     goto Lend
            # Lelse:
            #     <else>
            # Lend:
            l_else = self.new_label()
            l_end = self.new_label()
            cond = self.gen_expr(stmt.cond)
            self.program.append(IfFalseTriple(cond, stmt.cond.result_type, l_else))
            self.gen_stmt(stmt.then_stmt)
            self.program.append(GotoTriple(l_end))
            self.program.append(LabelTriple(l_else))
            self.gen_stmt(stmt.else_stmt)
            self.program.append(LabelTriple(l_end))

    def gen_while(self, stmt):
        # Ltop:
        #     if_false cond goto Lend
        #     <body>
        #     goto Ltop
        # Lend:
        l_top = self.new_label()
        l_end = self.new_label()
        self.program.append(LabelTriple(l_top))
        cond = self.gen_expr(stmt.cond)
        self.program.append(IfFalseTriple(cond, stmt.cond.result_type, l_end))
        self.gen_stmt(stmt.body)
        self.program.append(GotoTriple(l_top))
        self.program.append(LabelTriple(l_end))

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
