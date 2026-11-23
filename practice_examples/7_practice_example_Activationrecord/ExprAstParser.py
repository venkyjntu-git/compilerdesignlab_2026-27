from sly import Parser
from ExprAstLexer import ExprAstLexer
from ast_nodes import *
from tac_generator import generate_for_program
from tac_to_mips import generate_mips, FrameLayout


class ExprAstParser(Parser):
    tokens = ExprAstLexer.tokens

    # P -> functions
    @_('functions')
    def P(self, value):
        return Program(value[0])

    @_('functions function')
    def functions(self, value):
        return value[0] + [value[1]]

    @_('function')
    def functions(self, value):
        return [value[0]]

    # function -> int id ( params ) { stmts }
    @_('INT ID "(" params ")" "{" stmts "}"')
    def function(self, value):
        return Function(value[1], value[3], value[6])

    @_('param_list')
    def params(self, value):
        return value[0]

    @_('')
    def params(self, value):
        return []

    @_('param_list "," INT ID')
    def param_list(self, value):
        return value[0] + [value[3]]

    @_('INT ID')
    def param_list(self, value):
        return [value[1]]

    @_('stmts S')
    def stmts(self, value):
        return value[0] + [value[1]]

    @_('S')
    def stmts(self, value):
        return [value[0]]

    # S -> id = E ;  |  return E ;  |  print E ;
    @_('ID "=" E ";"')
    def S(self, value):
        return Assign(Var(value[0]), value[2])

    @_('RETURN E ";"')
    def S(self, value):
        return Return(value[1])

    @_('PRINT E ";"')
    def S(self, value):
        return Print(value[1])

    # E, T, F as in practice 2 -- plus a call: F -> id ( args )
    @_('E "+" T', 'E "-" T')
    def E(self, value):
        return BinOp(value[1], value[0], value[2])

    @_('T')
    def E(self, value):
        return value[0]

    @_('T "*" F', 'T "/" F')
    def T(self, value):
        return BinOp(value[1], value[0], value[2])

    @_('F')
    def T(self, value):
        return value[0]

    @_('NUMBER')
    def F(self, value):
        return Num(value[0])

    @_('ID')
    def F(self, value):
        return Var(value[0])

    @_('"(" E ")"')
    def F(self, value):
        return value[1]

    @_('ID "(" args ")"')
    def F(self, value):
        return Call(value[0], value[2])

    @_('arg_list')
    def args(self, value):
        return value[0]

    @_('')
    def args(self, value):
        return []

    @_('arg_list "," E')
    def arg_list(self, value):
        return value[0] + [value[2]]

    @_('E')
    def arg_list(self, value):
        return [value[0]]


lexer = ExprAstLexer()
parser = ExprAstParser()
inp = '''
int square(int x) {
    return x * x;
}
int sumOfSquares(int a, int b) {
    s = square(a) + square(b);
    return s;
}
int main() {
    print sumOfSquares(3, 4);
}
'''
result = parser.parse(lexer.tokenize(inp))
#print(pretty(result))
functions_and_triples = generate_for_program(result)
for function, program in functions_and_triples:
    print(f"---- {function.name}: triples")
    print(program.render())
    print(FrameLayout(function).describe(function))
    print()
mipscode = generate_mips(functions_and_triples)
print("---- MIPS")
print(mipscode)
with open("program.s", "w") as f:       # run with:  spim -file program.s
    f.write(mipscode)
