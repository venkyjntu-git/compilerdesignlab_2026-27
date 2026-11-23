from sly import Lexer


class ExprAstLexer(Lexer):
    literals = {'+', '-', '*', '/', '=', '(', ')', '{', '}', ',', ';'}
    tokens = {NUMBER, ID, INT, RETURN, PRINT}

    ignore = ' \t\n'
    ignore_comment = r'//.*'

    keywords = {'int': 'INT', 'return': 'RETURN', 'print': 'PRINT'}

    @_(r'[A-Za-z_][A-Za-z0-9_]*')
    def ID(self, t):
        t.type = self.keywords.get(t.value, 'ID')
        return t

    @_(r'[0-9]+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t
