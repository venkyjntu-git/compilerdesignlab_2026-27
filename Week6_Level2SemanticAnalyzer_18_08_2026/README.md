# Week 6 — Semantic Analysis

## What is semantic analysis, and why now?

Everything through Week 5 only checks whether a program is *syntactically* valid — does it follow rules of the grammar? A program like `c = a + b;` where `a` was never declared, or `d = s < 5;` comparing a `string` against a number, parses perfectly fine — the grammar has no way to know those are meaniningful or not.
**Semantic analysis** is the pass that catches exactly this: using the symbol table
built during parsing (name → declared type), it walks the AST and checks that every use of a
variable makes sense, and that every operator is applied to compatible types.

This week also introduces a second, less obvious job for the same pass: **making implicit type
conversions explicit**. `int a; double b; b = a;` is legal in TinyCStr — but somewhere before
code generation, something has to decide *how* an `int` becomes a `double`.  this week's checker should **rewrites the AST**, inserting a `Cast` node exactly where an implicit conversion happens. By the time this pass is done, every type conversion in the program — whether the programmer wrote it explicitly with `(double)` or it happened implicitly — is a visible `Cast` node in the tree.

## What we're trying to do this week

Build `type_checker.py`: given a function's AST and its symbol table,
- report every undeclared-variable use, with a line number;
- report every type mismatch (bad arithmetic, bad comparison, incompatible ternary branches,
  invalid casts, invalid assignments), each with a line number;
- insert explicit `Cast` nodes wherever an implicit conversion is legal and needed.

## Current file contents

### What's already provided (do not modify)

- **`tinycstr_lexer.py`, `tinycstr_parser.py`** — a **verified, complete Level 2 reference**
  (Stages 1 + 2a + 2b + 2c).
- **`ast_nodes.py`** — **changed this week**: every node now accepts an optional `lineno`. See
  `docs/lineno_and_type_checking.md` for exactly how the parser populates it.
- **`SymbolTable.py`, `Function.py`, `Program.py`, `three_address_code.py`, `tac_generator.py`,
  `tac_to_mips.py`** — unchanged from Week 5.
- **`type_rules.py`** — TinyCStr's promotion policy as plain facts about the language
  (`is_numeric()`, `promote()`), and `SemanticError`, the small message+line record type checker
  errors are collected in.
- **`main.py`** — new `-check` flag (writes an error report + the type-checked AST to
  `<file>.check`); `-symtab` is finally implemented (writes `<file>.sym`, "planned for Week 6"
  since Week 2); `-3ac`/`-compile` now run the type checker first and abort cleanly if there are
  errors, rather than attempting codegen on a program that doesn't type-check.

### What you need to do

- **`type_checker.py`** — the actual exercise, staged into five sub-tasks matching the lab
  plan's own requirements: undeclared-variable detection, arithmetic promotion, relational
  comparability, ternary unification, and assignment/cast conversion rules. Each `check_*`
  method's docstring specifies exactly what to check and what to return.

### Documentation

- **`docs/lineno_and_type_checking.md`** — how `value.lineno` actually works in SLY (verified
  directly), why every `check_*` method returns `(node, type)` instead of just a
  type, the error-recovery policy that lets one run catch every error instead of just the first.

### Tests

`tests/test4.tc`–`tests/test7.tc` are carried over from Week 5 (plus one new comprehensive
program, `test7.tc`) — all four are already confirmed to report **zero** type errors, which
directly satisfies the take-home's "run the checker over Week 5's test programs" starting point.
`tests/test_errors.tc` is new: a single program deliberately containing all five categories of
mistake (undeclared variable, bad comparison, incompatible ternary, invalid cast, invalid
assignment) — useful both as a test case and as a template for your own take-home error report.

## Step by step

1. Read `docs/lineno_and_type_checking.md` fully before writing code — mainly the `(node, type)` return
   convention.
2. Implement `check_var()` and the undeclared-variable half of `check_assign_stmt()` first — the
   simplest sub-task, and everything else depends on symbol lookups working correctly.
3. Implement `check_binop()`. Test:
   ```bash
   python main.py -check tests/test4.tc
   diff tests/test4.tc.check tests/test4.check.expected.txt
   ```
4. Implement `check_relop()`, `check_ternary()`, `check_cast()`, then finish
   `check_assign_stmt()`'s conversion-rule half. Test against `test5.tc`/`test6.tc`/`test7.tc`
   the same way.
5. Test against `tests/test_errors.tc` — confirm all 5 errors are reported in one run, with
   correct line numbers, matching `tests/test_errors.check.expected.txt`.
6. Take-home: write up at least 3 of the caught errors (from `test_errors.tc` or your own
   programs) as a short report — what the mistake was, what error message and line number your
   checker produced, and why that's the correct diagnosis.

## Getting unstuck

 If you're still stuck, post in the Week 6 GitHub Issues.
