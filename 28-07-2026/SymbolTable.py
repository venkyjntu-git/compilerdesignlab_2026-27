"""
SymbolTable -- fully implemented.

Week 3's learning objective is the PARSER (grammar rules, precedence,
AST construction) -- not re-deriving this bookkeeping. Declarations
write into a SymbolTable during parsing but produce no AST node.

"""
from enum import Enum

DataType = Enum('DataType', ['INT'])


class SymbolTableEntry:
    def __init__(self, name, datatype):
        self.name = name
        self.datatype = datatype

    def getSymbolName(self):
        return self.name

    def getDataType(self):
        return self.datatype

    def print(self):
        print(f"{self.name}: {self.datatype.name}")


class SymbolTable:
    def __init__(self):
        self.table = []

    def addSymbol(self, symbol):
        """
        symbol: a SymbolTableEntry. Appends unconditionally -- this does
        NOT check for redeclaration. Detecting a name declared twice in
        the same scope is a semantic-analysis concern (Week 6), not a
        parser concern; the parser's job this week is just to record
        what it sees.
        """
        self.table.append(symbol)

    def nameInSymbolTable(self, name):
        return any(entry.getSymbolName() == name for entry in self.table)

    def getSymbol(self, name):
        for entry in self.table:
            if entry.getSymbolName() == name:
                return entry
        return None

    def printSymbolTable(self):
        for entry in self.table:
            entry.print()
