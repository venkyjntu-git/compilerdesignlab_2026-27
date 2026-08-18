"""
Function -- fully implemented; 

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
        self.localSymbolTable.assignOffsetsToSymbols()
        mips_gen = MIPSGenerator(self.localSymbolTable)
        frame_size = self.localSymbolTable.size()
        self.mipsCode = mips_gen.generate(self.tripleTACstmts.triples, frame_size)
        

    def getMipsCode(self):
        """Returns None if compile() hasn't run yet."""
        return self.mipsCode
