"""
TinyCStr -- AST to Three-Address Code (triple form) generator.

Read docs/calls_3ac_reference.md before editing this file.

Levels 1-3 are complete (Week 9's exercise). Your work this week: two
TODOs, gen_call() and gen_return() -- a call becomes PARAM ... PARAM,
CALL; `return` becomes RETURN.
Level 3 (Week 9): If / While / Block statements become LABELS and JUMPS.
Label order convention: a statement allocates ALL of its labels first,
before generating any of its children.
"""
from SymbolTable import DataType
from ast_nodes import (Const, Var, Assign, Print, BinOp, RelOp, Cast, Ternary,
                       If, While, Block, FunctionCall, Return)
from three_address_code import (
    TripleTAC, BinOpTriple, AssignTriple, PrintTriple,
    RelOpTriple, CastTriple, SelectTriple,
    LabelTriple, GotoTriple, IfFalseTriple,
    ParamTriple, CallTriple, ReturnTriple,
)


class TACGenerator:
    def __init__(self, first_label=0):
        self.program = TripleTAC()
        self.label_counter = first_label   # WEEK 11: continues across functions
        self.function = None

    def generate(self, function):
        self.function = function           # WEEK 11: gen_return needs the return type
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
        # ------------------------------------------------------------------
        # LEVEL 4 (Week 11)
        # ------------------------------------------------------------------
        elif isinstance(stmt, FunctionCall):
            self.gen_call(stmt, value_used=False)
        elif isinstance(stmt, Return):
            self.gen_return(stmt)
        else:
            raise ValueError(f"unexpected statement type: {type(stmt)}")

    def gen_call(self, node, value_used=True):
        """
        TODO(week-11): a FunctionCall node -> PARAM ... PARAM, CALL.
        Called from gen_expr() (value_used=True: `x = f(a);`) and from
        gen_stmt() (value_used=False: `f(a);`). Return the TripleRef that
        appending the CallTriple gives you -- it is the call's value.

          1. Evaluate ALL arguments first, in order:
                 operands = [self.gen_expr(arg) for arg in node.args]
             A call nested in an argument -- f(g(1), 2) -- thereby emits its
             own PARAMs and CALL completely BEFORE f's first PARAM, so the
             PARAMs of every call end up consecutive, right before its CALL.
             (Emitting each PARAM as soon as its argument is evaluated would
             interleave g's PARAM/CALL between f's PARAMs. Why is that wrong?
             See docs/calls_3ac_reference.md.)
          2. One ParamTriple(operand, arg.result_type) per argument, in order.
             arg.result_type is already the PARAMETER's type: the type checker
             inserted a Cast wherever the argument needed converting.
          3. CallTriple(node.name, len(node.args), node.return_type, value_used)
             -- node.return_type is the callee's declared return type
             (stamped by the type checker, even on a statement call).
        """
        raise NotImplementedError("implement TACGenerator.gen_call()")

    def gen_return(self, stmt):
        """
        TODO(week-11): one ReturnTriple(operand, self.function.getReturnType()),
        where operand is self.gen_expr(stmt.expr) -- or None for `return;`.
        """
        raise NotImplementedError("implement TACGenerator.gen_return()")

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
        elif isinstance(node, FunctionCall):     # WEEK 11
            return self.gen_call(node)
        else:
            raise ValueError(f"unexpected expr node type: {type(node)}")


def generate_for_function(function):
    """Convenience wrapper: generate() a fresh TACGenerator for one function."""
    return TACGenerator().generate(function)
