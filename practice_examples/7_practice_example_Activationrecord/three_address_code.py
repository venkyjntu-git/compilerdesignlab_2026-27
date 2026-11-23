"""
Three-address code -- TRIPLE representation (as in practice 4/5), plus
three triples for function calls:

    ParamTriple(arg)          (3) PARAM a          one argument of the NEXT call
    CallTriple(name, nargs)   (4) CALL square, 1   call; its value is the result
    ReturnTriple(arg)         (7) RETURN (6)       give a value back, leave the function

A call  f(e1, e2)  becomes:   <code for e1>  <code for e2>
                              PARAM e1       PARAM e2       CALL f, 2
"""


class TripleRef:
    def __init__(self, index):
        self.index = index

    def render(self):
        return f"({self.index})"

    def __eq__(self, other):
        return isinstance(other, TripleRef) and self.index == other.index


def render_operand(operand):
    return operand.render() if isinstance(operand, TripleRef) else str(operand)


def is_literal(operand):
    return isinstance(operand, str) and operand.isdigit()


class BinOpTriple:
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


class ParamTriple:
    def __init__(self, arg):
        self.arg = arg
        self.index = None

    def render(self):
        return f"({self.index}) PARAM {render_operand(self.arg)}"


class CallTriple:
    def __init__(self, name, nargs):
        self.name, self.nargs = name, nargs
        self.index = None

    def render(self):
        return f"({self.index}) CALL {self.name}, {self.nargs}"


class ReturnTriple:
    def __init__(self, arg):
        self.arg = arg
        self.index = None

    def render(self):
        return f"({self.index}) RETURN {render_operand(self.arg)}"


class TripleProgram:
    def __init__(self):
        self.triples = []

    def append(self, triple):
        triple.index = len(self.triples)
        self.triples.append(triple)
        return TripleRef(triple.index)

    def render(self):
        return "\n".join(t.render() for t in self.triples)
