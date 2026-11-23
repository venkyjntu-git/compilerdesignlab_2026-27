"""
AST node definitions -- expressions (as in the earlier practice examples)
plus FUNCTIONS: Call, Return, Function, Program.
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


class Call(ASTNode):
    """name(arg, arg, ...) -- an expression whose value is the function's result"""

    def __init__(self, name, args):
        self.name, self.args = name, args

    def label(self):
        return f"Call({self.name})"

    def children(self):
        return list(self.args)


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


class Return(ASTNode):
    def __init__(self, expr):
        self.expr = expr

    def label(self):
        return "Return"

    def children(self):
        return [self.expr]


class Function(ASTNode):
    """int name(int p1, int p2, ...) { body }"""

    def __init__(self, name, params, body):
        self.name, self.params, self.body = name, params, body

    def label(self):
        return f"Function {self.name}({', '.join(self.params)})"

    def children(self):
        return list(self.body)

    def locals(self):
        """Every variable ASSIGNED in the body that is not a parameter, in order."""
        names = []
        for stmt in self.body:
            if isinstance(stmt, Assign) and stmt.var.name not in self.params \
                    and stmt.var.name not in names:
                names.append(stmt.var.name)
        return names


class Program(ASTNode):
    def __init__(self, functions):
        self.functions = functions

    def children(self):
        return list(self.functions)


def pretty(node, indent=0):
    lines = [("  " * indent) + node.label()]
    for child in node.children():
        lines.append(pretty(child, indent + 1))
    return "\n".join(lines)
