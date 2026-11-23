"""
Program -- fully implemented.

A TinyCStr program is (Slide 3 of the TinyCStr specification):
    optional global declarations, followed by one or more functions,
    one of which must be main.

WEEK 8: a Program owns a GLOBAL SymbolTable, filled by the parser's
`global_decl_list` rule.

WEEK 10 CHANGES (flagged):
  - The global part may now also contain function PROTOTYPES (Slide 7:
    `int add(int,int);`), kept in self.prototypes as FunctionPrototype
    objects. A prototype has a signature but no body.
  - A program has one OR MORE functions (self.functions, in source order).
    "Exactly one of them is main" is a semantic rule, checked by the type
    checker -- the grammar accepts any number >= 1.
"""
from Function import Function
from SymbolTable import SymbolTable


class FunctionPrototype:
    """WEEK 10 -- `int add(int,int);`: return type, name, parameter types, no body."""

    def __init__(self, returnType, name, params, lineno=None):
        self.returnType = returnType
        self.name = name
        self.paramList = list(params)  # (DataType, name-or-None) pairs; names are ignored
        self.lineno = lineno

    def getReturnType(self):
        return self.returnType

    def getName(self):
        return self.name

    def getParamTypes(self):
        return [datatype for datatype, _ in self.paramList]

    def getLineno(self):
        return self.lineno


class Program:
    def __init__(self):
        self.functions = []
        self.globalSymbolTable = SymbolTable()  # WEEK 8
        self.prototypes = []                    # WEEK 10

    def addFunction(self, function):
        self.functions.append(function)

    def getFunctions(self):
        return self.functions

    def getGlobalSymbolTable(self):
        return self.globalSymbolTable

    def setGlobalSymbolTable(self, symtab):
        self.globalSymbolTable = symtab

    # WEEK 10 -----------------------------------------------------------
    def addPrototype(self, prototype):
        self.prototypes.append(prototype)

    def getPrototypes(self):
        return self.prototypes

    def getFunction(self, name):
        """The FIRST definition with this name, or None."""
        for function in self.functions:
            if function.getName() == name:
                return function
        return None
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
