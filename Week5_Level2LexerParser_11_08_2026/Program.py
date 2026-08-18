"""
Program -- fully implemented.

A TinyCStr program is a list of functions
"""
from Function import Function

class Program:
    def __init__(self):
        self.functions = []

    def addFunction(self, function):
        self.functions.append(function)

    def getFunctions(self):
        return self.functions

    def generateTripleTAC(self):
        for function in self.functions:
            function.generateTripleTAC()

    def renderTripleTAC(self):
        for function in self.functions:
            function.renderTripleTAC()

    def compile(self):
        for function in self.functions:
            function.compile()


    
