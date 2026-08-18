# SLY Level 2 Help (Week 5)

Read this before touching Stage 2a/2b/2c. Builds on Week 2's lexer help and Week 3's
parser help — this only covers what's new this week.

## 1. `REAL_CONST` must be a function-style rule, not a string attribute

```python
@_(r'\d+\.\d+')
def REAL_CONST(self, t):
    t.value = float(t.value)
    return t
```
A plain string attribute (`REAL_CONST = r'\d+\.\d+'`) can only assign a token *type* to a matched pattern — it can't transform the matched *text*. You need the matched `"3.14"` to become an actual Python `float` before it reaches the parser (so `Const(value)` holds a real number, not a string) — that transformation is only possible in a function-style rule.

## 2. Relational operators don't need special ordering care

`<=` and `<` (and `>=`/`>`, `==`/`ASSIGN`, `!=` with nothing shorter to collide with) look like
they might need careful handling so `<=` doesn't get tokenized as `<` then `=`. They don't — as
long as you define them as **plain string attributes** (not functions), SLY's own rule (string
rules tried in order of *decreasing pattern length*) already tries `LE = r'<='` before
`LT = r'<'`, since `'<='` is a longer pattern string than `'<'`. This is the same mechanism that
already made `ignore_COMMENT`/`DIVIDE` and `ASSIGN`/`EQ` work correctly without special-casing
back in Weeks 2 and 4.

## 3. Relational precedence goes *above* arithmetic in the tuple — not below

```python
precedence = (
    ('left', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'),  # <-- new entry, ABOVE the existing ones
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)
```
SLY's `precedence` tuple is low-to-high, entries *later* in the
tuple bind *tighter*. Relational operators less precedence than arithmetic (`a + b < c`
must mean `(a+b) < c`, not `a + (b<c)`), so their entry goes *before* (earlier than) `PLUS`/
`MINUS` — the opposite end of the tuple from where you might first reach for it.

## 4. Ternary goes even further above — and needs to be right-associative

```python
precedence = (
    ('right', 'QUESTION', 'COLON'),                 # <-- lowest of all
    ('left', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)
```
`'right'`, not `'left'` — a chained ternary like `a ? b : c ? d : e` should parse as
`a ? b : (c ? d : e)` (matching C), which needs right-associativity. 

## 5. Casts need `%prec` — a plain precedence entry isn't enough on its own

This is the trickiest part of Week 5. A naive cast rule:
```python
@_('LPAREN DOUBLE RPAREN expr')
def expr(self, p):
    return Cast("double", p.expr)
```
has a problem: the trailing `expr` on the right-hand side is a *full* expression, so without
help, the parser will happily let that trailing `expr` extend as far right as grammar allows —
`(double)a/b` would then parse as `(double)(a/b)` (cast applied to the *whole* division), not
the correct `((double)a)/b` (cast applied to `a` alone, then divided by `b`).

The fix is the same trick classic yacc-family grammars use for unary minus: attach a
**dummy, high-precedence token** to the rule via `%prec`, forcing SLY to prefer reducing
the cast immediately rather than continuing to shift more of the expression into it:
```python
precedence = (
    ('right', 'QUESTION', 'COLON'),
    ('left', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UCAST'),        # <-- dummy token, never actually produced by the lexer
)

@_('LPAREN DOUBLE RPAREN expr %prec UCAST')
def expr(self, p):
    return Cast("double", p.expr)

@_('LPAREN INT RPAREN expr %prec UCAST')
def expr(self, p):
    return Cast("int", p.expr)
```
`UCAST` is never a real token the lexer produces — it exists purely to give this *rule* a
precedence level (the highest one) distinct from any real operator's. `%prec UCAST` at the end
of the rule string tells SLY "resolve any shift/reduce ambiguity for this specific rule as if it
had `UCAST`'s precedence," overriding whatever precedence the rule would otherwise inherit from
its rightmost terminal.


## 6. Quick self-check before you run the golden tests

- [ ] `REAL_CONST` is function-style and converts to `float`.
- [ ] `CHAR_CONST`/`STRING_CONST` are function-style and strip their surrounding quotes.
- [ ] Six relational tokens are plain string attributes, not functions.
- [ ] Relational precedence entry is *above* (less) arithmetic in the tuple.
- [ ] Ternary precedence entry is `'right'` and is the very first entry.
- [ ] Both cast rules end in `%prec UCAST`, and `UCAST` is declared as the *last* (highest)
      precedence entry.
