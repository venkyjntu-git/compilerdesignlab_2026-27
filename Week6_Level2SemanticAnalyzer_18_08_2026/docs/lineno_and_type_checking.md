# Line Numbers and Type Checking

## Where line numbers come from

Every AST node now accepts an optional `lineno` (see `ast_nodes.py`). The parser sets it using
SLY's `value.lineno` property.

```python
@_('expr PLUS expr')
def expr(self, value):
    return BinOp('+', value[0], value[2], lineno=value.lineno)
```

`value.lineno` walks the production's raw token/symbol list left to right and returns the
**first line number it finds** — skipping symbols that don't carry one (a plain Python list, for
instance, like what `id_list`/`stmt_list` return, has no `.lineno`). Two things make this
reliable without any extra bookkeeping on your part:

1. **Every real terminal token always carries a line number** (SLY sets this automatically
   during lexing), so any rule with a keyword/operator/identifier in its RHS will find
   one immediately.
2. **AST nodes carry their own `lineno` too**, once you've set it — so for a rule like
   `expr : expr PLUS expr`, `value.lineno` checks the *left* `expr` first, finds that child
   node's own (already-correct) `lineno`, and returns it immediately. Line numbers cascade
   naturally through nested expression.

verify: A multi-statement test program produced `lineno` values of 4, 5, 6, 7 for four consecutive statements, exactly matching the source — see `tests/test6.ast.expected.txt`'s corresponding `.tc` file.

## Why `type_checker.py`'s methods return `(node, type)`, not just `type`

"modify AST if required" — Type checking here isn't just *validation* (yes/no, is this legal); it's also *rewriting*: whenever an implicit conversion is needed (an `int` used where a `double` is expected), the checker **inserts an explicit `Cast` node** around the subtree that needs converting.

Example: `int a; double b; b = a;` is legal TinyCStr (implicit type conversion, matching C). Before
type-checking, the AST is:
```
Assign
  Var(b)
  Var(a)
```
After type-checking, it becomes:
```
Assign
  Var(b)
  Cast(DataType.DOUBLE)
    Var(a)
```
Nothing about the *source code* changed — but the tree now says explicitly, "convert this int to a double right here". Every `check_*` method therefore returns a pair: the node to substitute in place of what was passed in, and the type it evaluates to. The **caller** does the substitution (`node.left = new_left`, `stmt.expr = new_expr`, etc.) — a `check_*` method never mutates the node it was handed in place; it returns what should replace it.

## Error recovery: keep going after the first error

`self.error(message, lineno)` **records** an error, it doesn't raise or stop anything. Every
`check_*` method still returns a `(node, type)` pair even when it just reported an error — using
a reasonable fallback type (usually `DataType.INT`, or the "intended" type before the mismatch
was discovered) so the caller can keep type-checking the rest of the program. This is why
`tests/test_errors.tc` — deliberately packed with five different mistakes — reports all five in
one run instead of stopping at the first: undeclared `c`, a bad comparison, incompatible ternary
branches, an invalid cast, and an invalid assignment, each on its own line, each still letting
the checker continue.

One consequence worth knowing about: since the checker keeps going after an error, you can see
a *doubly-nested* `Cast` in an error report — e.g. `a = (int)(double)s;` where `s` is a
`string`. The explicit `(double)s` cast is invalid (reported), but the checker still returns
`DataType.DOUBLE` as that expression's "type" (a cast's result type is always its target,
regardless of whether the thing being cast was valid) — and then the *assignment* to `a` (an
`int`) sees a `DOUBLE`-typed expression and wraps *another* `Cast(INT)` around it. This isn't a
bug — it's the fallback-and-keep-checking policy working as intended, just visibly stacking two
casts in the printed tree for a program that already has a different error reported.

