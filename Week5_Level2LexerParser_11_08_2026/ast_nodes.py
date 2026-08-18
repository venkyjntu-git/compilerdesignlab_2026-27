"""
TinyCStr AST node definitions -- fully implemented.

WEEK 5 ADDITIONS : RelOp, Cast, Ternary, Const. 
Removed : Num
Var/Assign/Print/BinOp are unchanged from before.

A note on Const: this week uses Const as a generic LITERAL holder, not just
for integers -- a double literal (3.14), a char literal ('x'), and a
string literal ("hi") are all represented as Const(value, type), distinguished
only by the type field not by AST node class. 

Every node implements two small methods instead of hand-writing a
pretty-printer and a DOT exporter per class:
    label()    -- one-line display text for this node
    children() -- list of child AST nodes (empty for leaves)
`pretty()` and `to_dot()` below are generic tree-walkers built once on
top of those two methods, so every node's printed/exported form stays
consistent by construction
"""
from SymbolTable import DataType

class ASTNode:
    """Base class for all TinyCStr AST nodes."""

    def label(self):
        return type(self).__name__

    def children(self):
        return []


class Const(ASTNode):
    """
    A literal value -- int, double, char, or string.
    type -- INT, DOUBLE, CHAR, STRING
    """

    def __init__(self, value, type):
        self.value = value
        self.type = type 

    def label(self):
        return f"Const({self.value},{self.type})"


class Var(ASTNode):
    def __init__(self, name):
        self.name = name

    def label(self):
        return f"Var({self.name})"


class Assign(ASTNode):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

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


class BinOp(ASTNode):

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def label(self):
        return f"BinOp({self.op})"

    def children(self):
        return [self.left, self.right]


class RelOp(ASTNode):
    """
    WEEK 5, Stage 2b -- relational comparison: < > <= >= == !=
    Same shape as BinOp (op, left, right), kept as a SEPARATE class
    (rather than folding into BinOp) so that later weeks' type-checking
    and codegen can check on "is this a comparison" vs "is this
    arithmetic" by AST node type alone, without inspecting `op` itself.
    """

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def label(self):
        return f"RelOp({self.op})"

    def children(self):
        return [self.left, self.right]


class Cast(ASTNode):
    """
    WEEK 5, Stage 2c -- explicit type cast: (double)expr or (int)expr.
    `target_type` is a SymbolTable.DataType value 
    """

    def __init__(self, target_type, expr):
        self.target_type = target_type
        self.expr = expr

    def label(self):
        return f"Cast({self.target_type})"

    def children(self):
        return [self.expr]


class Ternary(ASTNode):
    """WEEK 5, Stage 2c -- cond ? then_expr : else_expr"""

    def __init__(self, cond, then_expr, else_expr):
        self.cond = cond
        self.then_expr = then_expr
        self.else_expr = else_expr

    def label(self):
        return "Ternary"

    def children(self):
        return [self.cond, self.then_expr, self.else_expr]


def pretty(node, indent=0):
    """
    Indented, human-readable text form of an AST subtree.
    two spaces per indentation level, one node per line, `label()` text only
    (no extra punctuation).
    """
    lines = [("  " * indent) + node.label()]
    for child in node.children():
        lines.append(pretty(child, indent + 1))
    return "\n".join(lines)


def to_dot(node, graph_name="AST", filename="ast.dot"):
    '''
    Renders an AST subtree as Graphviz DOT source.
    run `dot -Tpng ast.dot -o ast.png` (or any Graphviz frontend) to view it.
    '''
    lines = [f"digraph {graph_name} {{"]
    counter = 0

    def visit(node, parent_id=None):
        nonlocal counter

        node_id = counter
        counter += 1

        label = node.label().replace('"', '\\"')
        lines.append(f'  n{node_id} [label="{label}"];')

        if parent_id is not None:
            lines.append(f"  n{parent_id} -> n{node_id};")

        for child in node.children():
            visit(child, node_id)

    visit(node)

    lines.append("}")
    lines = "\n".join(lines)
    file = open(filename, 'w')
    file.write(lines)
