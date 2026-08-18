"""
Function -- mostly fully implemented; compile() is this week's TODO.

Function has:
1. local SymbolTable - contains information about all the local variables used in the function,
   which is mainly populated when declarations are parsed
2. AST list: holds the statement AST list for one function, except declaration statements
3. tripleTACstmts: holds the list of three address code statements in triples form
4. mipsCode: holds the rendered MIPS assembly text for this function, once
   compile() has run -- None until then.

"""
from SymbolTable import SymbolTable
from three_address_code import TripleTAC
from tac_generator import TACGenerator
from tac_to_mips import MIPSGenerator


class Function:
    def __init__(self, returnType, name):
        self.returnType = returnType
        self.name = name
        self.statementsAstList = []
        self.localSymbolTable = SymbolTable()
        self.tripleTACstmts = TripleTAC()
        self.mipsCode = None  

    def setStatementsAstList(self, sastList):
        self.statementsAstList = sastList

    def getStatementsAstList(self):
        return self.statementsAstList

    def addStatement(self, stmt):
        self.statementsAstList.append(stmt)

    def setLocalSymbolTable(self, localList):
        self.localSymbolTable = localList

    def getLocalSymbolTable(self):
        return self.localSymbolTable

    def getReturnType(self):
        return self.returnType

    def getName(self):
        return self.name

    def generateTripleTAC(self):
        tacgen = TACGenerator()
        self.tripleTACstmts = tacgen.generate(self)

    def renderTripleTAC(self):
        return self.tripleTACstmts.render()

    def compile(self):
        """
        TODO(week-4): produce this function's complete MIPS assembly and
        store it in self.mipsCode. Steps, in order:

          1. self.localSymbolTable.assignOffsetsToSymbols()
             -- already-implemented SymbolTable method (see
             SymbolTable.py). Assigns each declared local a real $fp
             offset (0, 4, 8, ... in declaration order) -- this MUST run
             before step 2, since MIPSGenerator needs those offsets to
             emit correct lw/sw instructions.

          2. mips_gen = MIPSGenerator(self.localSymbolTable)
             frame_size = self.localSymbolTable.size()
             self.mipsCode = mips_gen.generate(self.tripleTACstmts.triples, frame_size)
             -- MIPSGenerator.generate() (tac_to_mips.py) is responsible
             for emitting the prologue, walking every triple to produce
             the function body, and emitting the epilogue, then
             returning the fully rendered text.

        Assumes self.tripleTACstmts has already been populated -- i.e.
        generateTripleTAC() has already run. (Program.compile() does NOT
        call generateTripleTAC() for you -- see main.py's write_compile()
        for the required call order: parse -> program.generateTripleTAC()
        -> program.compile().)
        """
        raise NotImplementedError("implement Function.compile()")

    def getMipsCode(self):
        """NEW this week. Returns None if compile() hasn't run yet."""
        return self.mipsCode
