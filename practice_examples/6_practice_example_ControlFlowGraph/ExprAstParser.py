from sly import Parser
from ExprAstLexer import ExprAstLexer
from ast_nodes import *
from tac_generator import generate_for_program
from cfg import find_leaders, build_cfg, cfg_to_text, cfg_to_dot


class ExprAstParser(Parser):
    tokens = ExprAstLexer.tokens

    # dangling else: an else belongs to the NEAREST if (see Week 8)
    precedence = (
        ('nonassoc', 'IFX'),
        ('nonassoc', 'ELSE'),
    )

    # P -> S_list                   (the whole program is one block)
    @_('stmts')
    def P(self, value):
        return Block(value[0])

    @_('stmts S')
    def stmts(self, value):
        return value[0] + [value[1]]

    @_('S')
    def stmts(self, value):
        return [value[0]]

    # S -> id = E ;
    @_('ID "=" E ";"')
    def S(self, value):
        return Assign(Var(value[0]), value[2])

    # S -> print E ;
    @_('PRINT E ";"')
    def S(self, value):
        return Print(value[1])

    # S -> if ( C ) S
    @_('IF "(" C ")" S %prec IFX')
    def S(self, value):
        return If(value[2], value[4])

    # S -> if ( C ) S else S
    @_('IF "(" C ")" S ELSE S')
    def S(self, value):
        return If(value[2], value[4], value[6])

    # S -> while ( C ) S
    @_('WHILE "(" C ")" S')
    def S(self, value):
        return While(value[2], value[4])

    # S -> { S_list }
    @_('"{" stmts "}"')
    def S(self, value):
        return Block(value[1])

    # C -> E relop E
    @_('E RELOP E')
    def C(self, value):
        return RelOp(value[1], value[0], value[2])

    # E -> E + T | E - T | T
    @_('E "+" T', 'E "-" T')
    def E(self, value):
        return BinOp(value[1], value[0], value[2])

    @_('T')
    def E(self, value):
        return value[0]

    # T -> T * F | T / F | F
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
inp = '''
    n = 10;
    i = 1;
    s = 0;
    while (i <= n) {
        if (i > 5)
            s = s + i;
        i = i + 1;
    }
    print s;
'''
result = parser.parse(lexer.tokenize(inp))
#print(pretty(result))
tripleprogram = generate_for_program(result)
print("---- Three-address code (triples)")
print(tripleprogram.render())
print("\n---- Leaders (triple numbers):", find_leaders(tripleprogram.triples))
blocks = build_cfg(tripleprogram.triples)
print("\n---- Control-flow graph")
print(cfg_to_text(blocks))
cfg_to_dot(blocks)          # writes cfg.dot -- render: dot -Tpng cfg.dot -o cfg.png
