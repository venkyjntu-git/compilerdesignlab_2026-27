from sly import Lexer
class ExprAstLexer(Lexer):
    literals = {'+', '-', '*', '/', '%', '='}
    tokens   = { NUMBER, ID }

    ID = r'[A-Za-z_][A-Za-z0-9_]*'
    NUMBER = r'[0-9]+'

    def NUMBER(self, t):
        #print(' token is', t.type, t.value)
        t.value = int(t.value)
        return t

#to test run Lexer independently following code used
#inp = '2+3*5'
#lexer = CalcLexer()
# tokenize function which takes input string and returns tokens
#for token in lexer.tokenize(inp):
#    print( token.type, token.value,type(token.value))
