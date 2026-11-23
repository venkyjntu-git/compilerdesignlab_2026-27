"""
AST to Three-Address Code (triples) -- now with control flow.

Expressions are translated exactly as in practice 4. The new part is the
STATEMENTS, which become labels and jumps:

  if (c) S              if (c) S1 else S2         while (c) S
  ---------             ------------------        -----------
      <c>                   <c>                   Ltop:
      if_false c Lend       if_false c Lelse          <c>
      <S>                   <S1>                      if_false c Lend
  Lend:                     goto Lend                 <S>
                        Lelse:                        goto Ltop
                            <S2>                  Lend:
                        Lend:

new_label() is the FRESH-LABEL allocator: L0, L1, L2, ... never reused.
"""
from ast_nodes import Num, Var, BinOp, RelOp, Assign, Print, If, While, Block
from three_address_code import (TripleProgram, BinOpTriple, RelOpTriple, AssignTriple,
                                PrintTriple, LabelTriple, GotoTriple, IfFalseTriple)


class TACGenerator:
    def __init__(self):
        self.program = TripleProgram()
        self.label_counter = 0

    def new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def gen_stmt(self, stmt):
        if isinstance(stmt, Assign):
            self.program.append(AssignTriple(stmt.var.name, self.gen_expr(stmt.expr)))
        elif isinstance(stmt, Print):
            self.program.append(PrintTriple(self.gen_expr(stmt.expr)))
        elif isinstance(stmt, Block):
            for s in stmt.stmts:
                self.gen_stmt(s)
        elif isinstance(stmt, If) and stmt.else_stmt is None:
            l_end = self.new_label()
            cond = self.gen_expr(stmt.cond)
            self.program.append(IfFalseTriple(cond, l_end))
            self.gen_stmt(stmt.then_stmt)
            self.program.append(LabelTriple(l_end))
        elif isinstance(stmt, If):
            l_else, l_end = self.new_label(), self.new_label()
            cond = self.gen_expr(stmt.cond)
            self.program.append(IfFalseTriple(cond, l_else))
            self.gen_stmt(stmt.then_stmt)
            self.program.append(GotoTriple(l_end))
            self.program.append(LabelTriple(l_else))
            self.gen_stmt(stmt.else_stmt)
            self.program.append(LabelTriple(l_end))
        elif isinstance(stmt, While):
            l_top, l_end = self.new_label(), self.new_label()
            self.program.append(LabelTriple(l_top))
            cond = self.gen_expr(stmt.cond)
            self.program.append(IfFalseTriple(cond, l_end))
            self.gen_stmt(stmt.body)
            self.program.append(GotoTriple(l_top))
            self.program.append(LabelTriple(l_end))
        return self.program

    def gen_expr(self, node):
        if isinstance(node, Num):
            return str(node.value)
        if isinstance(node, Var):
            return node.name
        if isinstance(node, BinOp):
            left, right = self.gen_expr(node.left), self.gen_expr(node.right)
            return self.program.append(BinOpTriple(node.op, left, right))
        if isinstance(node, RelOp):
            left, right = self.gen_expr(node.left), self.gen_expr(node.right)
            return self.program.append(RelOpTriple(node.op, left, right))


def generate_for_program(program_block):
    return TACGenerator().gen_stmt(program_block)
