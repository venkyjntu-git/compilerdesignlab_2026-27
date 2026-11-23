"""
AST node definitions -- expressions (as in the earlier practice examples)
plus the STATEMENTS needed for control flow: Print, If, While, Block.

Every node implements label() and children(); pretty() prints any tree.
"""


class ASTNode:
    def label(self):
        return type(self).__name__

    def children(self):
        return []


class Num(ASTNode):
    def __init__(self, value):
        self.value = value

    def label(self):
        return f"Num({self.value})"


class Var(ASTNode):
    def __init__(self, name):
        self.name = name

    def label(self):
        return f"Var({self.name})"


class BinOp(ASTNode):
    def __init__(self, op, left, right):
        self.op, self.left, self.right = op, left, right

    def label(self):
        return f"BinOp({self.op})"

    def children(self):
        return [self.left, self.right]


class RelOp(ASTNode):
    """a comparison, e.g. i <= n -- the condition of an if / while"""

    def __init__(self, op, left, right):
        self.op, self.left, self.right = op, left, right

    def label(self):
        return f"RelOp({self.op})"

    def children(self):
        return [self.left, self.right]


class Assign(ASTNode):
    def __init__(self, var, expr):
        self.var, self.expr = var, expr

    def label(self):
        return "Assign"

    def children(self):
        return [self.var, self.expr]


class Print(ASTNode):
    def __init__(self, expr):
        self.expr = expr

    def label(self):
        return "Print"

    def children(self):
        return [self.expr]


class If(ASTNode):
    """if (cond) then_stmt [else else_stmt] -- else_stmt is None without else"""

    def __init__(self, cond, then_stmt, else_stmt=None):
        self.cond, self.then_stmt, self.else_stmt = cond, then_stmt, else_stmt

    def label(self):
        return "If" if self.else_stmt is None else "IfElse"

    def children(self):
        kids = [self.cond, self.then_stmt]
        return kids if self.else_stmt is None else kids + [self.else_stmt]


class While(ASTNode):
    def __init__(self, cond, body):
        self.cond, self.body = cond, body

    def label(self):
        return "While"

    def children(self):
        return [self.cond, self.body]


class Block(ASTNode):
    """{ stmt stmt ... } -- also used for the whole program"""

    def __init__(self, stmts):
        self.stmts = stmts

    def label(self):
        return "Block"

    def children(self):
        return list(self.stmts)


def pretty(node, indent=0):
    lines = [("  " * indent) + node.label()]
    for child in node.children():
        lines.append(pretty(child, indent + 1))
    return "\n".join(lines)
