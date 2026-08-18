"""
SymbolTable -- fully implemented.

Declarations write into a SymbolTable during parsing.

WEEK 5 CHANGE : DataType now also lists DOUBLE, CHAR, STRING,
needed so the parser can build SymbolTableEntry objects for Level 2
declarations.  
"""

from enum import Enum

DataType = Enum('DataType', ['INT', 'DOUBLE', 'CHAR', 'STRING'])


class SymbolTableEntry:
    def __init__(self, name, datatype):
        self.name = name
        self.datatype = datatype
        self.offset = None

    def getSymbolName(self):
        return self.name

    def getDataType(self):
        return self.datatype

    def getOffset(self):
        return self.offset

    def setOffset(self, offset):
        self.offset = offset

    def print(self):
        print(f"{self.name}: {self.datatype.name}, offset = {self.offset}")


class SymbolTable:
    def __init__(self):
        self.table = []

    def addSymbol(self, symbol):
        self.table.append(symbol)

    def nameInSymbolTable(self, name):
        return any(entry.getSymbolName() == name
                   for entry in self.table)

    def getSymbol(self, name):
        for entry in self.table:
            if entry.getSymbolName() == name:
                return entry
        return None

    def getSizeOfType(self, datatype):
        if datatype == DataType.INT:
            return 4
        elif datatype == DataType.DOUBLE:
            return 8
        elif datatype == DataType.CHAR:
            return 1
        elif datatype == DataType.STRING:
            return 4

    def assignOffsetsToSymbols(self):
        offset = 0
        for entry in self.table:
            entry.setOffset(offset)
            offset += self.getSizeOfType(entry.getDataType())

    def size(self):
        total = 0
        for entry in self.table:
            total += self.getSizeOfType(entry.getDataType())
        return total

    def printSymbolTable(self):
        for entry in self.table:
            entry.print()
