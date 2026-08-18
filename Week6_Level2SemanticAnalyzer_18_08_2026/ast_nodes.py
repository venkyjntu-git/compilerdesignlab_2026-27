"""
TinyCStr AST node definitions -- fully implemented.

WEEK 6 CHANGE: every node now accepts an optional `lineno`
(defaults to None if not given) which will be used to report
undeclared-variable and type-mismatch errors with a line number
in Semantic Analysis

`lineno` is set by the PARSER (tinycstr_parser.py), using SLY's
`value.lineno` -- see docs/lineno_and_type_checking.md for exactly how
that works and why it's reliable even for multi-symbol productions.

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

    def __init__(self, value, type, lineno=None):
        self.value = value
        self.type = type
        self.lineno = lineno

    def label(self):
        return f"Const({self.value},{self.type})"


class Var(ASTNode):
    def __init__(self, name, lineno=None):
        self.name = name
        self.lineno = lineno

    def label(self):
        return f"Var({self.name})"


class Assign(ASTNode):
    def __init__(self, var, expr, lineno=None):
        self.var = var
        self.expr = expr
        self.lineno = lineno

    def label(self):
        return "Assign"

    def children(self):
        return [self.var, self.expr]


class Print(ASTNode):
    def __init__(self, expr, lineno=None):
        self.expr = expr
        self.lineno = lineno

    def label(self):
        return "Print"

    def children(self):
        return [self.expr]


class BinOp(ASTNode):

    def __init__(self, op, left, right, lineno=None):
        self.op = op
        self.left = left
        self.right = right
        self.lineno = lineno

    def label(self):
        return f"BinOp({self.op})"

    def children(self):
        return [self.left, self.right]


class RelOp(ASTNode):

    def __init__(self, op, left, right, lineno=None):
        self.op = op
        self.left = left
        self.right = right
        self.lineno = lineno

    def label(self):
        return f"RelOp({self.op})"

    def children(self):
        return [self.left, self.right]


class Cast(ASTNode):
    """
    WEEK 6: also the node type_checker.py inserts automatically when it
    finds an IMPLICIT promotion/conversion is needed (e.g. an int used
    where a double is expected) -- see type_checker.py's module
    docstring. A Cast built by the parser and one inserted by the type
    checker look identical; there's no separate "implicit cast" class.
    """

    def __init__(self, target_type, expr, lineno=None):
        self.target_type = target_type
        self.expr = expr
        self.lineno = lineno

    def label(self):
        return f"Cast({self.target_type})"

    def children(self):
        return [self.expr]


class Ternary(ASTNode):

    def __init__(self, cond, then_expr, else_expr, lineno=None):
        self.cond = cond
        self.then_expr = then_expr
        self.else_expr = else_expr
        self.lineno = lineno

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
