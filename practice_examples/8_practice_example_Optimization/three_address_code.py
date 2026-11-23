"""
Three-address code -- TRIPLE representation (as in practice 4/5), plus
the three triples that make control flow possible:

    LabelTriple(label)            (6) L0:                 a jump target
    GotoTriple(label)             (9) goto L0             always jump
    IfFalseTriple(cond, label)    (4) if_false (3) goto L1
                                  jump if cond is 0 (false), else fall through

and RelOpTriple for comparisons (value 1 = true, 0 = false).
"""


class TripleRef:
    """A reference to an earlier triple's result, by its index."""

    def __init__(self, index):
        self.index = index

    def render(self):
        return f"({self.index})"

    def __eq__(self, other):
        return isinstance(other, TripleRef) and self.index == other.index

    def __hash__(self):
        return hash(self.index)


def render_operand(operand):
    return operand.render() if isinstance(operand, TripleRef) else str(operand)


class BinOpTriple:
    def __init__(self, op, arg1, arg2):
        self.op, self.arg1, self.arg2 = op, arg1, arg2
        self.index = None

    def render(self):
        return f"({self.index}) {self.op} {render_operand(self.arg1)}, {render_operand(self.arg2)}"


class RelOpTriple:
    def __init__(self, op, arg1, arg2):
        self.op, self.arg1, self.arg2 = op, arg1, arg2
        self.index = None

    def render(self):
        return f"({self.index}) {self.op} {render_operand(self.arg1)}, {render_operand(self.arg2)}"


class AssignTriple:
    def __init__(self, dest, arg1):
        self.dest, self.arg1 = dest, arg1
        self.index = None

    def render(self):
        return f"({self.index}) {self.dest} = {render_operand(self.arg1)}"


class PrintTriple:
    def __init__(self, arg1):
        self.arg1 = arg1
        self.index = None

    def render(self):
        return f"({self.index}) PRINT {render_operand(self.arg1)}"


class LabelTriple:
    def __init__(self, label):
        self.label = label
        self.index = None

    def render(self):
        return f"({self.index}) {self.label}:"


class GotoTriple:
    def __init__(self, label):
        self.label = label
        self.index = None

    def render(self):
        return f"({self.index}) goto {self.label}"


class IfFalseTriple:
    def __init__(self, cond, label):
        self.cond, self.label = cond, label
        self.index = None

    def render(self):
        return f"({self.index}) if_false {render_operand(self.cond)} goto {self.label}"


class TripleProgram:
    """A flat, ordered list of triples; append() numbers them."""

    def __init__(self):
        self.triples = []

    def append(self, triple):
        triple.index = len(self.triples)
        self.triples.append(triple)
        return TripleRef(triple.index)

    def render(self):
        return "\n".join(t.render() for t in self.triples)
