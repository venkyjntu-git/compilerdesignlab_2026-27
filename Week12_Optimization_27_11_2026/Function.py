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
from calling_convention import arg_locations, SAVED_FP_RA_BYTES


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

    def generateTripleTAC(self, first_label=0):
        """
        WEEK 11: first_label continues the label numbering from the previous
        function, so labels are unique in the whole program. Returns the next
        free label number.
        """
        tacgen = TACGenerator(first_label)
        self.tripleTACstmts = tacgen.generate(self)
        return tacgen.label_counter

    def renderTripleTAC(self):
        return self.tripleTACstmts.render()

    def layoutFrame(self):
        """
        WEEK 11: assigns every local and parameter its offset from $fp, and
        returns the frame size. See docs/activation_records.md for the picture.

            frame_size + 8 + k   stack arguments (passed by the caller; k = offset
                                 in the stack argument area)
            frame_size + 4       saved $ra
            frame_size + 0       saved $fp
            ...                  register parameters, homed from $a0-$a3
            0 .. locals size     local variables         <- $fp (= $sp)
        """
        self.localSymbolTable.assignOffsetsToSymbols()
        offset = self.localSymbolTable.size()
        locations, _ = arg_locations(self.getParamTypes())
        entries = [self.paramSymbolTable.getSymbol(name) for _, name in self.paramList]
        for entry, (kind, _) in zip(entries, locations):
            if kind == 'reg':
                entry.setOffset(offset)
                offset += self.localSymbolTable.getSizeOfType(entry.getDataType())
        frame_size = offset
        for entry, (kind, where) in zip(entries, locations):
            if kind == 'stack':
                entry.setOffset(frame_size + SAVED_FP_RA_BYTES + where)
        return frame_size

    def compile(self, globalSymbolTable=None, context=None):
        """
        WEEK 7: MIPSGenerator needs the triple list (to resolve a TripleRef's type);
        WEEK 9: ... and the global symbol table;
        WEEK 11: ... and the program-wide ProgramContext (strings, labels).
        mipsCode is now this function's body lines; Program renders the .s file.
        """
        frame_size = self.layoutFrame()
        mips_gen = MIPSGenerator(self, self.tripleTACstmts.triples, globalSymbolTable, context)
        self.mipsCode = mips_gen.generate(self.tripleTACstmts.triples, frame_size)

    def getMipsCode(self):
        return self.mipsCode
