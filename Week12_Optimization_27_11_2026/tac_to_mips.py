"""
Three-Address Code (triples) to MIPS generator -- Levels 1-4.

REFERENCE IMPLEMENTATION, fully complete through Level 4.

WEEK 11 CHANGES:
  1. One MIPSGenerator per FUNCTION, all sharing one ProgramContext: the
     string-literal pool (one .data section for the whole program) and
     the label counter (so two functions never emit the same label).
     render_program() assembles the finished .s file.
  2. Every function gets its own label (calling_convention.function_label)
     and an activation record: the Week 4 prologue/epilogue, which already
     saved $ra and $fp, plus "homing" -- storing each register argument
     ($a0-$a3) into the function's own frame -- right after the prologue.
  3. Names resolve locals -> parameters -> globals (as in the type checker).
  4. PARAM / CALL / RETURN code generation: gen_param, gen_call, gen_return.
     See docs/activation_records.md.

Earlier weeks: control flow and globals (Week 9), mixed types (Week 7).
"""
from SymbolTable import DataType
from three_address_code import (
    BinOpTriple, RelOpTriple, CastTriple, SelectTriple, AssignTriple, PrintTriple,
    LabelTriple, GotoTriple, IfFalseTriple,
    ParamTriple, CallTriple, ReturnTriple,
    TripleRef,
)
from calling_convention import (arg_locations, function_label, return_label,
                                SAVED_FP_RA_BYTES)

INT_OP = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div'}
DBL_OP = {'+': 'add.d', '-': 'sub.d', '*': 'mul.d', '/': 'div.d'}
INT_BRANCH_TRUE = {'<': 'blt', '>': 'bgt', '<=': 'ble', '>=': 'bge', '==': 'beq', '!=': 'bne'}


def literal_kind(operand):
    """
    Returns 'int' / 'double' / 'char' / 'string' for a literal operand, else None.
    WEEK 12: numeric literals may now be NEGATIVE ("-5", "-2.5"). The source
    language still has no unary minus, but constant folding can produce one
    (`0 - 5` folds to -5); `li`/`li.d` accept negative values directly.
    """
    if not isinstance(operand, str):
        return None
    if operand.startswith('"') and operand.endswith('"'):
        return 'string'
    if operand.startswith("'") and operand.endswith("'"):
        return 'char'
    number = operand[1:] if operand.startswith('-') else operand
    if number.isdigit():
        return 'int'
    if number.count('.') == 1:
        a, b = number.split('.')
        if a.isdigit() and b.isdigit():
            return 'double'
    return None


def triple_result_type(triple):
    """DataType of a value-producing triple's result (for resolving a TripleRef)."""
    if isinstance(triple, BinOpTriple):
        return triple.result_type
    if isinstance(triple, RelOpTriple):
        return DataType.INT
    if isinstance(triple, CastTriple):
        return triple.target_type
    if isinstance(triple, SelectTriple):
        return triple.result_type
    if isinstance(triple, CallTriple):      # WEEK 11
        return triple.return_type
    raise ValueError(f"triple has no referenceable result: {type(triple)}")


class ProgramContext:
    """WEEK 11: what all functions of one program share while being compiled."""

    def __init__(self, first_label=0):
        self.label_counter = first_label
        self.string_labels = {}
        self.data_lines = []

    def new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def get_string_label(self, text):
        if text in self.string_labels:
            return self.string_labels[text]
        label = f"Lstr{len(self.string_labels)}"
        self.string_labels[text] = label
        self.data_lines.append(f'{label}: .asciiz "{text}"')
        return label


class MIPSGenerator:
    def __init__(self, function, triples, global_symbol_table=None, context=None):
        self.function = function
        self.symbol_table = function.getLocalSymbolTable()
        self.param_symbol_table = function.getParamSymbolTable()
        self.global_symbol_table = global_symbol_table
        self.triples = triples
        self.context = context if context is not None else ProgramContext(
            sum(isinstance(t, LabelTriple) for t in triples))
        self.int_avail = [True] * 10
        self.float_avail = [True] * 16  # $f0,$f2,...,$f30
        self.int_index_to_reg = {}
        self.float_index_to_reg = {}
        self.text_lines = []
        self.pending_params = []        # WEEK 11: PARAMs waiting for their CALL

    # ------------------------------------------------------------------
    # Register allocation, labels, string data
    # ------------------------------------------------------------------
    def alloc_int(self):
        i = self.int_avail.index(True)
        self.int_avail[i] = False
        return f"$t{i}"

    def free_int(self, reg):
        self.int_avail[int(reg[2:])] = True

    def alloc_float(self):
        i = self.float_avail.index(True)
        self.float_avail[i] = False
        return f"$f{i * 2}"

    def free_float(self, reg):
        self.float_avail[int(reg[2:]) // 2] = True

    def live_registers(self):
        """WEEK 11: every temporary currently holding a value, as (reg, is_double) pairs."""
        live = [(f"$t{i}", False) for i, free in enumerate(self.int_avail) if not free]
        live += [(f"$f{i * 2}", True) for i, free in enumerate(self.float_avail) if not free]
        return live

    def new_label(self):
        return self.context.new_label()

    def get_string_label(self, text):
        return self.context.get_string_label(text)

    def emit(self, line):
        self.text_lines.append(line)

    def is_double_family(self, t):
        return t == DataType.DOUBLE

    def free_reg(self, reg, op_type):
        if self.is_double_family(op_type):
            self.free_float(reg)
        else:
            self.free_int(reg)

    # ------------------------------------------------------------------
    # Variables: local / parameter (stack frame) or global (.data)
    # ------------------------------------------------------------------
    def lookup(self, name):
        """Locals, then parameters, then globals -- the same rule as the type checker."""
        entry = self.symbol_table.getSymbol(name)
        if entry is None:
            entry = self.param_symbol_table.getSymbol(name)
        if entry is not None:
            return entry, False
        return self.global_symbol_table.getSymbol(name), True

    def address(self, name):
        """The MIPS memory operand for a variable: `8($fp)` or `g_name`."""
        entry, is_global = self.lookup(name)
        return f"g_{name}" if is_global else f"{entry.getOffset()}($fp)"

    def resolve_type(self, operand):
        if isinstance(operand, TripleRef):
            return triple_result_type(self.triples[operand.index])
        kind = literal_kind(operand)
        if kind == 'int':
            return DataType.INT
        if kind == 'double':
            return DataType.DOUBLE
        if kind == 'char':
            return DataType.CHAR
        if kind == 'string':
            return DataType.STRING
        entry, _ = self.lookup(operand)
        return entry.getDataType()

    def load(self, operand, op_type):
        """
        Gets `operand`'s value into a register of the family matching
        op_type. Returns (reg, was_fresh); the CONSUMER frees reg either way.
        """
        if isinstance(operand, TripleRef):
            if self.is_double_family(op_type):
                return self.float_index_to_reg[operand.index], False
            return self.int_index_to_reg[operand.index], False
        kind = literal_kind(operand)
        if kind == 'double':
            reg = self.alloc_float()
            self.emit(f"li.d {reg}, {operand}")
        elif kind == 'int':
            reg = self.alloc_int()
            self.emit(f"li {reg}, {operand}")
        elif kind == 'char':
            reg = self.alloc_int()
            self.emit(f"li {reg}, {ord(operand[1:-1])}")
        elif kind == 'string':
            reg = self.alloc_int()
            self.emit(f"la {reg}, {self.get_string_label(operand[1:-1])}")
        elif self.is_double_family(op_type):
            reg = self.alloc_float()
            self.emit(f"l.d {reg}, {self.address(operand)}")
        else:
            reg = self.alloc_int()
            self.emit(f"lw {reg}, {self.address(operand)}")
        return reg, True

    def store_to_var(self, reg, name, reg_type):
        op = "s.d" if self.is_double_family(reg_type) else "sw"
        self.emit(f"{op} {reg}, {self.address(name)}")

    def record(self, triple, reg, reg_type):
        if self.is_double_family(reg_type):
            self.float_index_to_reg[triple.index] = reg
        else:
            self.int_index_to_reg[triple.index] = reg

    # ------------------------------------------------------------------
    # Per-triple codegen
    # ------------------------------------------------------------------
    def gen_instr(self, triple):
        if isinstance(triple, BinOpTriple):
            self.gen_binop(triple)
        elif isinstance(triple, RelOpTriple):
            self.gen_relop(triple)
        elif isinstance(triple, CastTriple):
            self.gen_cast(triple)
        elif isinstance(triple, SelectTriple):
            self.gen_select(triple)
        elif isinstance(triple, AssignTriple):
            self.gen_assign(triple)
        elif isinstance(triple, PrintTriple):
            self.gen_print(triple)
        elif isinstance(triple, LabelTriple):
            self.gen_label(triple)
        elif isinstance(triple, GotoTriple):
            self.gen_goto(triple)
        elif isinstance(triple, IfFalseTriple):
            self.gen_iffalse(triple)
        # WEEK 11 -- calls
        elif isinstance(triple, ParamTriple):
            self.gen_param(triple)
        elif isinstance(triple, CallTriple):
            self.gen_call(triple)
        elif isinstance(triple, ReturnTriple):
            self.gen_return(triple)
        else:
            raise ValueError(f"unexpected triple type: {type(triple)}")

    def gen_binop(self, triple):
        t = triple.result_type
        r1, _ = self.load(triple.arg1, t)
        r2, _ = self.load(triple.arg2, t)
        if self.is_double_family(t):
            dest = self.alloc_float()
            self.emit(f"{DBL_OP[triple.op]} {dest}, {r1}, {r2}")
        else:
            dest = self.alloc_int()
            self.emit(f"{INT_OP[triple.op]} {dest}, {r1}, {r2}")
        self.record(triple, dest, t)
        self.free_reg(r1, t)
        self.free_reg(r2, t)

    def gen_relop(self, triple):
        t = triple.operand_type
        r1, _ = self.load(triple.arg1, t)
        r2, _ = self.load(triple.arg2, t)
        dest = self.alloc_int()
        l_true = self.new_label()
        l_end = self.new_label()
        if self.is_double_family(t):
            op = triple.op
            if op in ('<', '<=', '=='):
                cmp = {'<': 'c.lt.d', '<=': 'c.le.d', '==': 'c.eq.d'}[op]
                self.emit(f"{cmp} {r1}, {r2}")
                self.emit(f"bc1t {l_true}")
            elif op in ('>', '>='):
                cmp = {'>': 'c.lt.d', '>=': 'c.le.d'}[op]
                self.emit(f"{cmp} {r2}, {r1}")   # operands swapped
                self.emit(f"bc1t {l_true}")
            else:  # '!='
                self.emit(f"c.eq.d {r1}, {r2}")
                self.emit(f"bc1f {l_true}")
        else:
            self.emit(f"{INT_BRANCH_TRUE[triple.op]} {r1}, {r2}, {l_true}")
        self.emit(f"li {dest}, 0")
        self.emit(f"b {l_end}")
        self.emit(f"{l_true}:")
        self.emit(f"li {dest}, 1")
        self.emit(f"{l_end}:")
        self.int_index_to_reg[triple.index] = dest
        self.free_reg(r1, t)
        self.free_reg(r2, t)

    def gen_cast(self, triple):
        src_t, dst_t = triple.source_type, triple.target_type
        src, _ = self.load(triple.arg, src_t)
        if self.is_double_family(src_t) and not self.is_double_family(dst_t):
            tmp = self.alloc_float()
            self.emit(f"cvt.w.d {tmp}, {src}")
            dest = self.alloc_int()
            self.emit(f"mfc1 {dest}, {tmp}")
            self.free_float(tmp)
        elif not self.is_double_family(src_t) and self.is_double_family(dst_t):
            tmp = self.alloc_float()
            self.emit(f"mtc1 {src}, {tmp}")
            dest = self.alloc_float()
            self.emit(f"cvt.d.w {dest}, {tmp}")
            self.free_float(tmp)
        else:
            self.record(triple, src, dst_t)
            return
        self.record(triple, dest, dst_t)
        self.free_reg(src, src_t)

    def gen_select(self, triple):
        rt = triple.result_type
        dest = self.alloc_float() if self.is_double_family(rt) else self.alloc_int()
        move = "mov.d" if self.is_double_family(rt) else "move"
        l_then = self.new_label()
        l_end = self.new_label()

        cond, _ = self.load(triple.cond, triple.cond_type)
        if self.is_double_family(triple.cond_type):
            zero = self.alloc_float()
            self.emit(f"li.d {zero}, 0.0")
            self.emit(f"c.eq.d {cond}, {zero}")
            self.emit(f"bc1f {l_then}")
            self.free_float(zero)
        else:
            self.emit(f"bne {cond}, $zero, {l_then}")
        self.free_reg(cond, triple.cond_type)

        reg, _ = self.load(triple.else_val, rt)
        self.emit(f"{move} {dest}, {reg}")
        self.free_reg(reg, rt)
        self.emit(f"b {l_end}")
        self.emit(f"{l_then}:")
        reg, _ = self.load(triple.then_val, rt)
        self.emit(f"{move} {dest}, {reg}")
        self.free_reg(reg, rt)
        self.emit(f"{l_end}:")
        self.record(triple, dest, rt)

    def gen_assign(self, triple):
        entry, _ = self.lookup(triple.dest)
        t = entry.getDataType()
        reg, _ = self.load(triple.arg1, t)
        self.store_to_var(reg, triple.dest, t)
        self.free_reg(reg, t)

    def gen_print(self, triple):
        t = self.resolve_type(triple.arg1)
        reg, _ = self.load(triple.arg1, t)
        if t == DataType.DOUBLE:
            self.emit(f"mov.d $f12, {reg}")
            self.emit("li $v0, 3")
        elif t == DataType.STRING:
            self.emit(f"move $a0, {reg}")
            self.emit("li $v0, 4")
        elif t == DataType.CHAR:
            self.emit(f"move $a0, {reg}")
            self.emit("li $v0, 11")
        else:
            self.emit(f"move $a0, {reg}")
            self.emit("li $v0, 1")
        self.emit("syscall")
        self.free_reg(reg, t)

    def gen_label(self, triple):
        self.emit(f"{triple.label}:")

    def gen_goto(self, triple):
        self.emit(f"j {triple.label}")

    def gen_iffalse(self, triple):
        reg, _ = self.load(triple.cond, triple.cond_type)
        if self.is_double_family(triple.cond_type):
            zero = self.alloc_float()
            self.emit(f"li.d {zero}, 0.0")
            self.emit(f"c.eq.d {reg}, {zero}")
            self.emit(f"bc1t {triple.label}")
            self.free_float(zero)
        else:
            self.emit(f"beq {reg}, $zero, {triple.label}")
        self.free_reg(reg, triple.cond_type)

    # ------------------------------------------------------------------
    # LEVEL 4 -- calls (Week 11)
    # ------------------------------------------------------------------
    def gen_param(self, triple):
        # Nothing is emitted yet: the CALL decides where every argument goes,
        # and must first save the caller's live temporaries (see gen_call).
        self.pending_params.append(triple)

    def gen_call(self, triple):
        params, self.pending_params = self.pending_params, []

        # 1. caller-saved temporaries still needed AFTER the call: everything
        #    allocated now, except registers that only hold this call's arguments
        arg_regs = set()
        for p in params:
            if isinstance(p.arg, TripleRef):
                arg_regs.add(self.float_index_to_reg[p.arg.index]
                             if self.is_double_family(p.arg_type)
                             else self.int_index_to_reg[p.arg.index])
        saved = [(reg, dbl) for reg, dbl in self.live_registers() if reg not in arg_regs]
        for reg, dbl in saved:
            if dbl:
                self.emit("subu $sp, $sp, 8")
                self.emit(f"s.d {reg}, 0($sp)")
            else:
                self.emit("subu $sp, $sp, 4")
                self.emit(f"sw {reg}, 0($sp)")

        # 2. arguments: $a0-$a3, or the stack argument area
        locations, stack_bytes = arg_locations([p.arg_type for p in params])
        if stack_bytes:
            self.emit(f"subu $sp, $sp, {stack_bytes}")
        for p, (kind, where) in zip(params, locations):
            reg, _ = self.load(p.arg, p.arg_type)
            if kind == 'reg':
                self.emit(f"move {where}, {reg}")
            elif self.is_double_family(p.arg_type):
                self.emit(f"s.d {reg}, {where}($sp)")
            else:
                self.emit(f"sw {reg}, {where}($sp)")
            self.free_reg(reg, p.arg_type)

        # 3. the call itself, then pop the argument area
        self.emit(f"jal {function_label(triple.name)}")
        if stack_bytes:
            self.emit(f"addiu $sp, $sp, {stack_bytes}")

        # 4. the result -- copied out of $v0/$f0 BEFORE restoring, since a
        #    restored temporary may be $f0 itself
        if triple.value_used and triple.return_type != DataType.VOID:
            if self.is_double_family(triple.return_type):
                dest = self.alloc_float()
                self.emit(f"mov.d {dest}, $f0")
            else:
                dest = self.alloc_int()
                self.emit(f"move {dest}, $v0")
            self.record(triple, dest, triple.return_type)

        # 5. restore the saved temporaries, in reverse order
        for reg, dbl in reversed(saved):
            if dbl:
                self.emit(f"l.d {reg}, 0($sp)")
                self.emit("addiu $sp, $sp, 8")
            else:
                self.emit(f"lw {reg}, 0($sp)")
                self.emit("addiu $sp, $sp, 4")

    def gen_return(self, triple):
        if triple.arg is not None:
            reg, _ = self.load(triple.arg, triple.return_type)
            if self.is_double_family(triple.return_type):
                self.emit(f"mov.d $f0, {reg}")
            else:
                self.emit(f"move $v0, {reg}")
            self.free_reg(reg, triple.return_type)
        self.emit(f"j {return_label(self.function.getName())}")

    # ------------------------------------------------------------------
    # Activation record: prologue / epilogue
    # ------------------------------------------------------------------
    def emit_prologue(self, frame_size):
        self.emit("subu $sp, $sp, 4")
        self.emit("sw   $ra, 0($sp)")
        self.emit("subu $sp, $sp, 4")
        self.emit("sw   $fp, 0($sp)")
        self.emit(f"addiu $fp, $sp, -{frame_size}")
        self.emit("move $sp, $fp")

    def emit_home_params(self):
        """
        WEEK 11: copy each REGISTER argument into the function's own frame,
        so the body reads parameters from memory like any local -- and so a
        later `print` (which overwrites $a0) or a nested call can't destroy them.
        """
        locations, _ = arg_locations(self.function.getParamTypes())
        for (_, name), (kind, reg) in zip(self.function.getParamList(), locations):
            if kind == 'reg':
                self.emit(f"sw {reg}, {self.address(name)}")

    def emit_epilogue(self, frame_size):
        self.emit(f"addiu $sp, $fp, {frame_size}")
        self.emit("lw    $fp, 0($sp)")
        self.emit("addiu $sp, $sp, 4")
        self.emit("lw    $ra, 0($sp)")
        self.emit("addiu $sp, $sp, 4")
        self.emit("jr    $ra")

    def generate(self, triples, frame_size):
        """Returns this function's body lines (prologue .. epilogue), not yet indented."""
        self.emit_prologue(frame_size)
        self.emit_home_params()
        for triple in triples:
            self.gen_instr(triple)
        if any(isinstance(t, ReturnTriple) for t in triples):
            self.emit(f"{return_label(self.function.getName())}:")
        self.emit_epilogue(frame_size)
        return self.text_lines


def global_data_lines(global_symbol_table):
    """One zero-initialized .data slot per global, doubles 8-byte aligned."""
    lines = []
    if global_symbol_table is None:
        return lines
    for entry in global_symbol_table.table:
        name = f"g_{entry.getSymbolName()}"
        if entry.getDataType() == DataType.DOUBLE:
            lines.append(".align 3")
            lines.append(f"{name}: .double 0.0")
        else:
            lines.append(f"{name}: .word 0")
    return lines


def render_program(context, global_symbol_table, functions_code):
    """
    WEEK 11: the whole .s file. functions_code is a list of (label, body_lines)
    in source order. A one-function program renders exactly as in Week 9.
    """
    lines = []
    data = global_data_lines(global_symbol_table) + context.data_lines
    if data:
        lines.append(".data")
        lines.extend(data)
    lines.append(".text")
    lines.append(".globl main")
    for label, body in functions_code:
        lines.append(f"{label}:")
        lines.extend(f"    {line}" for line in body)
    return "\n".join(lines) + "\n"
