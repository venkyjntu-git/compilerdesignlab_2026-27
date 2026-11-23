"""
Three-Address Code (triples) to MIPS generator -- Level 2 (mixed types).

REFERENCE IMPLEMENTATION, fully complete through Level 2 (this was
Week 7's exercise, now carried forward as infrastructure). Level 3
control flow (labels/branches for if/while) is Week 9's subject.

WEEK 7: this extends Week 4's single-register-family (integer-only)
generator to handle DOUBLE, CHAR, and STRING alongside INT, and adds
codegen for RelOp/Cast/Ternary (via the RelOpTriple/CastTriple/
SelectTriple triples tac_generator.py now emits).

Two SEPARATE register pools now, tracked independently:
  - Integer: $t0-$t9 (unchanged from Week 4)
  - Floating-point: $f0, $f2, $f4, ..., $f30 -- MIPS's FPU registers are
    used in EVEN-numbered PAIRS to hold one 8-byte double each (the odd
    register of each pair holds the high-order half). This code always
    allocates/frees by the even index, so you never need to think about
    the paired odd register directly -- see docs/mips_fp_reference.md.

Every triple's operand(s) get resolved to the RIGHT pool based on their
TYPE (looked up via resolve_type() / literal_kind(), both provided) --
an int-family value always goes through alloc_int()/the integer
instructions; a double-family value always goes through
alloc_float()/the ".d" instructions.
"""
from SymbolTable import DataType
from three_address_code import (
    BinOpTriple, RelOpTriple, CastTriple, SelectTriple, AssignTriple, PrintTriple,
    TripleRef, is_literal,
)

INT_OP = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div'}
DBL_OP = {'+': 'add.d', '-': 'sub.d', '*': 'mul.d', '/': 'div.d'}

# int comparison -> branch-if-true pseudo-instruction (SPIM provides
# blt/bgt/ble/bge/beq/bne as 3-operand pseudo-ops -- verified directly
# on real SPIM, see docs/mips_fp_reference.md).
INT_BRANCH_TRUE = {'<': 'blt', '>': 'bgt', '<=': 'ble', '>=': 'bge', '==': 'beq', '!=': 'bne'}


def literal_kind(operand):
    """
    Provided. Returns 'int' / 'double' / 'char' / 'string' for a literal
    operand, or None if `operand` is a variable name instead. String and
    char literals are recognizable because tac_generator.py's Const
    handling wraps them in their original quote characters
    ('"hello"' / "'x'") specifically so this function can tell them
    apart from a bare variable name by inspection -- see
    docs/typed_3ac_reference.md.
    """
    if not isinstance(operand, str):
        return None
    if operand.startswith('"') and operand.endswith('"'):
        return 'string'
    if operand.startswith("'") and operand.endswith("'"):
        return 'char'
    if operand.isdigit():
        return 'int'
    if operand.count('.') == 1:
        a, b = operand.split('.')
        if a.isdigit() and b.isdigit():
            return 'double'
    return None


def triple_result_type(triple):
    """
    Provided. Returns the DataType a given (already-generated) triple's
    result has, for resolving a TripleRef operand's type. Only triples
    that PRODUCE a referenceable value need a case here (AssignTriple/
    PrintTriple never do -- nothing ever builds a TripleRef to one).
    """
    if isinstance(triple, BinOpTriple):
        return triple.result_type
    if isinstance(triple, RelOpTriple):
        return DataType.INT  # a comparison's own value is always INT 0/1
    if isinstance(triple, CastTriple):
        return triple.target_type
    if isinstance(triple, SelectTriple):
        return triple.result_type
    raise ValueError(f"triple has no referenceable result: {type(triple)}")


class MIPSGenerator:
    def __init__(self, symbol_table, triples):
        self.symbol_table = symbol_table
        self.triples = triples  # needed to resolve a TripleRef operand's type
        self.int_avail = [True] * 10
        self.float_avail = [True] * 16  # represents $f0,$f2,...,$f30
        self.int_index_to_reg = {}
        self.float_index_to_reg = {}
        self.text_lines = []
        self.data_lines = []
        self.string_labels = {}
        self.label_counter = 0

    # ------------------------------------------------------------------
    # Register allocation, labels, string data -- PROVIDED
    # ------------------------------------------------------------------
    def alloc_int(self):
        i = self.int_avail.index(True)
        self.int_avail[i] = False
        return f"$t{i}"

    def free_int(self, reg):
        i = int(reg[2:])
        self.int_avail[i] = True

    def alloc_float(self):
        i = self.float_avail.index(True)
        self.float_avail[i] = False
        return f"$f{i * 2}"

    def free_float(self, reg):
        i = int(reg[2:]) // 2
        self.float_avail[i] = True

    def new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def get_string_label(self, text):
        """Deduplicates identical string literals to one .data entry each."""
        if text in self.string_labels:
            return self.string_labels[text]
        label = f"Lstr{len(self.string_labels)}"
        self.string_labels[text] = label
        self.data_lines.append(f'{label}: .asciiz "{text}"')
        return label

    def emit(self, line):
        self.text_lines.append(line)

    def is_double_family(self, t):
        return t == DataType.DOUBLE

    def free_reg(self, reg, op_type):
        """Frees `reg` from whichever pool matches op_type."""
        if self.is_double_family(op_type):
            self.free_float(reg)
        else:
            self.free_int(reg)

    # ------------------------------------------------------------------
    # Type resolution -- PROVIDED
    # ------------------------------------------------------------------
    def resolve_type(self, operand):
        """
        Returns the DataType of ANY operand (literal, variable name, or
        TripleRef). Used by gen_print() and by load()'s callers that
        don't already know the type from context.
        """
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
        entry = self.symbol_table.getSymbol(operand)
        return entry.getDataType()

    # ------------------------------------------------------------------
    # Loading/storing operands
    # ------------------------------------------------------------------
    def load(self, operand, op_type):
        """
        Gets `operand`'s value into a register of the family matching
        op_type and returns (reg, was_fresh). was_fresh is False only for
        a reused TripleRef register (the caller must not free it).
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
            label = self.get_string_label(operand[1:-1])
            self.emit(f"la {reg}, {label}")
        else:
            offset = self.symbol_table.getSymbol(operand).getOffset()
            if self.is_double_family(op_type):
                reg = self.alloc_float()
                self.emit(f"l.d {reg}, {offset}($fp)")
            else:
                reg = self.alloc_int()
                self.emit(f"lw {reg}, {offset}($fp)")
        return reg, True

    def store_to_var(self, reg, name, reg_type):
        offset = self.symbol_table.getSymbol(name).getOffset()
        if self.is_double_family(reg_type):
            self.emit(f"s.d {reg}, {offset}($fp)")
        else:
            self.emit(f"sw {reg}, {offset}($fp)")

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
        else:
            raise ValueError(f"unexpected triple type: {type(triple)}")

    def record(self, triple, reg, reg_type):
        """Remembers which register holds `triple`'s result."""
        if self.is_double_family(reg_type):
            self.float_index_to_reg[triple.index] = reg
        else:
            self.int_index_to_reg[triple.index] = reg

    def gen_binop(self, triple):
        t = triple.result_type
        r1, fresh1 = self.load(triple.arg1, t)
        r2, fresh2 = self.load(triple.arg2, t)
        if self.is_double_family(t):
            dest = self.alloc_float()
            self.emit(f"{DBL_OP[triple.op]} {dest}, {r1}, {r2}")
        else:
            dest = self.alloc_int()
            self.emit(f"{INT_OP[triple.op]} {dest}, {r1}, {r2}")
        self.record(triple, dest, t)
        if fresh1:
            self.free_reg(r1, t)
        if fresh2:
            self.free_reg(r2, t)

    def gen_relop(self, triple):
        t = triple.operand_type
        r1, fresh1 = self.load(triple.arg1, t)
        r2, fresh2 = self.load(triple.arg2, t)
        dest = self.alloc_int()
        l_true = self.new_label()
        l_end = self.new_label()
        if self.is_double_family(t):
            op = triple.op
            if op == '<':
                self.emit(f"c.lt.d {r1}, {r2}")
                self.emit(f"bc1t {l_true}")
            elif op == '<=':
                self.emit(f"c.le.d {r1}, {r2}")
                self.emit(f"bc1t {l_true}")
            elif op == '==':
                self.emit(f"c.eq.d {r1}, {r2}")
                self.emit(f"bc1t {l_true}")
            elif op == '>':
                self.emit(f"c.lt.d {r2}, {r1}")
                self.emit(f"bc1t {l_true}")
            elif op == '>=':
                self.emit(f"c.le.d {r2}, {r1}")
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
        if fresh1:
            self.free_reg(r1, t)
        if fresh2:
            self.free_reg(r2, t)

    def gen_cast(self, triple):
        src_t, dst_t = triple.source_type, triple.target_type
        src, fresh = self.load(triple.arg, src_t)
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
            # same register family: no instruction, the loaded register IS the result
            self.record(triple, src, dst_t)
            return
        self.record(triple, dest, dst_t)
        if fresh:
            self.free_reg(src, src_t)

    def gen_select(self, triple):
        rt = triple.result_type
        dest = self.alloc_float() if self.is_double_family(rt) else self.alloc_int()
        move = "mov.d" if self.is_double_family(rt) else "move"
        l_then = self.new_label()
        l_end = self.new_label()

        cond, cfresh = self.load(triple.cond, triple.cond_type)
        if self.is_double_family(triple.cond_type):
            zero = self.alloc_float()
            self.emit(f"li.d {zero}, 0.0")
            self.emit(f"c.eq.d {cond}, {zero}")
            self.emit(f"bc1f {l_then}")
            self.free_float(zero)
        else:
            self.emit(f"bne {cond}, $zero, {l_then}")
        if cfresh:
            self.free_reg(cond, triple.cond_type)

        reg, fresh = self.load(triple.else_val, rt)
        self.emit(f"{move} {dest}, {reg}")
        if fresh:
            self.free_reg(reg, rt)
        self.emit(f"b {l_end}")

        self.emit(f"{l_then}:")
        reg, fresh = self.load(triple.then_val, rt)
        self.emit(f"{move} {dest}, {reg}")
        if fresh:
            self.free_reg(reg, rt)
        self.emit(f"{l_end}:")
        self.record(triple, dest, rt)

    def gen_assign(self, triple):
        t = self.symbol_table.getSymbol(triple.dest).getDataType()
        reg, _ = self.load(triple.arg1, t)
        self.store_to_var(reg, triple.dest, t)
        self.free_reg(reg, t)  # a store always frees its register

    def gen_print(self, triple):
        t = self.resolve_type(triple.arg1)
        reg, fresh = self.load(triple.arg1, t)
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
        if fresh:
            self.free_reg(reg, t)

    # ------------------------------------------------------------------
    # Prologue / epilogue -- PROVIDED, unchanged from Week 4
    # ------------------------------------------------------------------
    def emit_prologue(self, frame_size):
        self.emit("subu $sp, $sp, 4")
        self.emit("sw   $ra, 0($sp)")
        self.emit("subu $sp, $sp, 4")
        self.emit("sw   $fp, 0($sp)")
        self.emit(f"addiu $fp, $sp, -{frame_size}")
        self.emit("move $sp, $fp")

    def emit_epilogue(self, frame_size):
        self.emit(f"addiu $sp, $fp, {frame_size}")
        self.emit("lw    $fp, 0($sp)")
        self.emit("addiu $sp, $sp, 4")
        self.emit("lw    $ra, 0($sp)")
        self.emit("addiu $sp, $sp, 4")
        self.emit("jr    $ra")

    def generate(self, triples, frame_size):
        """
        Provided. Emits the prologue, the body (one gen_instr() call per
        triple, in order), then the epilogue, and renders the final .s
        text. You should not need to change this method.
        """
        self.emit_prologue(frame_size)
        for triple in triples:
            self.gen_instr(triple)
        self.emit_epilogue(frame_size)
        return self.render()

    def render(self):
        """Provided. Assembles .data (only if string literals were used) + .text."""
        lines = []
        if self.data_lines:
            lines.append(".data")
            lines.extend(self.data_lines)
        lines.append(".text")
        lines.append(".globl main")
        lines.append("main:")
        lines.extend(f"    {line}" for line in self.text_lines)
        return "\n".join(lines) + "\n"


def generate_mips(function, triple_program):
    """
    Convenience wrapper. Assumes assignOffsetsToSymbols() has already
    been called on function.getLocalSymbolTable() -- see Function.compile().
    """
    gen = MIPSGenerator(function.getLocalSymbolTable(), triple_program.triples)
    return gen.generate(triple_program, function.getLocalSymbolTable().size())
