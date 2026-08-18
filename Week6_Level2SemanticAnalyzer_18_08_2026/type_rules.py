"""
Type rules -- provided fully implemented.

Week 6's learning objective is APPLYING these rules while walking the
AST (type_checker.py) These rules encode TinyCStr's C-like promotion policy

TinyCStr's promotion policy (assumed similar to C):
  - INT, DOUBLE, CHAR are all "numeric" -- arithmetic and relational
    operators can mix any combination of them, with implicit promotion.
  - STRING is NOT numeric -- it never silently promotes to/from anything.
  - Between two numeric types: if EITHER is DOUBLE, the result is
    DOUBLE (a DOUBLE always wins). Otherwise (CHAR/INT combinations,
    including CHAR with itself) the result is INT -- this matches C's
    "integer promotion" rule, where arithmetic on anything narrower than
    int is always at least int-typed, even char + char.
"""
from SymbolTable import DataType

NUMERIC_TYPES = {DataType.INT, DataType.DOUBLE, DataType.CHAR}


def is_numeric(datatype):
    return datatype in NUMERIC_TYPES


def promote(type1, type2):
    """
    Given two NUMERIC types, returns the promoted result type -- DOUBLE
    if either operand is DOUBLE, else INT. Only call this when both
    type1 and type2 are_numeric() -- it doesn't handle STRING at all
    (STRING mixing is always an error, checked separately in
    type_checker.py, never "promoted").
    """
    if type1 == DataType.DOUBLE or type2 == DataType.DOUBLE:
        return DataType.DOUBLE
    return DataType.INT


class SemanticError:
    """One type-checking error: a message plus the line it occurred on."""

    def __init__(self, message, lineno):
        self.message = message
        self.lineno = lineno

    def __str__(self):
        line = self.lineno if self.lineno is not None else '?'
        return f"line {line}: {self.message}"
