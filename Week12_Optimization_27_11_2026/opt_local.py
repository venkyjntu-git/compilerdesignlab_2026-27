"""
Local optimizations: constant folding and copy propagation.

Your work (part B): the BinOp and RelOp cases of fold_value(), and
copy_propagation(). The Cast/Select cases and constant_folding() itself
are provided.

Constant folding evaluates, at COMPILE time, any computation whose
operands are all constants, and replaces every use of its result by the
constant. It must give exactly the answer the program would compute at
RUN time on SPIM -- verified there before these rules were written:
  - int `/` truncates toward zero:      -7 / 2   ->  -3   (Python's // gives -4!)
  - (int) of a double truncates:        (int)2.7 ->  2,   (int)-2.7 -> -2
  - an int result outside 32 bits is NOT folded (MIPS add traps on overflow)
  - division by zero is NOT folded (let it fail at run time, as unoptimized)

Copy propagation, inside one basic block: after `x = y` (y a variable or
a constant), later uses of x in the same block read y instead -- until x
or y is assigned again, or a CALL (which may change globals) intervenes.
Propagating constants is what makes folding cascade:
    a = 0 - 5;  b = a * 2;   ->   a = -5;  b = -5 * 2   ->   b = -10
"""
from SymbolTable import DataType
from three_address_code import (BinOpTriple, RelOpTriple, CastTriple, SelectTriple,
                                AssignTriple, CallTriple, TripleRef)
from tac_to_mips import literal_kind
from ir_utils import (operand_fields, is_variable, is_constant, delete, is_deleted,
                      replace_uses, delete_unused_value)

INT_MIN, INT_MAX = -2 ** 31, 2 ** 31 - 1


def _int_literal(value):
    return str(value) if INT_MIN <= value <= INT_MAX else None


def _double_literal(value):
    text = repr(float(value))
    return text if literal_kind(text) == 'double' else None   # no 1e-07, inf, nan


def _truncating_div(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _compute(op, a, b):
    return {'+': a + b, '-': a - b, '*': a * b}[op]


def fold_value(triple):
    """
    The constant (as literal text) that `triple` always produces, or None
    if it can't be folded. For a SelectTriple with a constant condition,
    returns the chosen OPERAND (which may be a variable or a TripleRef).
    """
    if isinstance(triple, BinOpTriple):
        # TODO(week-12, part B): fold `+ - * /` when BOTH operands are
        # constants (is_constant()). Operands are literal TEXT: convert with
        # float(...) when triple.result_type is DataType.DOUBLE, int(...)
        # otherwise. Build the result text with _double_literal() /
        # _int_literal() -- they return None when the result can't be a
        # literal (too big for 32 bits, or 1e-07 style), and None means
        # "don't fold". For '/': a zero divisor -> None; an int quotient
        # must come from _truncating_div() -- NOT Python's // (see the
        # module docstring: -7 / 2 is -3 on SPIM). _compute() does + - *.
        raise NotImplementedError("implement BinOp folding in fold_value()")

    if isinstance(triple, RelOpTriple):
        # TODO(week-12, part B): both operands constant -> compare them as
        # numbers (float() is exact for our ints) and return '1' or '0'.
        raise NotImplementedError("implement RelOp folding in fold_value()")

    if isinstance(triple, CastTriple):
        kind = literal_kind(triple.arg)
        if triple.target_type == DataType.DOUBLE and kind == 'int':
            return _double_literal(int(triple.arg))
        if triple.target_type in (DataType.INT, DataType.CHAR) and kind == 'double':
            return _int_literal(int(float(triple.arg)))       # int() truncates, like cvt.w.d
        if triple.target_type == DataType.INT and kind == 'char':
            return str(ord(triple.arg[1:-1]))
        return None

    if isinstance(triple, SelectTriple):
        kind = literal_kind(triple.cond)
        if kind in ('int', 'double'):
            truthy = float(triple.cond) != 0.0
        elif kind == 'char':
            truthy = ord(triple.cond[1:-1]) != 0
        else:
            return None
        return triple.then_val if truthy else triple.else_val
    return None


def constant_folding(triples):
    """Folds every foldable triple, in order (so folds cascade). Returns the number folded."""
    folded = 0
    for t in triples:
        if is_deleted(t):
            continue
        value = fold_value(t)
        if value is None:
            continue
        replace_uses(triples, TripleRef(t.index), value)
        delete(t)
        folded += 1
        if isinstance(t, SelectTriple):
            # the branch NOT chosen was computed for nothing
            for unused in (t.then_val, t.else_val):
                if isinstance(unused, TripleRef) and unused != value:
                    delete_unused_value(triples, unused.index)
    return folded


def copy_propagation(cfg, global_names):
    """
    TODO(week-12, part B): within each basic block SEPARATELY (start every
    block with an empty `copies` dict: variable -> the operand it is a copy
    of). Returns the number of operands replaced.

    For each non-deleted triple t of the block, in order:
      1. REWRITE: for each f in operand_fields(t), if getattr(t, f) is a
         variable (is_variable) that is in copies, setattr(t, f, copies[...])
         and count it.
      2. UPDATE what is known:
         - AssignTriple `x = ...`: x has a new value, so forget every entry
           whose key OR value is x. Then, if the right-hand side t.arg1 is a
           variable or a literal (literal_kind(...) is not None) -- but not a
           TripleRef, and not x itself -- record copies[x] = t.arg1.
         - CallTriple: the callee may assign any GLOBAL, so forget every
           entry whose key or value is in global_names.
    Why only one block: at a label, control may arrive from somewhere that
    never executed `x = y` (docs/optimization_reference.md #2).
    """
    raise NotImplementedError("implement copy_propagation()")
