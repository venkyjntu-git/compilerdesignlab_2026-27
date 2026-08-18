"""
Three-Address Code (triples) to MIPS generator.

Provided in Week 5. You should not need to change this file.
-- Works only for Level1.
"""
from three_address_code import BinOpTriple, AssignTriple, PrintTriple, TripleRef, is_literal

MIPS_OP = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',   
    '/': 'div',   # SPIM pseudo-instruction: 3-operand div $d,$s,$t
}


class MIPSGenerator:
    def __init__(self, symbol_table):
        """
        symbol_table: the function's SymbolTable, with offsets already
        assigned by assignOffsetsToSymbols() in Function.compile() must
        call that BEFORE constructing MIPSGenerator.
        """
        self.symbol_table = symbol_table
        self.mips_lines = []
        # Simple register allocation -- $t0-$t9 all available initially.
        self.availability_registers = [True] * 10
        self.triple_index_to_reg = {}

    def allocate_registers(self):
        """Allocates the first free $tN register."""
        try:
            freeregidx = self.availability_registers.index(True)
            self.availability_registers[freeregidx] = False
            return "$t" + str(freeregidx)
        except ValueError:
            raise RuntimeError("Registers are not available")

    def deallocate_register(self, reg):
        """Marks a $tN register free again."""
        extract_idx = int(reg[2])
        self.availability_registers[extract_idx] = True

    def addMIPS(self, line):
        """Appends one line of MIPS assembly."""
        self.mips_lines.append(line)

    def resolve_address(self, name):
        return f"{self.symbol_table.getSymbol(name).getOffset()}($fp)"

    def load(self, operand, reg):
        if is_literal(operand):
            self.addMIPS(f"li {reg}, {operand}")
        else:
            self.addMIPS(f"lw {reg}, {self.resolve_address(operand)}")

        return reg


    def store(self, reg, name):
        """
        Once a value has been written back to a variable's slot, 
        the register holding it is free to reuse.
        """
        self.addMIPS(f"sw {reg}, {self.resolve_address(name)}")
        self.deallocate_register(reg)

    def gen_instr(self, triple):
        if isinstance(triple, BinOpTriple):
            src1 = triple.arg1
            src2 = triple.arg2

            if isinstance(src1, TripleRef):
                src1 = self.triple_index_to_reg[src1.index]
            else:
                src1 = self.load(src1, self.allocate_registers())

            if isinstance(src2, TripleRef):
                src2 = self.triple_index_to_reg[src2.index]
            else:
                src2 = self.load(src2, self.allocate_registers())

            dest = self.allocate_registers()
            self.addMIPS(f"{MIPS_OP[triple.op]} {dest}, {src1}, {src2}")
            self.triple_index_to_reg[triple.index] = dest
            self.deallocate_register(src1)
            self.deallocate_register(src2)

        elif isinstance(triple, AssignTriple):
            if isinstance(triple.arg1, TripleRef):
                triple.arg1 = self.triple_index_to_reg[triple.arg1.index]
            else:
                triple.arg1 = self.load(triple.arg1, self.allocate_registers())

            self.store(triple.arg1, triple.dest)

        elif isinstance(triple, PrintTriple):
            if isinstance(triple.arg1, TripleRef):
                triple.arg1 = self.triple_index_to_reg[triple.arg1.index]
            else:
                triple.arg1 = self.load(triple.arg1, self.allocate_registers())

            self.addMIPS(f"move $a0, {triple.arg1}")
            self.addMIPS("li $v0, 1")
            self.addMIPS("syscall")
            self.deallocate_register(triple.arg1)
        

    # ------------------------------------------------------------------
    # Prologue / epilogue -- PROVIDED, Exact sequence from
    # the Frame-based Linkage Convention; see
    # https://chortle.ccsu.edu/AssemblyTutorial/Chapter-28/ass28_06.html
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
        SymbolTable method). Note this is ONLY the locals' size now.
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
