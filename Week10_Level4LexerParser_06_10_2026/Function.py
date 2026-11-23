"""
Function has:
1. local SymbolTable - contains information about all the local variables used in the function
2. AST list: holds the statement AST list for one function, except declaration statements
3. tripleTACstmts: holds the list of three address code statements in triples form
4. mipsCode: holds the rendered MIPS assembly text for this function, once compile() has run.

WEEK 10 CHANGES (flagged):
5. paramList: the parameters exactly as written, a list of (DataType, name)
   pairs -- name is None when the source left it out, e.g. `int f(int)`.
   That is legal in a PROTOTYPE but an error in a DEFINITION; the type
   checker (not the parser) reports it, so this list must keep the gaps.
6. paramSymbolTable: one SymbolTableEntry per NAMED parameter. Name lookup
   inside the function body is: locals, then parameters, then globals.
7. lineno: the line of the function's header, for error messages.
"""
from SymbolTable import SymbolTable, SymbolTableEntry
from three_address_code import TripleTAC
from tac_generator import TACGenerator
from tac_to_mips import MIPSGenerator


class Function:
    def __init__(self, returnType, name, params=None, lineno=None):
        self.returnType = returnType
        self.name = name
        self.statementsAstList = []
        self.localSymbolTable = SymbolTable()
        self.tripleTACstmts = TripleTAC()
        self.mipsCode = None
        # WEEK 10
        self.paramList = list(params or [])
        self.paramSymbolTable = SymbolTable()
        for datatype, pname in self.paramList:
            if pname is not None:
                self.paramSymbolTable.addSymbol(SymbolTableEntry(pname, datatype))
        self.lineno = lineno

    # WEEK 10 -----------------------------------------------------------
    def getParamList(self):
        return self.paramList

    def getParamTypes(self):
        return [datatype for datatype, _ in self.paramList]

    def getParamSymbolTable(self):
        return self.paramSymbolTable

    def getLineno(self):
        return self.lineno
    # ------------------------------------------------------------------

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

    def compile(self, globalSymbolTable=None):
        self.localSymbolTable.assignOffsetsToSymbols()
        # WEEK 7: MIPSGenerator also needs the full triple list, to resolve a
        # TripleRef operand's TYPE (via triple_result_type()).
        # WEEK 9: ... and the program's GLOBAL symbol table, since a name that
        # isn't local now lives in .data instead of the stack frame.
        mips_gen = MIPSGenerator(self.localSymbolTable, self.tripleTACstmts.triples,
                                 globalSymbolTable)
        frame_size = self.localSymbolTable.size()
        self.mipsCode = mips_gen.generate(self.tripleTACstmts.triples, frame_size)

    def getMipsCode(self):
        return self.mipsCode
