# Integrated Demo Runbook (Week 12)

A ~10-minute walk through the *whole* compiler you built, on one program: `demo/demo.tc`. It uses
every language level, and has something for each optimization to find. Run each command from this
folder and show the file it writes. The expected content is in `tests/test_demo.*.expected.txt`;
`test_demo.tc` is the same program.

| # | Stage (week built) | Command | Show |
|---|---|---|---|
| 1 | Lexer (2, 5, 8, 10) | `python main.py -tokens demo/demo.tc` | `demo/demo.tc.toks`: keywords from every level (`WHILE`, `RETURN`, ...), `REAL_CONST`, `STRING_CONST`, line numbers |
| 2 | Parser + AST (3, 5, 8, 10) | `python main.py -ast -dot demo/demo.tc` | `demo.tc.ast`; render `dot -Tpng demo/demo.tc.dot -o ast.png` |
| 3 | Symbol tables (6, 8, 10) | `python main.py -symtab demo/demo.tc` | the global `calls`, the function table, parameters vs. locals |
| 4 | Semantic analysis (6, 10) | `python main.py -check demo/demo.tc` | `No type errors found.` and the inserted `Cast(DataType.DOUBLE)` in `average` |
| 5 | 3AC (4, 7, 9, 11) | `python main.py -3ac demo/demo.tc` | one block per function; `PARAM`/`CALL`, `if_false`, the ternary's `?` triple |
| 6 | CFG (12) | `python main.py -cfg demo/demo.tc` | `sumTo`'s loop back edge; `fact`'s two `RETURN` blocks with no successor |
| 7 | Optimization (12) | `python main.py -optreport demo/demo.tc` | `main` before/after (below), the data-flow tables, and the last line: `183 unoptimized, 169 optimized` |
| 8 | MIPS (4, 7, 9, 11) | `python main.py -O -compile demo/demo.tc` | `f_sumTo:` prologue, homing `$a0`, `jal f_fact`, `ret_fact:` |
| 9 | Run it | `spim -file demo/demo.tc.spim` (or QtSpim) | `555.5highY1` |

Then the closing argument, step 10: **the optimizer changed nothing the program prints.**

```bash
python run_tests.py -spim test_demo     # run-on-spim:ok  spim-O:ok
```

## What step 7 shows in `main`

| Before (30 triples) | After (23 triples) | Why |
|---|---|---|
| `(0) * 2, 3`, `(1) + (0), 4`, `(2) a = (1)` | — | folded to `a = 10`, propagated, then dead |
| `(3) * a, 2`, `(4) b = (3)` | — | `b = 20`: only used by `unused` |
| `(5) * a, b`, `(6) unused = (5)` | — | dead: never read |
| `(7) PARAM a` | `(0) PARAM 10` | copy propagation of the constant |
| `CALL sumTo`, `CALL average`, `CALL fact` | all kept | calls may print or change the global `calls` |

`average`, `sumTo` and `fact` don't change at all. Be ready to explain why: no constants, no
repeated expression, no dead assignment, and inside `sumTo`'s loop every variable changes on every
iteration (`docs/optimization_reference.md` #5).

## Questions to be ready for

- *Why is `verdict = ...` not folded, even though `avg` is 5.5?* `avg` comes from a **call**, which
  constant folding can't see through. Folding across calls would need interprocedural analysis.
- *Why does `print calls;` read memory at the end, instead of using 1?* `calls` is a global
  changed inside `average`. Copy propagation forgets globals at every `CALL`.
- *Where are `a` and `b` in the MIPS?* Nowhere: they were never assigned. Their frame slots still
  exist (`-symtab`), unused.
