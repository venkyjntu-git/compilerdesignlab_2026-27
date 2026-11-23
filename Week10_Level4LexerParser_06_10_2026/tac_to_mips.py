"""
Three-Address Code (triples) to MIPS generator -- Levels 1-3.

REFERENCE IMPLEMENTATION, fully complete through Level 3.

WEEK 9 CHANGES:
  1. Control flow: LabelTriple -> `L0:`, GotoTriple -> `j L0`,
     IfFalseTriple -> `beq reg, $zero, L0` (int/char condition) or
     `c.eq.d reg, zero` + `bc1t L0` (double condition).
  2. Globals: a global lives in .data under the label g_<name>, and is
     read/written with `lw/sw/l.d/s.d reg, g_<name>` instead of an
     offset($fp). The g_ prefix keeps a TinyCStr name like `b` or `j`
     from colliding with a MIPS mnemonic used as a label.
  3. Labels inside the MIPS code for RelOp/Select start numbering AFTER
     the 3AC's own labels, so the two never collide.
  4. Register freeing: a register is freed by whichever triple CONSUMES
     it -- also when it was reached through a TripleRef. Week 7 freed
     only freshly-loaded registers, so every TripleRef leaked one
     register; one 6-term expression (tests/test_regpressure.tc) was
     enough to exhaust $t0-$t9. Because AST-generated 3AC uses every
     triple's result exactly once, freeing on consumption is safe, and
     it means NO temporary is live at the end of any statement -- in
     particular, none is live at any label.
"""
from SymbolTable import DataType
from three_address_code import (
    BinOpTriple, RelOpTriple, CastTriple, SelectTriple, AssignTriple, PrintTriple,
    LabelTriple, GotoTriple, IfFalseTriple,
    TripleRef,
)

INT_OP = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div'}
DBL_OP = {'+': 'add.d', '-': 'sub.d', '*': 'mul.d', '/': 'div.d'}
INT_BRANCH_TRUE = {'<': 'blt', '>': 'bgt', '<=': 'ble', '>=': 'bge', '==': 'beq', '!=': 'bne'}


def literal_kind(operand):
    """Returns 'int' / 'double' / 'char' / 'string' for a literal operand, else None."""
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
    """DataType of a value-producing triple's result (for resolving a TripleRef)."""
    if isinstance(triple, BinOpTriple):
        return triple.result_type
    if isinstance(triple, RelOpTriple):
        return DataType.INT
    if isinstance(triple, CastTriple):
        return triple.target_type
    if isinstance(triple, SelectTriple):
        return triple.result_type
    raise ValueError(f"triple has no referenceable result: {type(triple)}")


class MIPSGenerator:
    def __init__(self, symbol_table, triples, global_symbol_table=None):
        self.symbol_table = symbol_table
        self.global_symbol_table = global_symbol_table
        self.triples = triples
        self.int_avail = [True] * 10
        self.float_avail = [True] * 16  # $f0,$f2,...,$f30
        self.int_index_to_reg = {}
        self.float_index_to_reg = {}
        self.text_lines = []
        self.data_lines = []
        self.string_labels = {}
        # WEEK 9: the 3AC already uses L0..L(n-1); MIPS-internal labels continue from Ln.
        self.label_counter = sum(isinstance(t, LabelTriple) for t in triples)

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
    # Variables: local (stack frame) or global (.data) -- WEEK 9
    # ------------------------------------------------------------------
    def lookup(self, name):
        """Local first, then global -- the same rule as type_checker.lookup()."""
        entry = self.symbol_table.getSymbol(name)
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
        op_type. Returns (reg, was_fresh); since Week 9 the CONSUMER frees
        reg either way (see the module docstring, change 4).
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
        # WEEK 9 -- control flow
        elif isinstance(triple, LabelTriple):
            self.gen_label(triple)
        elif isinstance(triple, GotoTriple):
            self.gen_goto(triple)
        elif isinstance(triple, IfFalseTriple):
            self.gen_iffalse(triple)
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
            # same register family: the source register simply BECOMES the result
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

        # Both branch values were computed BEFORE this triple (they are earlier
        # triples / plain operands), so they are freed here once copied into dest.
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

    # ------------------------------------------------------------------
    # LEVEL 3 -- control flow (Week 9)
    # ------------------------------------------------------------------
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
            self.emit(f"bc1t {triple.label}")    # cond == 0.0  ->  false  ->  jump
            self.free_float(zero)
        else:
            self.emit(f"beq {reg}, $zero, {triple.label}")
        self.free_reg(reg, triple.cond_type)

    # ------------------------------------------------------------------
    # Prologue / epilogue / rendering
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

    def global_data_lines(self):
        """WEEK 9: one zero-initialized .data slot per global, doubles 8-byte aligned."""
        lines = []
        if self.global_symbol_table is None:
            return lines
        for entry in self.global_symbol_table.table:
            name = f"g_{entry.getSymbolName()}"
            if entry.getDataType() == DataType.DOUBLE:
                lines.append(".align 3")
                lines.append(f"{name}: .double 0.0")
            else:
                lines.append(f"{name}: .word 0")
        return lines

    def generate(self, triples, frame_size):
        self.emit_prologue(frame_size)
        for triple in triples:
            self.gen_instr(triple)
        self.emit_epilogue(frame_size)
        return self.render()

    def render(self):
        lines = []
        data = self.global_data_lines() + self.data_lines
        if data:
            lines.append(".data")
            lines.extend(data)
        lines.append(".text")
        lines.append(".globl main")
        lines.append("main:")
        lines.extend(f"    {line}" for line in self.text_lines)
        return "\n".join(lines) + "\n"
