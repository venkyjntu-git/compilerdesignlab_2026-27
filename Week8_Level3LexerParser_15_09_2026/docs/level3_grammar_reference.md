# TinyCStr — Level 3 Token & Grammar Reference (Week 8)

Level 3 adds **control flow** to TinyCStr: `if`, `if-else`, `while`, and block statements
`{ ... }`. It also adds **global declarations** before `main`. Every Level 1 and Level 2 program
is still a valid Level 3 program, because the grammar only gains rules.

## Program structure (Slide 3 of the TinyCStr specification)

> Every TinyC program has an optional global declarations followed by one or more functions and
> one function must be main.

Level 3 implements the *optional global declarations* part. It still has exactly one function,
`main`. More functions come in Level 4 (Week 10).

```
<global declarations>      int a,b;  double c;      <- NEW this week (Stage 3b), optional
int main(){
    <local declarations>   int i;                   <- unchanged since Week 3
    <statements>           assign | print | if | while | block
}
```

---

## Stage 3a — plain `if` (no `else`) and blocks

**New token:** `IF`, a keyword. It needs no new regex (see `docs/sly_help3.md` #1).

**New grammar:**
```
stmt    : assign
        | print_stmt
        | if_stmt                         <- NEW
        | block                           <- NEW

block   : LBRACE stmt_list RBRACE         -> Block(stmts)

if_stmt : IF LPAREN expr RPAREN stmt      -> If(cond, then_stmt)
```

The guarded part of an `if` is **one `stmt`**, not a `stmt_list`. To guard several statements,
you write one *block* statement. A `stmt` can now contain another `stmt`, so the statement
grammar becomes **recursive**, just as `expr` did in Week 3's Stage 1b.

This stage isolates one new grammar pattern, a statement guarded by a condition. There is no
ambiguity yet, and SLY should build it with **no conflict warnings**.

Test: `tests/test10.tc` (one `if` guarding a single statement, one guarding a block).

---

## Stage 3b — `else`, `while`, global declarations

**New tokens:** `ELSE`, `WHILE` (keywords).

**New grammar:**
```
stmt       : ... | while_stmt                         <- NEW

if_stmt    : IF LPAREN expr RPAREN stmt %prec IFX     -> If(cond, then_stmt)            (3a rule + %prec)
           | IF LPAREN expr RPAREN stmt ELSE stmt     -> If(cond, then_stmt, else_stmt) <- NEW

while_stmt : WHILE LPAREN expr RPAREN stmt            -> While(cond, body)              <- NEW

program          : global_decl_list func_def          <- CHANGED (was: func_def)
global_decl_list : global_decl_list decl              <- NEW, same shape as decl_stmt_list
                 | empty
```

Adding the `if-else` rule makes the grammar **ambiguous**. In
`if (e1) if (e2) s1 else s2`, which `if` owns the `else`? This is the classic *dangling else*.
SLY reports it as `WARNING: 1 shift/reduce conflict`. You must resolve it *explicitly*; see
`docs/sly_help3.md` #3–#4.

Tests: `tests/test11.tc` (Example 3), `tests/test12.tc` (while), `tests/test13.tc` (dangling
else), `tests/test14.tc` (everything together, including an `else if` chain).

---

## Precedence, all levels (low to high)

```
IFX            (lowest)  dummy token: the no-else `if` rule, via %prec   <- NEW
ELSE                     the else keyword                                 <- NEW
ternary   ? :
relational  < > <= >= == !=
+  -
*  /
cast           (highest) dummy token UCAST, via %prec (Week 5)
```

`IFX` and `ELSE` never interact with the expression operators. Their position at the top of the
tuple is a convention, not a requirement. What matters is that **`ELSE` comes after (is higher
than) `IFX`**.

---

## AST node shapes (`ast_nodes.py`, provided — do not modify)

| Node | Fields | `label()` printed by `-ast` |
|---|---|---|
| `If(cond, then_stmt, else_stmt=None)` | `else_stmt` is `None` when there's no `else` | `If` — or `IfElse` when there is an else |
| `While(cond, body)` | `body` is one statement (often a `Block`) | `While` |
| `Block(stmts)` | a Python list of statements, possibly empty | `Block` |

A single `If` class covers both forms. The printed label is `If` or `IfElse` only so that you
can **see** in the `-ast` output which `if` an `else` attached to. For the dangling-else case:

```
if (a > b)                         If                  <- outer: NO else
    if (b > c)                       RelOp(>) ...
        x = 1;                       IfElse            <- inner: OWNS the else
    else                               RelOp(>) ...
        x = 2;                         Assign x = 1
                                       Assign x = 2
```

These are the first AST nodes whose children are *statements* rather than only expressions.

---

## Design decisions for Level 3 (deliberate, and the same for everyone)

1. **Blocks contain statements only, no declarations.** All locals are still declared at the top
   of `main`, as in Levels 1–2. Block-level scope (a variable visible only inside `{ }`) belongs
   to Level 4's scoping work (Week 10), so it is not introduced here.
2. **Globals come before the function, and have no initializers.** `int a=40,b=50;` is not legal
   TinyCStr at any level of this course; see *Example 3, corrected* below.
3. **A condition must be numeric** (`int`, `char` or `double`). Non-zero means true, as in C. A
   `string` is not a truth value, so `if (s)` is a type error. The provided `type_checker.py`
   reports it, using the same rule the ternary's condition has used since Week 6.
4. **No logical operators** (`&&`, `||`, `!`). The TinyCStr spec (Slide 2) lists arithmetic,
   relational, ternary and cast operators only. Combine conditions by nesting instead.
5. **A local hides a global of the same name**, as in C. The provided type checker looks a name up
   locally first, then globally.

---

## Example 3, corrected (Slide 6)

The slide version uses declaration initializers (`int a=40,b=50;`), which the TinyCStr grammar
doesn't have. Week 3 corrected Example 2 (`int a=30;`) into a valid program for the same reason.
Here, each initial value moves into an assignment statement at the start of `main`:

| Slide 6 (as written) | Corrected — `tests/test11.tc` |
|---|---|
| `int a=40,b=50;` | `int a,b;` |
| `double c;` | `double c;` |
| `int main(){` | `int main(){` |
| | `    a=40;` |
| | `    b=50;` |
| `  if(a>b)` | `    if(a>b)` |
| `    c=(double)a/b;` | `        c=(double)a/b;` |
| `  else` | `    else` |
| `    c=(double)b/a;` | `        c=(double)b/a;` |
| `  print c;` | `    print c;` |
| `}` | `}` |

This is the `if/else` form of Week 5–7's `test6.tc`: the same computation written with a ternary
operator. Once Week 9 generates code for it, `tests/test11.tc` must print exactly what
`test6.tc` already prints on SPIM, `1.25`.

---

## What `main.py` does with a Level 3 program this week

| Option | Level 3 program | Level 1/2 program |
|---|---|---|
| `-tokens`, `-parse`, `-ast`, `-dot`, `-symtab` | ✔ your lexer/parser | ✔ |
| `-check` | ✔ provided type checker (globals + conditions) | ✔ |
| `-3ac`, `-compile` | writes `# ... not implemented yet (Week 9)` | ✔ full pipeline, unchanged |

Translating control flow into 3AC labels and jumps, and then into MIPS branches, is **Week 9's**
job. A Level 3 program stops after type checking this week, by design.
