"""
Three-Address Code (triples) to MIPS generator.

Read docs/register_allocation_reference.md and
docs/mips_spim_reference.md before editing this file.

This builds directly on the approach shown in
practice_examples/5_practice_examples_MIPS/tac_to_mips.py (Lab Practice
5 -- "Generating MIPS Assembly from Three-Address Code"), with three
real differences from that practice version, all TODOs this week:

  1. REAL addresses, not a placeholder. The practice example's load()/
     store() wrote a placeholder string, "disp($fp)of<name>" -- its own
     README calls this out explicitly as "a teaching placeholder, not
     actual MIPS assembly syntax" (see its section 6 and its "Home Work
     Extension", section 10). This week, SymbolTable.assignOffsetsToSymbols()
     (already implemented -- see SymbolTable.py) has already computed a
     real integer $fp offset for every declared variable, so load()/
     store() here must emit real addressing, e.g. "4($fp)", not the
     placeholder text.

  2. A real prologue/epilogue wraps the whole function, per the
     Frame-based Linkage Convention
     (https://chortle.ccsu.edu/AssemblyTutorial/Chapter-28/ass28_06.html).
     The practice example had no function/frame concept at all -- it
     just ended with a plain exit syscall. This week, MIPSGenerator.generate()
     wraps the triple-by-triple body with emit_prologue()/emit_epilogue()
     instead, and the function ends in `jr $ra` -- no explicit exit
     syscall needed (SPIM's own startup code handles program exit once
     `main` returns; verified directly on real SPIM, not assumed).

Register allocation strategy (unchanged from the practice example -- see
its README sections 2-4, 8-9, and docs/register_allocation_reference.md
here for the same explanation applied to TinyCStr specifically): ten
scratch registers $t0-$t9, allocated on demand, freed when no longer
needed. A triple's result stays live in whatever register it was
computed into (tracked in triple_index_to_reg) until something else
consumes it -- so a later triple referencing an earlier one via
TripleRef does NOT reload from memory, it just reuses that register
directly. This is intentionally simple, not a production register
allocator -- see docs/register_allocation_reference.md for a known
limitation (a TripleRef's register isn't always freed the moment it's
last used) and why it doesn't cause problems for Level 1's programs.
"""
from three_address_code import BinOpTriple, AssignTriple, PrintTriple, TripleRef, is_literal

MIPS_OP = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',   # SPIM pseudo-instruction: 3-operand mul $d,$s,$t
    '/': 'div',   # SPIM pseudo-instruction: 3-operand div $d,$s,$t
}


class MIPSGenerator:
    def __init__(self, symbol_table):
        """
        symbol_table: the function's SymbolTable, with offsets already
        assigned by assignOffsetsToSymbols() -- Function.compile() must
        call that BEFORE constructing MIPSGenerator.
        """
        self.symbol_table = symbol_table
        self.mips_lines = []
        # Simple register allocation -- $t0-$t9 all available initially.
        self.availability_registers = [True] * 10
        self.triple_index_to_reg = {}

    def allocate_registers(self):
        """Provided. Allocates the first free $tN register."""
        try:
            freeregidx = self.availability_registers.index(True)
            self.availability_registers[freeregidx] = False
            return "$t" + str(freeregidx)
        except ValueError:
            raise RuntimeError("Registers are not available")

    def deallocate_register(self, reg):
        """Provided. Marks a $tN register free again."""
        extract_idx = int(reg[2])
        self.availability_registers[extract_idx] = True

    def addMIPS(self, line):
        """Provided. Appends one line of MIPS assembly."""
        self.mips_lines.append(line)

    def resolve_address(self, name):
        """
        TODO(week-4): `name` is a real declared variable's name (a
        string) -- NOT a literal, NOT a TripleRef (callers only pass
        this a variable name). Look it up in self.symbol_table and
        return the MIPS address string for it, e.g. "4($fp)".

        Use self.symbol_table.getSymbol(name).getOffset() to get the
        integer offset, then format it as f"{offset}($fp)".
        """
        raise NotImplementedError("implement MIPSGenerator.resolve_address()")

    def load(self, operand, reg):
        """
        TODO(week-4): emit ONE instruction that gets `operand`'s value
        into `reg`.
          - If is_literal(operand) is True: emit `li reg, operand`
          - Otherwise (operand is a variable name string):
                emit `lw reg, {self.resolve_address(operand)}`

        Note: this is only ever called with a literal or a variable
        name -- TripleRef operands are handled separately in gen_instr()
        by reusing the already-live register from triple_index_to_reg,
        never by loading from memory.
        """
        raise NotImplementedError("implement MIPSGenerator.load()")

    def store(self, reg, name):
        """
        TODO(week-4): emit `sw reg, {self.resolve_address(name)}`, then
        deallocate_register(reg) -- once a value has been written back
        to a variable's slot, the register holding it is free to reuse.
        """
        raise NotImplementedError("implement MIPSGenerator.store()")

    def gen_instr(self, triple):
        """
        TODO(week-4): dispatch on the triple's type and emit MIPS.

          isinstance(triple, BinOpTriple):
              For EACH of arg1, arg2:
                - if isinstance(arg, TripleRef): reuse
                  self.triple_index_to_reg[arg.index] directly (no new
                  register, no load -- the value is already sitting in
                  that register from when that earlier triple ran)
                - else: allocate_registers(), then load(arg, that_reg)
              dest = self.allocate_registers()
              self.addMIPS(f"{MIPS_OP[triple.op]} {dest}, {src1}, {src2}")
              self.triple_index_to_reg[triple.index] = dest
              Then deallocate src1/src2 IF they were freshly allocated
              this call (i.e. NOT a TripleRef reuse) -- a register still
              recorded in triple_index_to_reg as another triple's live
              result must not be freed here.

          isinstance(triple, AssignTriple):
              Resolve triple.arg1 the same way (TripleRef -> reuse;
              else -> allocate + load), then store(that_reg, triple.dest).

          isinstance(triple, PrintTriple):
              Resolve triple.arg1 the same way into some reg, then:
                self.addMIPS(f"move $a0, {reg}")
                self.addMIPS("li $v0, 1")
                self.addMIPS("syscall")
              and deallocate reg if it was freshly allocated (not a
              TripleRef reuse).

        See docs/register_allocation_reference.md for a fully worked
        example of this dispatch on a small triple program, including
        exactly which registers get allocated/reused/freed at each step.
        """
        raise NotImplementedError("implement MIPSGenerator.gen_instr()")

    # ------------------------------------------------------------------
    # Prologue / epilogue -- PROVIDED, not a TODO. Exact sequence from
    # the Frame-based Linkage Convention; see docs/mips_spim_reference.md.
    # ------------------------------------------------------------------
    def emit_prologue(self, frame_size):
        self.addMIPS("subu $sp, $sp, 4")
        self.addMIPS("sw   $ra, 0($sp)")
        self.addMIPS("subu $sp, $sp, 4")
        self.addMIPS("sw   $fp, 0($sp)")
        self.addMIPS(f"addiu $fp, $sp, -{frame_size}")
        self.addMIPS("move $sp, $fp")

    def emit_epilogue(self, frame_size):
        self.addMIPS(f"addiu $sp, $fp, {frame_size}")
        self.addMIPS("lw    $fp, 0($sp)")
        self.addMIPS("addiu $sp, $sp, 4")
        self.addMIPS("lw    $ra, 0($sp)")
        self.addMIPS("addiu $sp, $sp, 4")
        self.addMIPS("jr    $ra")

    def generate(self, triples, frame_size):
        """
        Provided. Emits the prologue, the body (one gen_instr() call per
        triple, in order), then the epilogue, and renders the final .s
        text. You should not need to change this method.

        frame_size: total bytes to reserve for this function's declared
        locals -- pass self.symbol_table.size() (already-implemented
        SymbolTable method). Note this is ONLY the locals' size now, not
        locals-plus-temporaries -- triple results live in registers this
        week, not in their own stack slots, so there's nothing extra to
        reserve for them.
        """
        self.emit_prologue(frame_size)
        for triple in triples:
            self.gen_instr(triple)
        self.emit_epilogue(frame_size)
        return self.render()

    def render(self):
        """Provided. Assembles the final .text section."""
        lines = [".text", ".globl main", "main:"]
        lines.extend(f"    {line}" for line in self.mips_lines)
        return "\n".join(lines) + "\n"
