# TinyCStr — Level 2 Token & Grammar Reference (Week 5)

## Stage 2a: `double` declarations, real constants

New tokens: `DOUBLE` (keyword), `REAL_CONST` (a real number, e.g. `3.14`).

New grammar: `decl : DOUBLE id_list SEMICOLON` (same shape as the existing `INT` rule),
`expr : REAL_CONSTANT`.


## Stage 2b: `char`/`string` declarations and constants, relational operators

New tokens: `CHAR`, `STRING` (keywords), `CHAR_CONST` (`'x'`), `STRING_CONST` (`"hello"`), and six
relational operators: `LT` (`<`), `GT` (`>`), `LE` (`<=`), `GE` (`>=`), `EQ` (`==`), `NE` (`!=`).

New grammar: two more `decl` alternatives (`CHAR id_list SEMICOLON`,
`STRING id_list SEMICOLON`), `expr : CHAR_CONST | STRING_CONST`, and six new `expr` alternatives for the relational operators, each building a **`RelOp(op, left, right)`** node — one new AST class covering all six comparisons, the same way `BinOp` covers all four arithmetic operators.


## Stage 2c: casts, ternary — where mixed types first become legal

New tokens: `QUESTION` (`?`), `COLON` (`:`).
 **Casts need no new tokens at all** — `(double)` and
`(int)` are just `LPAREN`, the existing `DOUBLE`/`INT` keyword token, and `RPAREN`, already in
the lexer. Cast is purely a *parser* addition.

New grammar:
```
expr : LPAREN DOUBLE RPAREN expr    -- Cast("double", expr)
     | LPAREN INT RPAREN expr       -- Cast("int", expr)
     | expr QUESTION expr COLON expr -- Ternary(cond, then_expr, else_expr)
```

 A cast is what makes `(double)a / b` legal even though `a` is `int` and the division now involves a `double`-typed subexpression. Nothing about the grammar *enforces* correct typing here — e.g. `(double)a` doesn't check that `a` was actually declared `int`. 

## Precedence, all four levels (low to high)

```
ternary        (lowest)
relational     (< > <= >= == !=)
+  -
*  /
cast           (highest)
```

Casts higher precedence than arithmetic on purpose: `(double)a/b` must parse as `((double)a)/b`,
not `(double)(a/b)` — the cast applies to `a` alone, then the division happens. 
This needs SLY's `%prec` mechanism (a fictitious high-precedence token attached to the cast rule), not just a plain precedence-table entry — see `docs/sly_help2.md` #5 for exactly why and the syntax.

Ternary is right-associative (`a ? b : c ? d : e` parses as `a ? b : (c ? d : e)`, matching C) —
this was verified directly rather than assumed; see the docs.

## Change `Num` to `Const` AST, store type info based on constant value

A integer constant, double constant, a char constant, and a string constant all become `Const(value, type)` — the same AST class Constant, distinguished only by the  `type` of  (`INT`/`DOUBLE`/`STRING`/`CHAR`). 

## Sample Test case of Level 2

```
int main(){
    int a,b;
    double c;
    a=40;
    b=50;
    c = (a>b) ? (double)a/b : (double)b/a;
    print c;
}
```
