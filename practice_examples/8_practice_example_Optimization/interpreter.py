"""
A tiny interpreter for triples -- to CHECK an optimization.

An optimization is only correct if the program still prints exactly the
same thing. run() executes a list of triples with given input values and
returns what it printed, so before/after can be compared.
"""
from three_address_code import (BinOpTriple, RelOpTriple, AssignTriple, PrintTriple,
                                LabelTriple, GotoTriple, IfFalseTriple, TripleRef)


def run(triples, inputs):
    env = dict(inputs)              # variable -> value
    result = {}                     # triple index -> value it computed
    labels = {t.label: i for i, t in enumerate(triples) if isinstance(t, LabelTriple)}
    printed = []

    def val(op):
        if isinstance(op, TripleRef):
            return result[op.index]
        if op.lstrip('-').isdigit():
            return int(op)
        return env[op]

    pc = 0
    while pc < len(triples):
        t = triples[pc]
        pc += 1
        if isinstance(t, (BinOpTriple, RelOpTriple)):
            a, b = val(t.arg1), val(t.arg2)
            if t.op == '/':
                q = abs(a) // abs(b)
                result[t.index] = q if (a < 0) == (b < 0) else -q
            else:
                result[t.index] = int({'+': a + b, '-': a - b, '*': a * b, '<': a < b,
                                       '>': a > b, '<=': a <= b, '>=': a >= b,
                                       '==': a == b, '!=': a != b}[t.op])
        elif isinstance(t, AssignTriple):
            env[t.dest] = val(t.arg1)
        elif isinstance(t, PrintTriple):
            printed.append(val(t.arg1))
        elif isinstance(t, GotoTriple):
            pc = labels[t.label]
        elif isinstance(t, IfFalseTriple) and val(t.cond) == 0:
            pc = labels[t.label]
    return printed
