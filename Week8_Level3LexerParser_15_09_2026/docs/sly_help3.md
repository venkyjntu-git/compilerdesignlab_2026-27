# SLY Level 3 Help (Week 8)

Read this before starting Stage 3a/3b. It builds on Week 5's `sly_help2.md` and covers only what
is new this week. Every SLY message and behavior quoted here was produced by actually running
SLY 0.5 on this week's grammar.

## 1. Keywords: add them to the `keywords` table, never as separate token rules

`if`, `else` and `while` look like identifiers, and the existing `ID` rule already matches them.
The lexer's `ID` function renames the token type through the `keywords` table:

```python
keywords = { ..., 'if': 'IF', 'else': 'ELSE', 'while': 'WHILE' }

@_(r'[a-zA-Z_][a-zA-Z0-9_]*')
def ID(self, t):
    t.type = self.keywords.get(t.value, 'ID')
    return t
```

So adding three dictionary entries is the **whole** lexer change for Level 3. Writing
`IF = r'if'` as its own rule instead is wrong in both possible positions, because SLY tries
patterns **in the order they appear in the class**:

| Where `IF = r'if'` goes | Tokens for `if iffy` |
|---|---|
| before `ID` | `IF if`, `IF if`, `ID fy` — the identifier `iffy` is split in two |
| after `ID` | `ID if`, `ID iffy` — the keyword is never recognized |

Only the table lookup gives the right answer, `IF if`, `ID iffy`: the longest identifier-shaped
match wins first, and only then does the lexer decide whether that whole word is a keyword.

## 2. Statements become recursive

```
if_stmt : IF LPAREN expr RPAREN stmt
block   : LBRACE stmt_list RBRACE
```

An `if_stmt` is a `stmt` that *contains* a `stmt`, and a `block` is a `stmt` that contains a
`stmt_list`. This is the same kind of recursion that `expr : expr PLUS expr` introduced in
Week 3, but at the statement level. Two consequences:

- **The branch is a single `stmt`.** `if (c) a = 1; b = 2;` guards only `a = 1;`, and `b = 2;` is
  the next statement after the `if`, exactly as in C. To guard both, write a block.
- **Reuse `stmt_list` for the block body.** Don't write a new list rule. An empty block `{ }` is
  legal and gives `Block` with no children.

Stage 3a's grammar is still **unambiguous**: SLY should report no conflict. If it does, compare
your rules to `docs/level3_grammar_reference.md` before moving on.

## 3. The dangling else: what SLY reports, and why

Add the Stage 3b rule

```python
@_('IF LPAREN expr RPAREN stmt ELSE stmt')
```

and SLY prints, when the parser class is built:

```
WARNING: 1 shift/reduce conflict
```

To see *where* the conflict is, add a class attribute `debugfile = 'parser.out'` to
`TinyCStrParser`, run any command once, and open `parser.out`. Search for `conflict`:

```
    (22) if_stmt -> IF LPAREN expr RPAREN stmt . ELSE stmt
    (23) if_stmt -> IF LPAREN expr RPAREN stmt .
  ! shift/reduce conflict for ELSE resolved as shift
    ELSE            shift and go to state 95
    RBRACE          reduce using rule 23 (if_stmt -> IF LPAREN expr RPAREN stmt .)
    ...
```

(Your rule and state numbers will differ; the shape will not.) The parser has just read
`IF ( expr ) stmt`, and the next token is `ELSE`. There are two legal moves:

- **shift** the `ELSE`, which continues rule 22: this `else` belongs to the `if` just read (the
  *innermost* one).
- **reduce** by rule 23: close this `if` as an else-less statement now, and let the `else` belong
  to some *enclosing* `if`.

For `if (a > b) if (b > c) x = 1; else x = 2;` both readings are grammatical, so the grammar is
ambiguous. **C's rule is that an `else` belongs to the nearest unmatched `if`**, which means
*shift*.

## 4. Resolving it explicitly with `%prec`

SLY's default for a shift/reduce conflict is to shift, and here that happens to be correct. The
goldens even pass with the warning present. Leaving it unresolved is still not acceptable:

- A "resolved" conflict that nobody chose is indistinguishable from a real grammar bug. Once your
  grammar always prints `1 shift/reduce conflict`, you stop reading the line, and the day it says
  `2`, a real bug has slipped through unnoticed.
- This week's deliverable is a grammar that builds with **zero conflict warnings**.
  `run_tests.py` checks this separately, as its first line (`grammar`).

The fix is the same `%prec` idea Week 5 used for casts:

```python
precedence = (
    ('nonassoc', 'IFX'),      # dummy token -- the lexer never produces it
    ('nonassoc', 'ELSE'),
    ('right', 'QUESTION', 'COLON'),
    ...                       # the Level 2 entries, unchanged
)

@_('IF LPAREN expr RPAREN stmt %prec IFX')       # the no-else rule
def if_stmt(self, value): ...

@_('IF LPAREN expr RPAREN stmt ELSE stmt')       # unchanged
def if_stmt(self, value): ...
```

**How SLY uses it.** On a shift/reduce conflict, SLY compares the precedence of the **rule**
it could reduce with the precedence of the **lookahead token** it could shift:

| | precedence |
|---|---|
| rule `IF ( expr ) stmt` (reduce) | `IFX` (given by `%prec IFX`) |
| token `ELSE` (shift) | `ELSE` |

Entries later in the tuple bind tighter, so `ELSE` beats `IFX`, SLY chooses **shift** on purpose,
and the warning disappears. Without `%prec IFX`, the rule's precedence would come from its
rightmost terminal, `RPAREN`, which has no precedence at all, so SLY could not decide and fell
back to its default plus a warning.

`nonassoc` is used because these entries never compete with themselves; associativity only matters
when a rule and a token share the *same* level, which can't happen here.

**Order matters, and getting it wrong is silent.** Swap the two lines, so that `ELSE` comes before
`IFX`, and SLY prints **no warning**, because the conflict is still "resolved". Now it is resolved
as *reduce*: the inner `if` is closed, then the outer `if` is closed, and the `else` has nothing
left to attach to. Every `else` in every program becomes:

```
[parser] Syntax error near 'else' at line 8
```

That is why the AST goldens (`tests/test13.tc`) matter as much as the warning count.

**For your write-up.** The textbook alternative is to rewrite the grammar itself, splitting
statements into *matched* ones (every `if` has its `else`) and *unmatched* ones:

```
stmt      : matched | unmatched
matched   : IF ( expr ) matched ELSE matched | other_stmt
unmatched : IF ( expr ) stmt | IF ( expr ) matched ELSE unmatched
```

This is conflict-free with no precedence declarations, but it doubles the statement rules, and
`while` has to be split the same way. `%prec` keeps the grammar readable. Comparing the two
approaches is a good paragraph for the take-home write-up.

## 5. Global declarations don't conflict with `main`

```
program          : global_decl_list func_def
global_decl_list : global_decl_list decl | empty
```

`int a;` (a global) and `int main(){` (the function) both begin with `INT ID`, so it looks as if
the parser can't know which one it is reading. It can, because it only has to decide at the
**third** token. After `INT ID`, a `LPAREN` means a function and a `COMMA` or `SEMICOLON` means a
declaration. A LALR(1) parser makes that choice with one token of lookahead, so the new rule adds
no conflict. Reuse the existing `decl` rules for globals; the declaration syntax is identical.

In the `program` action, globals go into `prog.getGlobalSymbolTable()`, not into `main`'s local
table. Check the result with `-symtab`: `tests/test11.sym.expected.txt` shows a `Global` section
followed by `main` with `(no local variables)`.

## 6. Line numbers

Use `lineno=value.lineno` on every new node, as the Level 2 rules do. For a rule starting with a
token, `value.lineno` is that first token's line, so an `If` records the line of its `if`
keyword. The provided type checker reports condition errors against that line; see
`tests/test_l3_errors.check.expected.txt`.

## 7. Quick self-check before you run the golden tests

- [ ] `if`, `else`, `while` are entries in `keywords`, not separate token rules.
- [ ] `stmt` has three new alternatives: `if_stmt`, `block` (Stage 3a) and `while_stmt` (Stage 3b).
- [ ] An `if`'s branch and a `while`'s body are a single `stmt`.
- [ ] `block` reuses `stmt_list`.
- [ ] `IFX` comes before `ELSE` at the top of `precedence`, and the no-else rule ends in `%prec IFX`.
- [ ] `python run_tests.py` prints `PASS  grammar` on its first line.
- [ ] `program` uses `global_decl_list`, and globals land in the global symbol table.
