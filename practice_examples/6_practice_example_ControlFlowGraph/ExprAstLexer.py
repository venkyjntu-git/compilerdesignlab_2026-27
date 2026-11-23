from sly import Lexer


class ExprAstLexer(Lexer):
    literals = {'+', '-', '*', '/', '=', '(', ')', '{', '}', ';'}
    tokens = {NUMBER, ID, RELOP, IF, ELSE, WHILE, PRINT}

    ignore = ' \t\n'
    ignore_comment = r'//.*'

    # one token for all six comparisons; its value says which one
    RELOP = r'<=|>=|==|!=|<|>'

    keywords = {'if': 'IF', 'else': 'ELSE', 'while': 'WHILE', 'print': 'PRINT'}

    @_(r'[A-Za-z_][A-Za-z0-9_]*')
    def ID(self, t):
        t.type = self.keywords.get(t.value, 'ID')   # keyword or identifier
        return t

    @_(r'[0-9]+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t


# to test the lexer on its own:
# for token in ExprAstLexer().tokenize('while (i <= n) { s = s + i; }'):
#     print(token.type, token.value)
