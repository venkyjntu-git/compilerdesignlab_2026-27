"""
Helpers for EDITING a function's triples -- provided, do not modify.

Every optimization pass works the same way:
  1. it decides what to change, and
  2. changes it with these helpers:
       replace_uses()  -- every use of one operand now uses another
       delete()        -- mark a triple for removal
       compact()       -- actually remove deleted triples, RENUMBER the
                          rest, and fix every TripleRef to match.

Why compact() is needed: a triple is named by its POSITION. After (3)
is removed, the old (4) becomes the new (3), and every TripleRef(4)
anywhere in the function must become TripleRef(3) -- or the program
silently computes with the wrong value.
"""
from three_address_code import (
    BinOpTriple, RelOpTriple, CastTriple, SelectTriple, AssignTriple, PrintTriple,
    LabelTriple, GotoTriple, IfFalseTriple, ParamTriple, CallTriple, ReturnTriple,
    TripleRef,
)
from tac_to_mips import literal_kind

OPERAND_FIELDS = {
    BinOpTriple: ('arg1', 'arg2'),
    RelOpTriple: ('arg1', 'arg2'),
    CastTriple: ('arg',),
    SelectTriple: ('cond', 'then_val', 'else_val'),
    AssignTriple: ('arg1',),
    PrintTriple: ('arg1',),
    IfFalseTriple: ('cond',),
    ParamTriple: ('arg',),
    ReturnTriple: ('arg',),
    LabelTriple: (),
    GotoTriple: (),
    CallTriple: (),
}

# Triples that only COMPUTE a value: removing one whose value nobody uses
# changes nothing else. (A CallTriple is never pure -- the callee may print,
# or change a global.)
PURE = (BinOpTriple, RelOpTriple, CastTriple, SelectTriple)


def operand_fields(triple):
    return OPERAND_FIELDS[type(triple)]


def operands(triple):
    """The triple's operands that are present (a `return;` has none)."""
    return [getattr(triple, f) for f in operand_fields(triple) if getattr(triple, f) is not None]


def is_variable(operand):
    """A variable NAME -- not a literal, not a TripleRef."""
    return isinstance(operand, str) and literal_kind(operand) is None


def is_constant(operand):
    """A numeric literal: int or double (possibly negative)."""
    return literal_kind(operand) in ('int', 'double')


def is_deleted(triple):
    return getattr(triple, 'deleted', False)


def delete(triple):
    triple.deleted = True


def live_triples(triples):
    return [t for t in triples if not is_deleted(t)]


def replace_uses(triples, old, new):
    """Every operand equal to `old` (a TripleRef or a variable name) becomes `new`.
    Returns how many operands changed."""
    count = 0
    for t in triples:
        if is_deleted(t):
            continue
        for f in operand_fields(t):
            if getattr(t, f) == old:
                setattr(t, f, new)
                count += 1
    return count


def uses_of(triples, index):
    """How many operands, in live triples, refer to TripleRef(index)."""
    ref = TripleRef(index)
    return sum(1 for t in triples if not is_deleted(t) for op in operands(t) if op == ref)


def delete_unused_value(triples, index):
    """
    The value of triple `index` is no longer used. Delete it if it is pure --
    and then, recursively, whatever computed ITS operands. A CallTriple is
    kept (the call still has to happen); only its result is dropped.
    """
    t = triples[index]
    if is_deleted(t) or uses_of(triples, index) > 0:
        return
    if isinstance(t, CallTriple):
        t.value_used = False
        return
    if not isinstance(t, PURE):
        return
    delete(t)
    for op in operands(t):
        if isinstance(op, TripleRef):
            delete_unused_value(triples, op.index)


def compact(triples):
    """Removes deleted triples, renumbers the rest from (0), and remaps every TripleRef."""
    new_index = {}
    kept = []
    for t in triples:
        if not is_deleted(t):
            new_index[t.index] = len(kept)
            kept.append(t)
    for t in kept:
        for f in operand_fields(t):
            op = getattr(t, f)
            if isinstance(op, TripleRef):
                setattr(t, f, TripleRef(new_index[op.index]))
        t.index = new_index[t.index]
    return kept


def render(triples):
    return "\n".join(t.render() for t in live_triples(triples))
