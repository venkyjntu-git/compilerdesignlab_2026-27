"""
Program -- fully implemented.

A TinyCStr program is (Slide 3 of the TinyCStr specification):
    optional global declarations, followed by one or more functions,
    one of which must be main.

WEEK 8 CHANGE: a Program now also owns a GLOBAL SymbolTable, filled by
the parser's `global_decl_list` rule (Stage 3b). Function bodies keep
their own LOCAL SymbolTable exactly as before; the type checker looks a
name up locally first, then globally (type_checker.py's lookup()).
Level 3 still has exactly one function (main) -- multiple functions
are Level 4 (Week 10).
"""
from Function import Function
from SymbolTable import SymbolTable


class Program:
    def __init__(self):
        self.functions = []
        self.globalSymbolTable = SymbolTable()  # WEEK 8

    def addFunction(self, function):
        self.functions.append(function)

    def getFunctions(self):
        return self.functions

    # WEEK 8 -----------------------------------------------------------
    def getGlobalSymbolTable(self):
        return self.globalSymbolTable

    def setGlobalSymbolTable(self, symtab):
        self.globalSymbolTable = symtab
    # ------------------------------------------------------------------

    def generateTripleTAC(self):
        for function in self.functions:
            function.generateTripleTAC()

    def renderTripleTAC(self):
        for function in self.functions:
            function.renderTripleTAC()

    def compile(self):
        for function in self.functions:
            function.compile(self.globalSymbolTable)  # WEEK 9: globals reach the back end
