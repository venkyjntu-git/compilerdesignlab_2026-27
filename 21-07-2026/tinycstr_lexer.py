"""
TinyCStr Level 1 Lexer (Stages 1a -> 1b)

Read docs/token_reference.md and docs/sly_help.md before editing this file.

Fill in the TODOs in order: finish every Stage 1a TODO and get Stage 1b ready.
"""

from sly import Lexer


class TinyCStrLexer(Lexer):
    # ------------------------------------------------------------------
    # Full Stage 1a + 1b token set is declared here
    # ------------------------------------------------------------------
    tokens = {
        INT, ID, INTEGER, PRINT, ASSIGN, SEMICOLON, LBRACE, RBRACE, COMMA,LPAREN, RPAREN,   # Stage 1a
        PLUS, MINUS, TIMES, DIVIDE,REMAINDER,                     # Stage 1b
    }

    # skip spaces between tokens.
    ignore = ' \t'

    # TODO(week-2, stage-1a): ignore // line comments.
    # See docs/sly_help.md ###3 for why this must be an `ignore_`-prefixed
    # string attribute, not a normal token rule.
    # ignore_COMMENT = r'...'

    # TODO(week-2, stage-1a): count newlines into self.lineno.
    # See docs/sly_help.md ###4 for the standard pattern.
    # @_(r'\n+')
    # def ignore_newline(self, t):
    #     ...

    # ------------------------------------------------------------------
    # Stage 1a: keyword table + identifier rule
    # ------------------------------------------------------------------
    # TODO(week-2, stage-1a): fill in the reserved-word(key-word) table.
    keywords = {
        # 'int': 'INT',
        # 'print': 'PRINT',
    }

    # TODO(week-2, stage-1a): implement the ID rule using the
    # match-then-look-up-in-`keywords` method described in
    # docs/sly_help.md #1. Do NOT add separate INT/PRINT string rules.
    #
    # @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    # def ID(self, t):
    #     ...
    #     return t

    # TODO(week-2, stage-1a): INTEGER — one or more decimal digits.
    # INTEGER = r'...'

    # TODO(week-2, stage-1a): single-character punctuation tokens.
    # ASSIGN = r'...'
    # SEMI   = r'...'
    # LBRACE = r'...'
    # RBRACE = r'...'
    # COMMA  = r'...'
    # LPAREN = r'...'
    # RPAREN = r'...'


    # ------------------------------------------------------------------
    # Stage 1b: arithmetic operators and parentheses.
    # Do not start this section until all Stage 1a golden tests pass.
    # ------------------------------------------------------------------
    # TODO(week-2, stage-1b): uncomment and fill in.
    # PLUS   = r'...'
    # MINUS  = r'...'
    # TIMES  = r'...'
    # DIVIDE = r'...'
    # REMAINDER = r'...'
    
    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------
    def error(self, t):
        """
        TODO(week-2, stage-1a): report the illegal character and current
        line number in EXACTLY this format:

            ERROR <character> <lineno>
        Where <character> is the single bad character and <lineno> is the
        current line number.    

        Then advance past the single bad character so lexing continues
        (self.index += 1) rather than stopping at the first error.
        """
        raise NotImplementedError("implement TinyCStrLexer.error()")


if __name__ == '__main__':
    sample = "int main(){\nint a;\na = 5;\nprint a;\n}"
    lexer = TinyCStrLexer()
    for tok in lexer.tokenize(sample):
        print(tok)
