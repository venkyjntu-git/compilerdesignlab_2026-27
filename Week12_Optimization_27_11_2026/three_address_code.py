"""
Three-address code (3AC) -- TRIPLE representation. Provided fully
implemented.

WEEK 11 CHANGES (flagged): three call triples -- ParamTriple, CallTriple,
ReturnTriple -- at the end of this file, before TripleTAC.

WEEK 9 CHANGES (flagged): three control-flow triples -- LabelTriple,
GotoTriple, IfFalseTriple -- at the end of this file, before TripleTAC.
See docs/control_flow_3ac_reference.md. Everything below this note up to
them is unchanged from Week 7.

WEEK 7 CHANGES (flagged): Week 6's type checker now resolves and stores
a `result_type` on every AST node (see type_checker.py's module
docstring). This week's triples carry the SAME information forward, so
tac_to_mips.py can pick the right MIPS instruction family (integer vs
floating-point) for every operation without re-deriving types from
scratch:
  - BinOpTriple gained a `result_type` field.
  - Two NEW triple types: RelOpTriple (comparisons) and CastTriple
    (int<->double conversions).
  - ONE more new type: SelectTriple, for the ternary operator. It is
    DELIBERATELY still a single, flat triple at the 3AC level -- NOT a
    sequence of branch/label triples. "Implement ternary as a
    branch-based MIPS sequence" (this week's lab plan) means the
    BRANCHING happens only inside tac_to_mips.py's SelectTriple handler;
    the 3AC layer stays simple and linear, one triple per source-level
    operation, exactly like every other triple. General branch/label 3AC
    (for if/while) is Week 8's own subject, not pulled forward here.
  - is_literal() now also recognizes floating-point literals
    ("3.14".isdigit() is False -- a real gap in earlier materials,
    documented in Week 6, fixed here).

A TRIPLE never names its own result. Instead, each triple is numbered by
its position in the program (0, 1, 2, ...), and any LATER triple that
needs an earlier one's result refers to it by that index -- written as
"(i)" in text form.

Triple shapes, each a small class with a render() method:

    BinOpTriple(op, arg1, arg2, result_type)
        op in {'+','-','*','/'}. result_type is the (already-promoted)
        type of the computation -- e.g. DOUBLE for an int+double
        expression after Week 6 inserted the necessary Cast.

    RelOpTriple(op, arg1, arg2, operand_type)
        op in {'<','>','<=','>=','==','!='}. operand_type is the
        (already-promoted) type of arg1/arg2 -- e.g. comparing two
        doubles needs different MIPS instructions than comparing two
        ints, even though a RelOpTriple's own logical result is always
        an INT 0/1 (see type_checker.py's check_relop -- a comparison's
        RESULT type is always DataType.INT).

    CastTriple(source_type, target_type, arg)
        Converts arg (of source_type) to target_type. Mirrors the Cast
        AST node 1:1, whether that Cast was written explicitly in the
        source or inserted implicitly by the type checker.

    SelectTriple(cond, cond_type, then_val, else_val, result_type)
        The ternary operator: cond ? then_val : else_val. cond_type is
        needed because testing whether a DOUBLE-typed condition is
        "truthy" needs different MIPS instructions than testing an
        INT-typed one.

    AssignTriple(dest, arg1)
        dest is always a real declared variable NAME (a plain string)
        -- its type is looked up from the symbol table at codegen time,
        not stored redundantly here.

    PrintTriple(arg1)
        Prints arg1's value -- its type is resolved the same way as any
        other operand at codegen time (see tac_to_mips.py's resolve()).

`arg1`/`arg2`/`cond`/`then_val`/`else_val` are always one of:
    - a plain variable name (string, e.g. "a")
    - a literal (a digit string, e.g. "5" or "3.14")
    - a TripleRef(i), pointing at an earlier triple's result

Use TripleTAC (below) to build a program -- its append() stamps each
triple's `.index` automatically and hands back a ready-to-use TripleRef.
"""


class TripleRef:
    """A reference to an earlier triple's result, by its index."""

    def __init__(self, index):
        self.index = index

    def render(self):
        return f"({self.index})"

    def __eq__(self, other):
        return isinstance(other, TripleRef) and self.index == other.index

    def __repr__(self):
        return f"TripleRef({self.index})"


def render_operand(operand):
    """Renders a plain name/literal string, or a TripleRef, to text."""
    if isinstance(operand, TripleRef):
        return operand.render()
    return str(operand)


def is_literal(operand):
    """
    True if `operand` is a literal number (as a string) rather than a
    variable name or a TripleRef.

    WEEK 7 FIX: earlier versions only recognized plain integer strings
    (`"5".isdigit()`), which silently mis-treated a floating-point
    literal's text ("3.14") as if it were a variable name -- documented
    as a known gap in Week 6's docs, fixed here now that double-typed
    codegen actually needs it to work.

    WEEK 12: also accepts a leading '-'. The grammar still has no unary
    minus, but constant folding can produce a negative literal (0 - 5).
    """
    if not isinstance(operand, str):
        return False
    if operand.startswith('-'):
        operand = operand[1:]
    if operand.isdigit():
        return True
    if operand.count('.') == 1:
        int_part, frac_part = operand.split('.')
        return int_part.isdigit() and frac_part.isdigit()
    return False


class BinOpTriple:
    def __init__(self, op, arg1, arg2, result_type):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result_type = result_type
        self.index = None  # set by TripleTAC.append()

    def render(self):
        return (f"({self.index}) {self.op} {render_operand(self.arg1)}, "
                f"{render_operand(self.arg2)} : {self.result_type.name}")


class RelOpTriple:
    def __init__(self, op, arg1, arg2, operand_type):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.operand_type = operand_type
        self.index = None

    def render(self):
        return (f"({self.index}) {self.op} {render_operand(self.arg1)}, "
                f"{render_operand(self.arg2)} : cmp {self.operand_type.name}")


class CastTriple:
    def __init__(self, source_type, target_type, arg):
        self.source_type = source_type
        self.target_type = target_type
        self.arg = arg
        self.index = None

    def render(self):
        return (f"({self.index}) CAST({self.target_type.name}) "
                f"{render_operand(self.arg)} : from {self.source_type.name}")


class SelectTriple:
    """The ternary operator -- see module docstring for why this stays
    one flat triple at the 3AC level, with branching pushed entirely
    into tac_to_mips.py."""

    def __init__(self, cond, cond_type, then_val, else_val, result_type):
        self.cond = cond
        self.cond_type = cond_type
        self.then_val = then_val
        self.else_val = else_val
        self.result_type = result_type
        self.index = None

    def render(self):
        return (f"({self.index}) {render_operand(self.cond)} ? "
                f"{render_operand(self.then_val)} : {render_operand(self.else_val)} "
                f": {self.result_type.name}")


class AssignTriple:
    def __init__(self, dest, arg1):
        self.dest = dest
        self.arg1 = arg1
        self.index = None

    def render(self):
        return f"({self.index}) {self.dest} = {render_operand(self.arg1)}"


class PrintTriple:
    def __init__(self, arg1):
        self.arg1 = arg1
        self.index = None

    def render(self):
        return f"({self.index}) PRINT {render_operand(self.arg1)}"


# ----------------------------------------------------------------------
# WEEK 9 -- control flow. Three new triples that DON'T compute a value
# (nothing ever holds a TripleRef to them); they only change which
# triple runs next. Labels are plain strings "L0", "L1", ... handed out
# by TACGenerator.new_label().
# ----------------------------------------------------------------------
class LabelTriple:
    """A jump target. Marks a position in the triple list; emits no computation."""

    def __init__(self, label):
        self.label = label
        self.index = None

    def render(self):
        return f"({self.index}) {self.label}:"


class GotoTriple:
    """Unconditional jump: goto label."""

    def __init__(self, label):
        self.label = label
        self.index = None

    def render(self):
        return f"({self.index}) goto {self.label}"


class IfFalseTriple:
    """
    Conditional jump: if cond is FALSE (== 0) goto label; otherwise fall
    through to the next triple. cond_type is carried for the same reason
    SelectTriple carries it: testing a DOUBLE condition against zero needs
    different MIPS instructions than testing an INT one.
    """

    def __init__(self, cond, cond_type, label):
        self.cond = cond
        self.cond_type = cond_type
        self.label = label
        self.index = None

    def render(self):
        return (f"({self.index}) if_false {render_operand(self.cond)} goto {self.label} "
                f": {self.cond_type.name}")


# ----------------------------------------------------------------------
# WEEK 11 -- function calls. See docs/calls_3ac_reference.md.
# ----------------------------------------------------------------------
class ParamTriple:
    """
    One argument of the NEXT CallTriple. A call f(x, y) becomes
        PARAM x
        PARAM y
        CALL f, 2
    and the PARAMs of one call are always CONSECUTIVE, immediately before
    their CALL: any call nested inside an argument is generated completely
    (its own PARAMs and CALL) before the outer call's first PARAM.
    arg_type is the PARAMETER's type -- the type checker has already
    inserted any Cast needed to convert the argument to it.
    """

    def __init__(self, arg, arg_type):
        self.arg = arg
        self.arg_type = arg_type
        self.index = None

    def render(self):
        return f"({self.index}) PARAM {render_operand(self.arg)} : {self.arg_type.name}"


class CallTriple:
    """
    CALL name, nargs -- produces the callee's return value (a TripleRef to
    this triple refers to it), unless the function is VOID or the call is
    a statement whose value is thrown away (value_used=False).
    """

    def __init__(self, name, nargs, return_type, value_used=True):
        self.name = name
        self.nargs = nargs
        self.return_type = return_type
        self.value_used = value_used
        self.index = None

    def render(self):
        text = f"({self.index}) CALL {self.name}, {self.nargs} : {self.return_type.name}"
        if not self.value_used and self.return_type.name != 'VOID':
            text += " (result unused)"
        return text


class ReturnTriple:
    """RETURN [value] -- leave the function, handing `arg` (if any) back to the caller."""

    def __init__(self, arg, return_type):
        self.arg = arg                  # None for `return;`
        self.return_type = return_type  # the FUNCTION's return type
        self.index = None

    def render(self):
        if self.arg is None:
            return f"({self.index}) RETURN"
        return f"({self.index}) RETURN {render_operand(self.arg)} : {self.return_type.name}"


class TripleTAC:
    """
    A flat, ordered list of triples for one function, with automatic
    index assignment.
    """

    def __init__(self):
        self.triples = []

    def append(self, triple):
        """
        Sets `triple.index` with its position in the program and
        returns a TripleRef pointing at it -- handy since gen_expr()
        usually wants that ref immediately after appending.
        """
        triple.index = len(self.triples)
        self.triples.append(triple)
        return TripleRef(triple.index)

    def render(self):
        return "\n".join(t.render() for t in self.triples)

    def __len__(self):
        return len(self.triples)

    def __iter__(self):
        return iter(self.triples)
