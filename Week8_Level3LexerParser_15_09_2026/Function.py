"""
Function has:
1. local SymbolTable - contains information about all the local variables used in the function
2. AST list: holds the statement AST list for one function, except declaration statements
3. tripleTACstmts: holds the list of three address code statements in triples form
4. mipsCode: holds the rendered MIPS assembly text for this function, once compile() has run.
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
        self.localSymbolTable.assignOffsetsToSymbols()
        # WEEK 7: MIPSGenerator now also needs the full triple list, so it
        # can resolve a TripleRef operand's TYPE (via triple_result_type())
        # when deciding int-family vs double-family instructions -- Week 4's
        # version never needed this since everything was INT.
        mips_gen = MIPSGenerator(self.localSymbolTable, self.tripleTACstmts.triples)
        frame_size = self.localSymbolTable.size()
        self.mipsCode = mips_gen.generate(self.tripleTACstmts.triples, frame_size)

    def getMipsCode(self):
        return self.mipsCode
