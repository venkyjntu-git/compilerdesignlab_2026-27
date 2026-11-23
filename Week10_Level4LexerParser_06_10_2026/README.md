# Week 10 — Level 4 Lexer + Parser + Semantic Checker: Functions (Stages 4a → 4b)

## What is "Level 4" of TinyCStr?

Levels 1–3 gave you a complete compiler for a **single** `main`, with types, expressions,
`if`/`while` and globals, running on SPIM since Week 9. **Level 4 adds functions**:

- several functions per program, including `void` ones;
- typed parameters;
- prototypes (Slide 7: `int add(int,int);`);
- calls and `return`.

This week covers the **front end**: lexer, parser, and the semantic rules that functions bring.
Code generation for calls (activation records and the MIPS calling convention) is **Week 11**.

The work is staged so that only one hard idea arrives at a time:

- **Stage 4a** — a second function with **no parameters and no return value**, called from `main`
  (`printSquareOfFive();`). New ideas: one local scope per function, and a call as a statement or
  expression. Also the first whole-program rule: **exactly one `main`**.
- **Stage 4b** — **typed parameter lists**, prototypes, call arguments, and `return`. That means
  checking every call against the function's signature, and every `return` against the function
  it is in.

## Current file contents

### What's already provided (do not modify)

- **`ast_nodes.py`** — **new nodes**: `FunctionCall(name, args)`, used both as an expression and
  as a statement, and `Return(expr=None)`.
- **`Function.py`** — **changed**: parameters (`getParamList()`, `getParamSymbolTable()`) and the
  header's line number.
- **`Program.py`** — **changed**: prototypes (`FunctionPrototype`, `getPrototypes()`), and any
  number of functions.
- **`SymbolTable.py`** — `DataType.VOID` added (return types only).
- **`type_rules.py`** — a whole-program error with no line number now prints without `line ?:`.
- **`type_checker.py`** — mostly provided:
  - pass 1, `build_function_table()`: duplicate definitions, parameter rules, prototype checks;
  - name lookup through locals → parameters → globals;
  - an **unused-parameter warning**;
  - all of the Level 1–3 rules.

  Three methods are yours (below).
- **`tinycstr_parser.py`** — the Level 1–3 grammar, **plus one provided change**: every
  declaration now goes through a single `type` nonterminal (`docs/sly_help4.md` #2 shows the four
  conflicts that this change prevents).
- **`main.py`** — **changed**:
  - `-symtab` prints the function table and parameters;
  - `-check` prints warnings;
  - `-dot` draws every function;
  - `-3ac`/`-compile` say "planned for Week 11" for programs with calls, returns or more than one
    function.
- **`tac_generator.py`, `tac_to_mips.py`, and the rest of the back end** — Week 9's exercise, now
  fully implemented. Level 1–3 programs still compile and run on SPIM exactly as in Week 9.

### What you need to do

| File | Stage 4a | Stage 4b |
|---|---|---|
| `tinycstr_lexer.py` | keyword `void` | keyword `return` |
| `tinycstr_parser.py` | `func_def_list`, `func_head` (no parameters), `func_def`, `call` (no arguments), `call_stmt`, `expr : call` | parameters, prototypes, arguments, `return_stmt` |
| `type_checker.py` | `check_main()`, and `check_call()` without arguments | arguments in `check_call()`, `check_return()` |

### Documentation

- **`docs/level4_grammar_reference.md`** covers:
  - the grammar per stage and the AST shapes;
  - every semantic rule with its **exact** error message, and who writes each check;
  - implicit conversions of arguments and return values;
  - this level's design decisions.
- **`docs/sly_help4.md`** covers:
  - why declarations need one `type` nonterminal (4 shift/reduce conflicts otherwise);
  - why prototypes and definitions share one parameter rule (a reduce/reduce conflict otherwise);
  - why `ID` starting four different constructs is *not* a conflict;
  - how to read SLY's cascading syntax errors.
- **`docs/example4_original.tc`** — Slide 7's Example 4, **exactly as on the slide**, for the
  bug-hunt deliverable.

### Tests

| Program | Stage | What it exercises |
|---|---|---|
| `test17.tc` | 4a | a `void` helper with no parameters, called twice; a local `x` in each function |
| `test18.tc` | 4a | functions but **no `main`**: a semantic error |
| `test19.tc` | 4b | **Example 4, corrected**: globals, prototypes, `int` and `double` functions |
| `test20.tc` | 4b | parameters and return values; an `int` argument to a `double` parameter (inserted `Cast`); a call as an argument |
| `test21.tc` | 4b | global vs. parameter vs. local scope; `void` `return;`; `return` inside a `while` |
| `test_l4_errors.tc` | 4b | every function-related error, plus warnings, one per line |
| `test4`–`test16`, ... | L1–L3 | **regression**: tokens, AST, 3AC, MIPS and SPIM output identical to Week 9 |

## Step by step

1. Run `python run_tests.py` before changing anything. The `grammar` check and every Level 1–3
   regression test should pass (105 checks), and `test17`–`test21`/`test_l4_errors` fail.
2. Read `docs/level4_grammar_reference.md`, then `docs/sly_help4.md` #1–#2, #4–#5.
3. **Stage 4a, lexer and parser:** add `void`, then `func_def_list`, `func_head` and `func_def`,
   then `call`, `call_stmt` and `expr : call`. Test:
   ```bash
   python main.py -ast -symtab tests/test17.tc
   python run_tests.py test17
   ```
   `grammar` must still say PASS.
4. **Stage 4a, checker:** `check_main()`, then the Stage 4a part of `check_call()`. Test with
   `python run_tests.py test17 test18`.
5. Read `docs/sly_help4.md` #3, then do **Stage 4b, lexer and parser**: `return`, parameters,
   prototypes, arguments, and `return_stmt`. Test:
   ```bash
   python main.py -ast -symtab tests/test19.tc
   python run_tests.py test19 test20 test21
   ```
   (`.check` will still fail until step 6.)
6. **Stage 4b, checker:** arguments in `check_call()`, then `check_return()`. Test
   `test_l4_errors`, using `-v` to see a diff of any message that differs:
   ```bash
   python run_tests.py -v test_l4_errors
   ```
7. Run the full suite. Every line must be PASS, including the Level 1–3 regression tests.

## Example 4: the bug hunt (in-lab item 3, and part of the deliverable)

`docs/example4_original.tc` is Slide 7's Example 4 exactly as written. It has **at least five
bugs**:
- three are syntax errors;
- one is a semantic error;
- one is legal TinyCStr that the compiler reports only as a **warning**, although the program
  would compute the wrong answer.

Work through it with **your** compiler, one bug at a time:

```bash
cp docs/example4_original.tc ex4.tc          # Windows: copy docs\example4_original.tc ex4.tc
python main.py -parse ex4.tc                 # fix the FIRST reported error, re-run, repeat
python main.py -check ex4.tc                 # once it parses: errors, then warnings
python main.py -ast -symtab ex4.tc           # once it checks cleanly
```

Write down each bug in a table like this one:

| # | Line | Message from your compiler | Phase that caught it (lexer / parser / checker / warning) | Your fix | Why the original is wrong |
|---|---|---|---|---|---|

Also note any message that was only a **cascade** of an earlier error (`docs/sly_help4.md` #6).
For each fix, say whether you changed the *program* or could instead have changed the
*language*, and why you chose as you did. Finally, compare your fixed file with
`tests/test19.tc`. Any difference is fine if your version also passes `-check`, but explain it.

## Take-home (due at the start of Week 11's lab)

Write two more multi-function TinyCStr (L4) programs, and produce their ASTs and symbol tables
(`-ast -symtab`, and `-dot` for a diagram):

1. a **factorial helper** that is *recursive-looking but loop-based*: `int factorial(int n)`
   computes `n!` with a `while` loop, and `main` calls it for a few values;
2. a **two-function min/max** program: `int min(int a, int b)` and `int max(int a, int b)`, with
   `main` combining them (e.g. the middle value of three numbers, using only calls to `min` and
   `max`).

Both must pass `-check` with **no errors and no warnings**.

**Deliverable:**
- lexer, parser and semantic checker upgraded through Stages 4a–4b (`python run_tests.py` all
  PASS);
- the Example 4 bug table;
- the two take-home programs with their ASTs and symbol tables.

## Getting unstuck

- **`WARNING: ... shift/reduce conflicts` after adding `func_head`**: you are not using the
  provided `type` nonterminal in it (`docs/sly_help4.md` #2).
- **`WARNING: 1 reduce/reduce conflict`, and `int main(){` stops parsing**: you wrote separate
  parameter lists for prototypes and definitions (`docs/sly_help4.md` #3).
- **A call such as `x = f();` gives *two* errors**: `check_call()` must return `DataType.INT`
  after reporting an undefined or `void` function, so the assignment doesn't report again.
- **Your messages are right but in a different order**: the provided `check_program()` sorts
  errors by line; make sure you report each one through `self.error(...)` with the right line.

If you're still stuck, post in the Week 10 GitHub Issues.
