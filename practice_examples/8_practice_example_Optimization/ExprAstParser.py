from sly import Parser
from ExprAstLexer import ExprAstLexer
from ast_nodes import *
from tac_generator import generate_for_program
from cfg import build_cfg, cfg_to_text
from optimizer import optimize
from interpreter import run


class ExprAstParser(Parser):
    """The same language as practice 6: assignments, print, if/else, while, blocks."""
    tokens = ExprAstLexer.tokens

    precedence = (
        ('nonassoc', 'IFX'),
        ('nonassoc', 'ELSE'),
    )

    @_('stmts')
    def P(self, value):
        return Block(value[0])

    @_('stmts S')
    def stmts(self, value):
        return value[0] + [value[1]]

    @_('S')
    def stmts(self, value):
        return [value[0]]

    @_('ID "=" E ";"')
    def S(self, value):
        return Assign(Var(value[0]), value[2])

    @_('PRINT E ";"')
    def S(self, value):
        return Print(value[1])

    @_('IF "(" C ")" S %prec IFX')
    def S(self, value):
        return If(value[2], value[4])

    @_('IF "(" C ")" S ELSE S')
    def S(self, value):
        return If(value[2], value[4], value[6])

    @_('WHILE "(" C ")" S')
    def S(self, value):
        return While(value[2], value[4])

    @_('"{" stmts "}"')
    def S(self, value):
        return Block(value[1])

    @_('E RELOP E')
    def C(self, value):
        return RelOp(value[1], value[0], value[2])

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


lexer = ExprAstLexer()
parser = ExprAstParser()
# x and y are never assigned: think of them as INPUTS whose values are unknown
inp = '''
    a = 4;
    b = a * 2;              // folding + copy propagation: b = 8
    c = x * y;
    unused = c + 1;         // dead: never read
    if (x > b) {
        d = x * y;          // x * y is available (in c): reuse
    } else {
        d = 0;
    }
    e = x * y;              // available on BOTH paths: reuse
    x = x + 1;
    f = x * y;              // x changed: NOT available, recompute
    print d + e + f + b;
'''
result = parser.parse(lexer.tokenize(inp))
triples = generate_for_program(result).triples
print("---- CFG")
print(cfg_to_text(build_cfg(triples)))
print()

# keep an untouched copy of the original program, to compare with afterwards
original = generate_for_program(parser.parse(lexer.tokenize(inp))).triples
optimized = optimize(triples)

print("\n==== Same output before and after?  (the one rule every optimization must keep)")
for inputs in ({'x': 3, 'y': 5}, {'x': 20, 'y': 2}):
    before, after = run(original, inputs), run(optimized, inputs)
    print(f"    inputs {inputs}:  before {before}  after {after}  "
          f"{'same' if before == after else 'DIFFERENT -- the optimizer is wrong!'}")
print(f"    triples: {len(original)} before, {len(optimized)} after")
