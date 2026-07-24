# SLY Parser Help file (Week 3)

Read this before touching `tinycstr_parser.py`. 

## 1. The precedence tuple's order is low-to-high, not high-to-low

```python
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)
```

Entries **later in the tuple bind tighter**. Most people's first instinct is to write the
"more important" operator first — that's backwards. `TIMES`/`DIVIDE` are listed *after*
`PLUS`/`MINUS` specifically because they need *higher* precedence (bind tighter). If you get
this backwards, `2 + 3 * 4` will parse as `(2 + 3) * 4` instead of `2 + (3 * 4)`, and it will
look like it "mostly works" until a program actually depends on precedence 

`'left'` vs `'right'` in each tuple entry sets associativity for operators at that level. All
four Level 1 operators are left-associative.

## 2. Why left-recursion gives left-associativity "for free"

```
expr : expr PLUS expr
```

is ambiguous on its own (SLY needs the `precedence` table to resolve it), but once resolved,
left-recursive rules combined with `('left', 'PLUS', ...)` naturally produce a
left-leaning tree for a chain like `a + b + c` → `(a + b) + c`, matching normal arithmetic
associativity. You don't need to write separate "chain" logic — the precedence declaration plus
this rule shape is sufficient.


## 3. SLY uses `return`

**SLY uses a plain `return`.** Each grammar-rule method returns the value that
becomes `p.<rulename>` in whatever rule used it:

```python
@_('ID ASSIGN expr SEMI')
def assign(self, p):
    return Assign(Var(p[0]), p[2])
```

Here `p[0]` is the matched `ID` token's value (a string), and `p[2]` is whatever the `expr`
rule that matched returned (an AST node) — not the raw token.


## 4. Turn on the conflict debug log — the lab plan expects you to read it, not just trust it

```python
parser = TinyCStrParser()
```

SLY prints shift-reduce/reduce-reduce conflict warnings to stderr **at class-definition time**
(when the module is imported / the class body runs), not when you call `.parse(...)`. If your
`expr` grammar has an unresolved ambiguity, you'll see something like:

```
WARNING: 4 shift/reduce conflicts
```

printed once, on import, regardless of what file you later parse. Before adding the
`precedence` table, deliberately run your Stage-1b grammar once and read this warning — the lab
plan explicitly asks you to inspect it before moving on, not just add `precedence` and assume
it's fine. After adding `precedence`, most or all of these warnings should disappear; any that
remain are worth understanding.

## 5. `p.expr` when the same nonterminal appears twice in one rule

```python
@_('expr PLUS expr')
def expr(self, p):
    return BinOp('+', p.expr0, p.expr1)
```

When a rule mentions the same symbol name more than once, SLY disambiguates by appending `0`,
`1`, ... in left-to-right order: `p.expr0` is the left operand, `p.expr1` is the right. Plain
`p.expr` would be ambiguous here and SLY will raise an error at class-definition time if you try
it.

## 6. `error(self, token)` — `token` can be `None`

Unlike the lexer's `error(self, t)` (always given a real bad character), the parser's
`error(self, token)` is called with `token=None` when the syntax error is *at the end of input*
(e.g. a missing closing `}`). Check for `None` before accessing `token.value`/`token.lineno`, or
you'll get a confusing `AttributeError` instead of a clean error message.

## 7. Quick self-check before you run the tests

- [ ] `precedence` tuple exists (Stage 1b only) and lists lower-precedence operators *first*.
- [ ] Every grammar rule method `return`s its AST/list/string value.
- [ ] `decl` returns a **list** of `SymbolTableEntry` (not a single entry) — `int a,b,c;` is one
      `decl` statement but three symbol table entries.
- [ ] You've actually looked at the shift-reduce conflict log at least once.
- [ ] `error()` handles `token is None` without crashing.
