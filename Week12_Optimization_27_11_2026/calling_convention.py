"""
The TinyCStr calling convention -- provided, do not modify.

Read docs/activation_records.md first. Everything a CALLER and a CALLEE
must agree on lives in this one file, so the two sides can never drift
apart: where each argument goes, where the result comes back, and what
the assembly labels are called.

Arguments (position i = 0, 1, 2, ...):
  - int / char / string argument at position i < 4  ->  register $a<i>
  - every other argument (a double, or position >= 4) ->  the stack
    "argument area", in parameter order, 4 bytes per int-family value and
    8 per double, the FIRST stack argument at the LOWEST address.
  Register numbering follows the POSITION, as in MIPS O32: in f(int, double, int)
  the second int is in $a2, and $a1 is simply unused.
  (O32 passes leading doubles in $f12/$f14; TinyCStr deliberately keeps
  every double on the stack -- one rule fewer, see the docs.)

Result:
  - int / char / string  ->  $v0
  - double               ->  $f0
  - void                 ->  nothing

Registers:
  - caller-saved: $t0-$t9 and $f0-$f30 (our temporaries). A caller that
    still needs a temporary after the call pushes it before the call and
    pops it afterwards.
  - callee-saved: $ra and $fp (the prologue/epilogue save and restore
    them). $s0-$s7 are never used by this compiler, so nothing else needs
    saving.
"""
from SymbolTable import DataType

ARG_REGS = ['$a0', '$a1', '$a2', '$a3']
SAVED_FP_RA_BYTES = 8   # the prologue pushes $ra and $fp: 4 bytes each


def is_double(datatype):
    return datatype == DataType.DOUBLE


def arg_locations(param_types):
    """
    Returns (locations, stack_bytes). locations[i] is
        ('reg', '$a<i>')        -- in an argument register, or
        ('stack', offset)       -- at `offset` bytes into the stack argument area
    stack_bytes is the size of the whole stack argument area.
    """
    locations = []
    offset = 0
    for i, datatype in enumerate(param_types):
        if i < len(ARG_REGS) and not is_double(datatype):
            locations.append(('reg', ARG_REGS[i]))
        else:
            locations.append(('stack', offset))
            offset += 8 if is_double(datatype) else 4
    return locations, offset


def function_label(name):
    """
    `main` must stay `main` -- SPIM's startup code does `jal main`. Every
    other function gets an f_ prefix: Example 4's `add` is a MIPS
    instruction name, and SPIM rejects `add:` as a label.
    """
    return "main" if name == "main" else f"f_{name}"


def return_label(name):
    """Where every `return` in function `name` jumps to: the start of its epilogue."""
    return f"ret_{name}"
