# SLY Lexer Help File (Week 2)

Read this before writing `tinycstr_lexer.py`. 

Important points related to sly Lexer:

# 1. Tokens are matched in the same order that patterns(regular expressions) are listed in the Lexer class.
# 2. Longer tokens always need to be specified before short tokens.


### 1. Keyword vs. identifier disambiguation

**Do not** write a separate regex per keyword (e.g. one rule for `int`, another for `print`). If you do, then a keyword regex will often incorrectly match a prefix of a longer identifier.

**Do** write one `ID` rule that matches any identifier, and inside its handler function, look the matched text up in a small reserved-words(key-words) dictionary. If it's a keyword, override the token's `.type`; otherwise leave it as `ID`. Complete (fill in the dictionary and the rest of the class yourself):

```python
class TinyCStrLexer(Lexer):
    ...
    keywords = {
        # 'source text': 'TOKEN_TYPE'
    }

    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def ID(self, t):
        t.type = self.keywords.get(t.value, 'ID')
        return t
```

This is *the* standard method for keyword handling in every lex-style tool (flex, PLY, SLY) — you'll use it again in Week 5 when more keywords (`double`, `char`, `string`) are added.

### 2. Token matching order matters

SLY builds its master regex in this priority:

- Tokens defined as **plain string attributes** (`ASSIGN = r'='`) are tried in order of
  **decreasing regex length** — longest pattern string first.
- Tokens defined as **functions** (`@_(...)  def ID(self, t): ...`) are tried in the order
  they're **written in the class body**, and functions are matched before string-attribute
  tokens regardless of length.


### 3. Ignoring whitespace vs. ignoring comments

Two different mechanisms, don't confuse them:

- `ignore = ' \t'` — a **class attribute holding literal characters** to skip silently. Use
  this for spaces and tabs.
- `ignore_COMMENT = r'//.*'` — a class attribute whose name is prefixed `ignore_`. SLY treats
  this as a *pattern* to match and discard (no token emitted), which is what you want for `//`
  comments. This is different from a normal token rule — do not put `COMMENT` in your `tokens`
  set.

### 4. Line tracking

SLY does not track line numbers for you automatically beyond giving you `self.lineno`, which
starts at 1 and which *you* are responsible for incrementing. The standard pattern is a
function-style rule matching one-or-more newlines that does not return a token:

```python
@_(r'\n+')
def ignore_newline(self, t):
    self.lineno += t.value.count('\n')
```

Naming it with an `ignore_` prefix means it is discarded like a comment — correct, since a
newline should not itself produce a token in this grammar. If you forget this rule entirely,
every token will silently report `lineno=1`, which will make Stage 1b's Example 1 (a 7-line
program) impossible to debug and will break every later week's error messages.

### 5. Custom error handling

Override `error(self, t)`. `t.value` is the *remaining, unconsumed input* starting at the bad
character, not just the one bad character — so the bad character itself is `t.value[0]`. Your
`error()` must:

1. Report the character and `self.lineno` in the exact format specified in
   `docs/pitfalls_faq.md`.
2. Advance past the bad character so lexing can continue (`self.index += 1`), rather than
   raising an exception and stopping — TinyCStr's lexer should report *all* illegal characters
   in a file in one pass, not just the first one.

### 6. Quick self-check before you run the tests

- [ ] Every token type your lexer can emit is listed in the `tokens` set.
- [ ] `ID` is a function-style rule with the keyword-lookup idiom, not a plain string.
- [ ] Operator tokens (`PLUS`, `DIVIDE`, ...) are plain string attributes, not functions.
- [ ] `ignore = ' \t'` is set.
- [ ] `ignore_COMMENT` and a newline-counting rule both exist.
- [ ] `error()` is overridden, advances past the bad character, and matches the required format.
