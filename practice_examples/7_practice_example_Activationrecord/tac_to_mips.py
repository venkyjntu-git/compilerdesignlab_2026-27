"""
Three-Address Code to MIPS -- with ACTIVATION RECORDS (stack frames).

Practice 5 wrote a variable's address as a placeholder, `disp($fp)ofx`.
Here every variable gets a REAL offset from $fp in its function's frame,
so the generated program runs on SPIM.

Frame of one function (the stack grows DOWN, toward lower addresses):

        higher addresses
        | caller's frame      |
        | saved $ra           |  frame_size + 4 ($fp)
        | saved $fp (caller's)|  frame_size + 0 ($fp)
        | local variables     |  after the parameters
        | parameters          |  0 ($fp), 4 ($fp), ...   (copied from $a0-$a3)
        +---------------------+  <- $fp = $sp
        lower addresses

Calling convention (a small version of MIPS's own):
  - argument 1..4 in $a0..$a3   (this example allows at most 4)
  - result in $v0
  - jal f  puts the return address in $ra;  jr $ra  goes back
  - $t0-$t9 are CALLER-saved: a value still needed after a call is pushed
    on the stack before the call and popped after it.
"""
from three_address_code import (BinOpTriple, AssignTriple, PrintTriple, ParamTriple,
                                CallTriple, ReturnTriple, TripleRef, is_literal)

MIPS_OP = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div'}
ARG_REGS = ['$a0', '$a1', '$a2', '$a3']


def function_label(name):
    # SPIM starts the program with `jal main`; other names get a prefix so that a
    # function called `add` or `b` can't clash with a MIPS instruction name
    return "main" if name == "main" else f"f_{name}"


class FrameLayout:
    """Offsets from $fp: parameters first, then locals, 4 bytes each."""

    def __init__(self, function):
        if len(function.params) > len(ARG_REGS):
            raise ValueError(f"{function.name}: this example supports at most 4 parameters")
        self.offset = {}
        for name in function.params + function.locals():
            self.offset[name] = 4 * len(self.offset)
        self.size = 4 * len(self.offset)

    def describe(self, function):
        lines = [f"Frame of {function.name}: {self.size} bytes of variables"]
        lines.append(f"  {self.size + 4:3}($fp)  saved $ra")
        lines.append(f"  {self.size:3}($fp)  saved $fp")
        for name, off in sorted(self.offset.items(), key=lambda kv: -kv[1]):
            kind = "parameter" if name in function.params else "local"
            lines.append(f"  {off:3}($fp)  {name}  ({kind})")
        return "\n".join(lines)


class MIPSGenerator:
    def __init__(self, function):
        self.function = function
        self.frame = FrameLayout(function)
        self.lines = []
        self.free = [True] * 10           # $t0-$t9
        self.triple_reg = {}              # triple index -> register holding its value
        self.pending_params = []          # PARAMs waiting for their CALL

    # --- registers: allocated when a value is produced, freed when it is USED ---
    def alloc(self):
        i = self.free.index(True)
        self.free[i] = False
        return f"$t{i}"

    def release(self, reg):
        self.free[int(reg[2:])] = True

    def emit(self, line, comment=""):
        self.lines.append(f"    {line:<24}# {comment}" if comment else f"    {line}")

    def value(self, operand):
        """A register holding the operand's value (literal, variable or earlier triple)."""
        if isinstance(operand, TripleRef):
            return self.triple_reg[operand.index]
        reg = self.alloc()
        if is_literal(operand):
            self.emit(f"li {reg}, {operand}")
        else:
            self.emit(f"lw {reg}, {self.frame.offset[operand]}($fp)", operand)
        return reg

    # --- the activation record ---
    def prologue(self):
        self.lines.append(f"{function_label(self.function.name)}:")
        self.emit("subu $sp, $sp, 4", "PROLOGUE: push $ra")
        self.emit("sw   $ra, 0($sp)")
        self.emit("subu $sp, $sp, 4", "push the caller's $fp")
        self.emit("sw   $fp, 0($sp)")
        self.emit(f"addiu $fp, $sp, -{self.frame.size}", f"new frame: {self.frame.size} bytes")
        self.emit("move $sp, $fp")
        for i, name in enumerate(self.function.params):
            self.emit(f"sw {ARG_REGS[i]}, {self.frame.offset[name]}($fp)",
                      f"parameter {name} from {ARG_REGS[i]}")

    def epilogue(self):
        self.lines.append(f"ret_{self.function.name}:")
        self.emit(f"addiu $sp, $fp, {self.frame.size}", "EPILOGUE: drop the frame")
        self.emit("lw    $fp, 0($sp)", "restore the caller's $fp")
        self.emit("addiu $sp, $sp, 4")
        self.emit("lw    $ra, 0($sp)", "restore the return address")
        self.emit("addiu $sp, $sp, 4")
        self.emit("jr    $ra", "back to the caller")

    # --- one triple ---
    def gen_instr(self, t):
        if isinstance(t, BinOpTriple):
            r1, r2 = self.value(t.arg1), self.value(t.arg2)
            dest = self.alloc()
            self.emit(f"{MIPS_OP[t.op]} {dest}, {r1}, {r2}")
            self.triple_reg[t.index] = dest
            self.release(r1)
            self.release(r2)
        elif isinstance(t, AssignTriple):
            reg = self.value(t.arg1)
            self.emit(f"sw {reg}, {self.frame.offset[t.dest]}($fp)", t.dest)
            self.release(reg)
        elif isinstance(t, PrintTriple):
            reg = self.value(t.arg1)
            self.emit(f"move $a0, {reg}", "print an integer")
            self.emit("li $v0, 1")
            self.emit("syscall")
            self.emit("li $a0, 10", "print a newline")
            self.emit("li $v0, 11")
            self.emit("syscall")
            self.release(reg)
        elif isinstance(t, ParamTriple):
            self.pending_params.append(t)       # placed by the CALL
        elif isinstance(t, CallTriple):
            self.gen_call(t)
        elif isinstance(t, ReturnTriple):
            reg = self.value(t.arg)
            self.emit(f"move $v0, {reg}", "the result goes in $v0")
            self.release(reg)
            self.emit(f"j ret_{self.function.name}")

    def gen_call(self, t):
        params, self.pending_params = self.pending_params, []
        arg_regs = {self.triple_reg[p.arg.index] for p in params if isinstance(p.arg, TripleRef)}
        # 1. save every temporary still needed AFTER the call
        saved = [f"$t{i}" for i, free in enumerate(self.free)
                 if not free and f"$t{i}" not in arg_regs]
        for reg in saved:
            self.emit("subu $sp, $sp, 4", f"CALL {t.name}: save {reg}, needed after the call")
            self.emit(f"sw {reg}, 0($sp)")
        # 2. arguments into $a0..$a3
        for i, p in enumerate(params):
            reg = self.value(p.arg)
            self.emit(f"move {ARG_REGS[i]}, {reg}", f"argument {i + 1}")
            self.release(reg)
        # 3. the call: $ra := address of the next instruction
        self.emit(f"jal {function_label(t.name)}")
        # 4. the result, out of $v0
        dest = self.alloc()
        self.emit(f"move {dest}, $v0", "the result")
        self.triple_reg[t.index] = dest
        # 5. restore the saved temporaries, in reverse order
        for reg in reversed(saved):
            self.emit(f"lw {reg}, 0($sp)", f"restore {reg}")
            self.emit("addiu $sp, $sp, 4")

    def generate(self, triples):
        self.prologue()
        for t in triples:
            self.gen_instr(t)
        self.epilogue()
        return "\n".join(self.lines)


def generate_mips(functions_and_triples):
    """The whole .s file: one block of code per function."""
    parts = [".text", ".globl main"]
    for function, program in functions_and_triples:
        parts.append(MIPSGenerator(function).generate(program.triples))
    return "\n".join(parts) + "\n"
