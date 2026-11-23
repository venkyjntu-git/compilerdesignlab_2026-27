# Week 8 — Level 3 Lexer + Parser: Control Flow (Stages 3a → 3b)

## What is "Level 3" of TinyCStr?

- **Level 1** (Weeks 2–4): `int` only, assignment, `print`, arithmetic. Full pipeline to SPIM.
- **Level 2** (Weeks 5–7): `double`/`char`/`string`, relational operators, ternary, casts. Full
  pipeline to SPIM, finished last week.
- **Level 3** (this week, plus Week 9): **control flow**. That means `if`, `if-else`, `while`,
  block statements `{ ... }`, and **global declarations** before `main`.

Every Level 1 and Level 2 program is still a valid Level 3 program, because the grammar only
gains rules. Level 3 still has exactly one function, `main`; more functions are Level 4.

## What we're trying to do this week

Extend the **lexer and parser only**, so that a Level 3 program produces the AST you'd expect.
The type checker comes already extended for Level 3. 3AC and MIPS for control flow are
**next week**.

The work is staged so that only one hard idea arrives at a time:

- **Stage 3a** — plain `if ( expr ) stmt` (no `else`) and blocks `{ ... }`. This brings one new
  grammar pattern, a statement guarded by a condition, and **no ambiguity**: SLY should build it
  without a single conflict warning.
- **Stage 3b** — `else`, `while ( expr ) stmt`, and global declarations. Adding `else` makes the
  grammar ambiguous, the classic **dangling else**, and you resolve it *explicitly* with SLY's
  `%prec` mechanism. Leaving it to SLY's silent default is not acceptable.

## Current file contents

### What's already provided (do not modify)

- **`ast_nodes.py`** — **changed this week**. Three new statement nodes:
  - `If(cond, then_stmt, else_stmt=None)` prints as `If` or `IfElse`, so the `-ast` output shows
    which `if` an `else` attached to.
  - `While(cond, body)`.
  - `Block(stmts)`.

  These are the first nodes whose children are statements. `to_dot()` now also closes its file.
- **`Program.py`** — **changed this week**: a `Program` owns a **global** `SymbolTable`
  (`getGlobalSymbolTable()`), next to each function's local one.
- **`type_checker.py`** — **changed this week**, provided:
  - It looks names up local-first, then global.
  - It checks the new statements. An `if`/`while` condition must be numeric (`if (s)` on a string
    is an error), and branches, loop bodies and block contents are checked recursively.
- **`main.py`** — **changed this week**:
  - `-symtab` prints a `Global` section when the program has globals.
  - New **`-dot`** flag writes `file.dot`, the AST as Graphviz, for the take-home diagrams.
  - `-3ac` and `-compile` now *say* that a Level 3 program is Week 9's work, instead of hiding
    the problem behind a blanket `try/except`.
- **`tac_generator.py`, `tac_to_mips.py`** — **Week 7's exercise, now fully implemented** as the
  reference back end. It reproduces all of Week 7's golden `.3ac`/`.s` files exactly, so Level 1/2
  programs still compile end to end.
- **`SymbolTable.py`, `Function.py`, `three_address_code.py`, `type_rules.py`** — unchanged.
- **`run_tests.py`** — **new**: runs every golden test and prints PASS/FAIL. It works on Windows
  too, where `diff` isn't available. Its first check, `grammar`, fails if SLY reports **any**
  conflict.

### What you need to do

- **`tinycstr_lexer.py`** — the tokens `IF`, `ELSE`, `WHILE` are already declared. Add them to the
  `keywords` table: `if` in 3a, `else`/`while` in 3b. That's the whole lexer change. Read
  `docs/sly_help3.md` #1 for why they must *not* be separate token rules.
- **`tinycstr_parser.py`** — the Level 1/2 grammar is complete. Your TODOs:
  - **3a:** `stmt` alternatives for `if_stmt` and `block`, plus the `block` and no-else `if_stmt`
    rules.
  - **3b:** the `if-else` rule, the `while_stmt` rule, `program : global_decl_list func_def`, and
    the dangling-else fix (two `precedence` entries plus `%prec IFX`).

### Documentation

- **`docs/level3_grammar_reference.md`** — Level 3 tokens and grammar per stage, AST node shapes,
  the precedence table, this level's design decisions, and Slide 6's Example 3 *corrected* (the
  slide uses declaration initializers, which TinyCStr doesn't have).
- **`docs/sly_help3.md`** — the SLY mechanics this week needs:
  - keywords vs. token rules;
  - recursive statements;
  - what SLY's `1 shift/reduce conflict` means, and how to inspect it with `debugfile`;
  - why `%prec IFX` fixes it, and what silently goes wrong if the two precedence lines are
    swapped;
  - why globals don't conflict with `int main()`.

### Tests

| Program | Stage | What it exercises |
|---|---|---|
| `test10.tc` | 3a | `if` guarding one statement; `if` guarding a block |
| `test11.tc` | 3b | **Example 3 (Slide 6), corrected**: globals + `if-else` + casts |
| `test12.tc` | 3b | `while` loop: sum of 1..N |
| `test13.tc` | 3b | **dangling else**: nearest-`if` binding, and braces forcing the outer `if` |
| `test14.tc` | 3b | everything: globals of two types, `while`, an `else if` chain |
| `test_l3_errors.tc` | 3b | type errors in control flow, reported with line numbers by `-check` |
| `test_syntax_error.tc` | 3a | `if a > b` without parentheses must be a syntax error |
| `test4`–`test9`, `test_errors` | L2 | **regression**: Week 7's programs must still give identical tokens/AST/3AC/MIPS |

Golden outputs are `tests/<name>.<toks|ast|sym|check|3ac|s>.expected.txt`. For Level 3 programs
the goldens stop at `-check`, and `test11.3ac`/`test11.s` show the expected "Week 9" message.

## Step by step

1. Run `python run_tests.py` once **before changing anything**. The Level 2 regression tests
   should already pass, and `test10`–`test14` should fail. This confirms your setup works. SLY
   will warn that `IF`, `ELSE` and `WHILE` are "defined, but not used" until you use them; that's
   expected.
2. Read `docs/level3_grammar_reference.md`, then `docs/sly_help3.md` #1–#2.
3. **Stage 3a.** Add the `if` keyword, then the `block` and no-else `if_stmt` rules. Test:
   ```bash
   python main.py -tokens -ast tests/test10.tc
   python run_tests.py test10 test_syntax_error
   ```
   `grammar` must say **PASS**: Stage 3a has no ambiguity. Also run
   `python main.py -parse tests/test_syntax_error.tc` and read the error message it prints.
4. Read `docs/sly_help3.md` #3–#4 **carefully** before going on. The dangling else is the main
   concept of the week.
5. **Stage 3b, part 1.** Add `else`, `while` and the `if-else`/`while` rules. SLY will now print
   `WARNING: 1 shift/reduce conflict`. Before fixing it, add `debugfile = 'parser.out'` to the
   parser class, run once, and find the conflict state in `parser.out`. Copy it into your
   write-up.
6. **Stage 3b, part 2.** Resolve the conflict with `IFX`/`ELSE` + `%prec IFX`. The warning must
   disappear. Verify with `test13`: in its `.ast`, the first `if` has the **inner** `IfElse`, and
   the braced one is an **outer** `IfElse` around a `Block`.
7. **Stage 3b, part 3.** Global declarations: change `program` to
   `global_decl_list func_def`. Test with `test11` and check its `-symtab` output.
8. Run the full suite. Every line must be PASS, including `grammar` and the Level 2 regression
   tests:
   ```bash
   python run_tests.py
   python run_tests.py -v test13      # shows a diff for anything that fails
   ```
9. Try the type checker on control flow: `python main.py -check tests/test_l3_errors.tc`, then
   read `tests/test_l3_errors.tc.check`.

## Take-home (due at the start of Week 9's lab)

1. Write a TinyCStr (L3) program with an **`if` nested inside a `while` loop**, for example
   counting evens vs. odds from 1..N. TinyCStr has no `%` operator, so test evenness with
   integer division: `n - (n/2)*2`. Produce its AST:
   ```bash
   python main.py -ast -dot evens_odds.tc
   dot -Tpng evens_odds.tc.dot -o evens_odds.png     # needs Graphviz (graphviz.org)
   ```
2. A one-page **dangling-else write-up**, covering:
   - a 3–4 line program where the `else` could belong to two different `if`s;
   - SLY's warning and the conflict state from your `parser.out` (step 5 above): name the shift
     move and the reduce move;
   - your fix, and *why* it makes SLY shift (rule precedence vs. token precedence);
   - what happens if you swap the `IFX`/`ELSE` lines. Try it and report what you see;
   - your before/after AST for `test13.tc`, and one sentence on the matched/unmatched grammar
     alternative (`docs/sly_help3.md` #4).

**Deliverable:** lexer and parser upgraded through Stages 3a–3b (`python run_tests.py` all PASS,
including `grammar`), the dangling-else write-up, and the AST (text + diagram) for **2
control-flow programs**: your evens/odds program, plus `tests/test12.tc` or `tests/test14.tc`.

## Getting unstuck

- `Syntax error near 'else'` on **every** `if-else`: your `IFX`/`ELSE` lines are in the wrong
  order (`docs/sly_help3.md` #4).
- `iffy` or `whileCount` tokenized wrongly: you wrote a separate `IF = r'if'` rule instead of
  using the `keywords` table (`docs/sly_help3.md` #1).
- `-symtab` shows the globals under `main`: the `program` action is adding them to the local table.

If you're still stuck, post in the Week 8 GitHub Issues.
