"""
AST node definitions 

IMPORTANT:  
- Abstarct Syntax Tree for expressions
- Every node implements two small methods instead of hand-writing a
pretty-printer and a DOT exporter per class:
    label()    -- one-line display text for this node
    children() -- list of child AST nodes (empty for leaves)
`pretty()` and `to_dot()` are generic tree-walkers built once on
top of those two methods, so every node's printed/exported form stays
consistent by construction.
"""

class ASTNode:
    """Base class for all AST nodes."""

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


class Assign(ASTNode):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

    def label(self):
        return "Assign"

    def children(self):
        return [self.var, self.expr]



class BinOp(ASTNode):

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def label(self):
        return f"BinOp({self.op})"

    def children(self):
        return [self.left, self.right]


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


def to_dot(node, graph_name="AST",filename="ast.dot"):
    '''
    Renders an AST subtree as Graphviz DOT source. 
    Feed the output to dot -Tpng ast.dot -o ast.png (or any Graphviz frontend) to view it. 
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
    lines ="\n".join(lines)
    file = open(filename, 'w')
    file.write(lines)