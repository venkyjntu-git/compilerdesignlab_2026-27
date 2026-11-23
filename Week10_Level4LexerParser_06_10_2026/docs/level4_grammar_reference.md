# TinyCStr — Level 4 Grammar & Semantic Reference (Week 10)

Level 4 adds **functions**: several functions per program, `void` functions, typed parameters,
prototypes (Slide 7: `int add(int,int);`), calls, and `return`. Every Level 1–3 program is still a
valid Level 4 program, with the same tokens, AST, 3AC and MIPS. `tests/test4`–`test16` and the
other Level 1–3 tests check exactly that.

## Program structure (Slide 3)

> Every TinyC program has an optional global declarations followed by one or more functions and
> one function must be main.

```
<global part>      int a,b;               global variables     (Week 8)
                   int add(int,int);      prototypes           <- NEW (Stage 4b)
<functions>        void helper(){ ... }   one or more          <- NEW (Stage 4a)
                   int main(){ ... }
                   int add(int a1, int a2){ ... }
```

Globals and prototypes come first, then the functions. Functions may appear in **any order**:
`main` may call a function defined after it, with or without a prototype (see "Design decisions").

---

## Stage 4a — several functions, no parameters, calls

**New token:** `VOID` (keyword; a return type only — no variable is ever `void`).

```
program       : global_decl_list func_def_list            CHANGED (was: ... func_def)
func_def_list : func_def_list func_def | func_def          NEW: one or more

func_head     : type ID LPAREN RPAREN                      NEW  (return type, name, [], line)
              | VOID ID LPAREN RPAREN
func_def      : func_head LBRACE decl_stmt_list stmt_list RBRACE

stmt          : ... | call_stmt                            NEW
call_stmt     : call SEMICOLON
call          : ID LPAREN RPAREN                           -> FunctionCall(name, [])
expr          : ... | call                                 NEW
```

The `type` nonterminal (`type : INT | DOUBLE | CHAR | STRING`, used by `decl : type id_list
SEMICOLON`) is **provided** this week. `docs/sly_help4.md` #2 explains why functions make it
necessary.

Tests: `tests/test17.tc` (a `void` helper; two functions, each with its own local `x`) and
`tests/test18.tc` (no `main`: must be a semantic error).

## Stage 4b — parameters, prototypes, arguments, return

**New token:** `RETURN`.

```
func_head        : type ID LPAREN params_opt RPAREN         CHANGED: ( ) -> ( params_opt )
                 | VOID ID LPAREN params_opt RPAREN
params_opt       : param_list | empty
param_list       : param_list COMMA param | param
param            : type ID                                   -> (type, name)
                 | type                                      -> (type, None)   unnamed

global_decl_list : ... | global_decl_list func_proto         NEW
func_proto       : func_head SEMICOLON                       -> FunctionPrototype

call             : ID LPAREN args_opt RPAREN                 CHANGED
args_opt         : arg_list | empty
arg_list         : arg_list COMMA expr | expr

stmt             : ... | return_stmt                         NEW
return_stmt      : RETURN expr SEMICOLON                     -> Return(expr)
                 | RETURN SEMICOLON                          -> Return(None)
```

**One** `param` rule serves both prototypes and definitions: `type ID` or a bare `type`. An
unnamed parameter is fine in a prototype, but is an error in a definition. The *type checker*
reports that, because writing separate parameter grammars for the two cases creates a
conflict (`docs/sly_help4.md` #3).

Tests: `tests/test19.tc` (**Example 4, corrected**), `tests/test20.tc`, `tests/test21.tc`,
`tests/test_l4_errors.tc`.

---

## AST and program-structure shapes (provided)

| Object | Fields | `-ast` label |
|---|---|---|
| `FunctionCall(name, args)` — AST node | `args` is a list of expressions | `Call(add)` |
| `Return(expr=None)` — AST node | `expr` is `None` for `return;` | `Return` |
| `Function(returnType, name, params, lineno)` | `params`: list of `(DataType, name-or-None)` | `Function add` |
| `FunctionPrototype(returnType, name, params, lineno)` | in `Program.getPrototypes()` | — |

There is **one** `FunctionCall` node for both uses of a call. In `x = f();` it is an expression
inside an `Assign`. In `f();` the `FunctionCall` *itself* sits in the statement list, just as
`f();` in C is an expression used as a statement. Look for `Call(bump)` directly under
`Function main` in `tests/test21.ast.expected.txt`.

`-symtab` now also prints the **function table** (every prototype and definition, as C-style
signatures) and each function's parameters, marked `(parameter)`. This appears only for programs
with prototypes or more than one function, so Level 1–3 output is unchanged.

---

## Semantic rules

Name lookup inside a function body is **locals → parameters → globals**, so a local hides a
global of the same name (`tests/test21.tc`). Each function has its own local scope: two functions
can both declare an `x` (`tests/test17.tc`).

Every message below appears in some `tests/*.check.expected.txt`, word for word. Errors are listed
in source-line order; whole-program errors, which have no line, come first.

| Rule | Message | Who writes it |
|---|---|---|
| exactly one `main` | `program has no 'main' function` | **you** (`check_main`, 4a) |
| `main`'s signature | `'main' must be declared as int main() with no parameters` | **you** (`check_main`, 4a) |
| call of an unknown name | `call to undefined function 'f'` | **you** (`check_call`, 4a) |
| `void` value used | `void function 'f' used in an expression` | **you** (`check_call`, 4a) |
| argument count | `function 'f' expects 2 argument(s), got 1` | **you** (`check_call`, 4b) |
| argument type | `argument 2 of 'f': cannot pass DataType.STRING as DataType.INT` | **you** (`check_call`, 4b) |
| `return;` in non-void | `return without a value in function 'f' returning DataType.INT` | **you** (`check_return`, 4b) |
| `return e;` in void | `return with a value in void function 'f'` | **you** (`check_return`, 4b) |
| return type | `cannot return DataType.STRING from function 'f' returning DataType.INT` | **you** (`check_return`, 4b) |
| one definition per name | `function 'f' defined more than once` | provided |
| named parameters in a definition | `parameter 1 of 'f' has no name` | provided |
| distinct parameter names | `duplicate parameter 'a' in 'f'` | provided |
| locals vs. parameters | `local variable 'p' in 'f' redeclares a parameter` | provided |
| prototype vs. definition | `prototype of 'f' does not match its definition` | provided |
| every prototype is defined | `function 'f' declared but never defined` | provided |
| *(warning)* | `parameter 'a1' of 'add' is never used` | provided |

**Implicit conversions.** A numeric argument passed to a parameter of a different numeric type,
or a numeric value returned from a function with a different numeric return type, is converted
exactly as an assignment converts: the checker wraps it in an inserted `Cast`. `tests/test20.tc`
passes an `int` to `half(double v)`, and its `.check` shows `Cast(DataType.DOUBLE)` around the
argument.

**Warnings** never stop compilation. A *named parameter the body never uses* is legal, but it is
usually a mistake: often the body uses some other variable where it meant the parameter.

---

## Design decisions for Level 4 (deliberate, and the same for everyone)

1. **`void` is a return type only.** There are no `void` variables, parameters or `(void)` lists:
   write `void f()`.
2. **Function names resolve over the whole program**, so a function may be called before its
   definition appears. A prototype is optional; if present, it must match the definition exactly
   (return type and parameter types).
3. **"Every path returns a value" is not checked.** An `int` function that can reach its end
   without a `return` is accepted, as most C compilers do without `-Wreturn-type`. What such a
   call returns is decided by Week 11's code generation.
4. **No unary minus.** TinyCStr has never had one; `-5` is a syntax error at every level, so
   negative values are written as `0 - 5`.
5. **Recursion is allowed** by the grammar and the checker. Week 11's stack frames make it work.
6. **`-3ac`/`-compile` stop at Level 4 programs this week** (`# ... not implemented yet (Week 11)`):
   calls, parameters and return values need activation records and the MIPS calling convention.
   Level 1–3 programs still compile and run exactly as in Week 9.
