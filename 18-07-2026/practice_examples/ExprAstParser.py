from sly import Parser
from ExprAstLexer import ExprAstLexer
from ast_nodes import * 

class ExprAstParser(Parser):
    tokens = ExprAstLexer.tokens
    
    # A -> id = E
    @_('ID "=" E')
    def A(self, value):
        return Assign(Var(value[0]), value[2])

    # E -> E + T
    @_('E "+" T')
    def E(self, value):
        return BinOp('+', value[0], value[2])

    # E -> E - T
    @_('E "-" T')
    def E(self, value):
        return BinOp('-', value[0], value[2])

    # E -> T
    @_('T')
    def E(self, value):
        return value[0]

    # T -> T * F
    @_('T "*" F')
    def T(self, value):
        return BinOp('*', value[0], value[2])

    # T -> T / F
    @_('T "/" F')
    def T(self, value):
        return BinOp('/', value[0], value[2])

    # T -> T % F
    @_('T "%" F')
    def T(self, value):
        return BinOp('%', value[0], value[2])

    # T -> F
    @_('F')
    def T(self, value):
        return value[0]

    # F-> NUMBER
    @_('NUMBER')
    def F(self, value):
        return Num(value[0])

    # F-> ID
    @_('ID')
    def F(self, value):
        return Var(value[0])


lexer = ExprAstLexer()
parser = ExprAstParser()
inp = 'a=2+3*5'
result = parser.parse(lexer.tokenize(inp))
print(pretty(result))
to_dot(result)
#print(result)


