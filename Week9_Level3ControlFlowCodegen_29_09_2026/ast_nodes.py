"""
TinyCStr AST node definitions -- fully implemented.

A note on Const: this uses Const as a generic LITERAL holder, not just
for integers -- a double literal (3.14), a char literal ('x'), and a
string literal ("hi") are all represented as Const(value, type),
distinguished only by the type field, not by AST node class.

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
    """
    WEEK 5, Stage 2b -- relational comparison: < > <= >= == !=
    Same shape as BinOp (op, left, right), kept as a SEPARATE class
    (rather than folding into BinOp) so that later weeks' type-checking
    and codegen can check on "is this a comparison" vs "is this
    arithmetic" by AST node type alone, without inspecting `op` itself.
    """

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
    WEEK 5, Stage 2c -- explicit type cast: (double)expr or (int)expr.
    `target_type` is a SymbolTable.DataType value

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
    """WEEK 5, Stage 2c -- cond ? then_expr : else_expr"""

    def __init__(self, cond, then_expr, else_expr, lineno=None):
        self.cond = cond
        self.then_expr = then_expr
        self.else_expr = else_expr
        self.lineno = lineno

    def label(self):
        return "Ternary"

    def children(self):
        return [self.cond, self.then_expr, self.else_expr]


# ----------------------------------------------------------------------
# LEVEL 3 (Week 8) -- statement nodes for control flow
#
# These are the first AST nodes whose children are STATEMENTS, not just
# expressions: an If's branch, a While's body, and a Block's contents
# are each themselves an Assign / Print / If / While / Block. That is
# what makes the statement grammar recursive this week (a while inside
# an if inside a while ...), exactly as `expr` became recursive in
# Week 3's Stage 1b.
# ----------------------------------------------------------------------
class If(ASTNode):
    """
    WEEK 8, Stage 3a -- if ( cond ) then_stmt
    WEEK 8, Stage 3b -- if ( cond ) then_stmt else else_stmt

    ONE class covers both forms; else_stmt is None when there is no
    else. The printed label differs ("If" vs "IfElse") purely so you can
    SEE in the -ast output which `if` an `else` was attached to -- the
    whole point of the dangling-else exercise (docs/sly_help3.md #4).
    """

    def __init__(self, cond, then_stmt, else_stmt=None, lineno=None):
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt
        self.lineno = lineno

    def label(self):
        return "If" if self.else_stmt is None else "IfElse"

    def children(self):
        if self.else_stmt is None:
            return [self.cond, self.then_stmt]
        return [self.cond, self.then_stmt, self.else_stmt]


class While(ASTNode):
    """WEEK 8, Stage 3b -- while ( cond ) body"""

    def __init__(self, cond, body, lineno=None):
        self.cond = cond
        self.body = body
        self.lineno = lineno

    def label(self):
        return "While"

    def children(self):
        return [self.cond, self.body]


class Block(ASTNode):
    """
    WEEK 8, Stage 3a -- { stmt stmt ... }

    A compound statement: a list of statements that counts as ONE
    statement wherever the grammar expects a `stmt` (e.g. as an if's
    branch). Level 3 blocks hold statements only, no declarations --
    block-level scope is Level 4's (Week 10) concern, not this week's.
    """

    def __init__(self, stmts, lineno=None):
        self.stmts = stmts
        self.lineno = lineno

    def label(self):
        return "Block"

    def children(self):
        return list(self.stmts)


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
    with open(filename, 'w') as file:  # WEEK 8: `with` so the file is always closed
        file.write("\n".join(lines) + "\n")
