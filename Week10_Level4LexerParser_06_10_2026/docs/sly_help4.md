# SLY Level 4 Help (Week 10)

This builds on `sly_help3.md`. Every SLY message quoted here was produced by running SLY 0.5 on the
grammar variant described.

## 1. Keywords

`void` and `return` are two more entries in the lexer's `keywords` table, exactly like Week 8's
`if`/`else`/`while` (`sly_help3.md` #1 explains why they must not be separate token rules).

## 2. Why declarations now use one `type` nonterminal (provided)

Up to Week 9, a declaration was spelled out per type, as `decl : INT id_list SEMICOLON`, the same
for `DOUBLE`, and so on. A function header needs a return type, `type ID LPAREN ...`. Keep the old
`decl` rules next to a `type`-based `func_head`, and SLY reports:

```
WARNING: 4 shift/reduce conflicts
```

One of the four states, from `parser.out`:
```
    (11) decl -> STRING . id_list SEMICOLON
    (7) type -> STRING .
  ! shift/reduce conflict for ID resolved as shift
```

After reading `string`, with an `ID` next, the parser must decide **now** whether `string` is
the start of a declaration (shift the `ID`) or a `type` for a function header (reduce
`type -> STRING`). Both continue with an `ID`, and the token that would tell them apart (`(`
versus `,`/`;`) is still one token further away. LALR(1) sees one token ahead, so it cannot
decide. SLY's default, shift, then breaks *every* typed function header: Example 4 fails with
`Syntax error near '(' at line 3`.

Routing declarations through the *same* `type` nonterminal removes the early decision. Both
`int a;` and `int f(...)` reduce `INT` to `type` first, shift `ID`, and only then look at the
next token: `(` means a function, while `,` or `;` means a declaration. **The rule of thumb is to
make two constructs share a common prefix in the grammar for as long as they share it in the
source.**

## 3. One parameter rule for prototypes and definitions

It is tempting to write one parameter list for prototypes (types only) and another for
definitions (types with names), each optional:

```
item : TYPE ID LPAREN proto_params_opt RPAREN SEMI
     | TYPE ID LPAREN def_params_opt RPAREN LBRACE ... RBRACE
proto_params_opt : proto_params | empty
def_params_opt   : def_params   | empty
```

SLY reports:
```
WARNING: 1 reduce/reduce conflict
  ! reduce/reduce conflict for RPAREN resolved using rule 5 (proto_params_opt -> empty .)
```

For `f()`, the parser sees `)` right after `(` and must reduce an *empty* list, but which one?
It can't know yet whether `;` or `{` comes after the `)`. SLY settles a reduce/reduce conflict by
picking the rule listed first, so every **definition** with no parameters, `int main(){`
included, stops parsing. A reduce/reduce conflict almost always means the grammar has to change.
Precedence declarations cannot fix one.

The fix follows the same idea as #2: share the prefix. There is **one** `params_opt`, **one**
`param : type ID | type`, and a shared `func_head` that a prototype finishes with `;` and a
definition with a body. Whether every parameter of a *definition* has a name becomes a semantic
rule, checked in `build_function_table()`. **Not every rule of the language has to be in the
grammar; some are easier and clearer in the checker.**

## 4. `ID` now starts four different things — no conflict

At the start of a statement, or inside an expression, an `ID` can begin:

| Source | Grammar | Token after `ID` |
|---|---|---|
| `x = 5;` | `assign : ID ASSIGN expr SEMICOLON` | `=` |
| `f();` | `call_stmt : call SEMICOLON`, `call : ID LPAREN ...` | `(` |
| `y = x + 1;` | `expr : ID` | an operator, `;`, `)`, ... |
| `y = f(x) + 1;` | `expr : call` | `(` |

Unlike #2, the deciding token here is the **very next** one, so LALR(1) handles all four cases
with no conflict. Your Stage 4a grammar should still build with zero warnings; `run_tests.py`
checks this on its first line.

## 5. A call statement needs no wrapper node

`call_stmt : call SEMICOLON` just returns `value[0]`, the `FunctionCall` node, and that node goes
straight into the statement list. The type checker tells the two uses apart by *where* it meets
the node: `check_stmt()` calls `check_call(node, as_statement=True)`, while `check_expr()` calls
`check_call(node)`. That is exactly the information it needs to report `void function 'f' used in
an expression` only when the value is actually used.

## 6. Reading SLY's syntax errors: fix the first one, then re-run

After a syntax error, SLY tries to **recover** and keep parsing, so that it can report more than
one error per run. Recovery is a guess, and after a guess the parser can report errors that are
only consequences of the first one. On Slide 7's Example 4, for example, after two of its bugs
are fixed, the parser reports two errors on the same line for what is really a single mistake.

So when working through `docs/example4_original.tc`: **trust the first message, fix that bug, and
re-run.** Treat later messages as hints until they reappear on their own. Your bug list should
record which messages were real and which were cascades.

## 7. Quick self-check

- [ ] `void` and `return` are `keywords` entries.
- [ ] `program : global_decl_list func_def_list`, and `func_def_list` is one or more `func_def`.
- [ ] One `func_head` (two rules: `type ...` and `VOID ...`) is shared by `func_def` and
      `func_proto`.
- [ ] One `params_opt` / `param_list` / `param`; `param` allows a missing name.
- [ ] `call` is used both as `expr : call` and in `call_stmt : call SEMICOLON`.
- [ ] `python run_tests.py` prints `PASS  grammar` (zero conflicts) after each stage.
