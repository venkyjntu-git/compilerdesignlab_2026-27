# Week 12 — Code Optimization + Integrated Demo

Your compiler is complete: every TinyCStr program, Levels 1–4, runs on SPIM. This final week adds
the **optimization** phase between 3AC and MIPS, then closes with a live demo of the whole
pipeline.

## What we're trying to do this week

1. **Build the CFG** from 3AC: leaders, basic blocks, and successor/predecessor edges. Test it on
   the nested `if`-in-`while`-in-`if` program and compare it with your Week 9 drawing.
2. **Local optimizations, within one basic block**: constant folding and copy propagation.
3. **CSE via available expressions**: a forward, *must* data-flow analysis (gen/kill, iterated to
   a fixed point), reusing a value that is still available instead of recomputing it.
4. **Dead code elimination via liveness**: a backward, *may* data-flow analysis; remove
   assignments that are dead on every path.

Every optimization must leave what the program **prints** unchanged. `run_tests.py -spim` checks
exactly that, for every test program.

## Current file contents

### What's already provided (do not modify)

- **`ir_utils.py`** — **new**: editing triples safely.
  - `replace_uses()`, `delete()`, `delete_unused_value()`;
  - `compact()`, which renumbers the triples and fixes every `TripleRef` after deletions.
- **`optimizer.py`** — **new**: the pipeline. It runs the local passes until they stop changing
  anything, then CSE, the local passes again, and DCE rounds; it also records every
  before/after for `-optreport`.
- **`main.py`** — **new flags**:

  | Flag | Effect |
  |---|---|
  | `-cfg` | the CFG per function, in `file.cfg` and `file.cfg.dot` |
  | `-O` | optimize before `-3ac` / `-compile` / `-cfg` |
  | `-passes fold,copy,cse,dce` | choose which passes to run |
  | `-optreport` | before/after 3AC of every pass, the data-flow tables, and MIPS instruction counts, in `file.opt` |

- **`tac_to_mips.py`, `three_address_code.py`** — a numeric literal may now be **negative**
  (folding `0 - 5` produces `-5`).
- **`run_tests.py`** — new golden kinds `cfg`, `opt`, `o3ac`, `os`. With `-spim`, every program
  runs on SPIM **twice**, plain and `-O`.
- **Everything else** — Week 11's exercise, now fully implemented: the complete L1–L4 compiler.

### What you need to do

| Part | File | TODOs |
|---|---|---|
| A | `cfg.py` | `find_leaders()`, `add_edges()` |
| B | `opt_local.py` | `fold_value()` for `BinOp` and `RelOp`; `copy_propagation()` |
| C | `opt_cse.py` | `gen_kill()`, `available_expressions()` (the fixed-point solver) |
| D | `opt_dce.py` | `use_def()`, `liveness()` (the solver), `eliminate_dead_code()` |

### Documentation

- **`docs/optimization_reference.md`** covers:
  - why our triples shape the passes;
  - each pass's rules, including folding semantics **checked on SPIM** (`-7 / 2` is `-3`);
  - the data-flow equations, with test28's actual gen/kill/IN/OUT tables;
  - what a single-block CSE misses, and what an *unsafe* one would wrongly reuse;
  - instruction-count results, and what these passes can't do.
- **`docs/demo_runbook.md`** — the integrated demo, step by step, with expected output and
  likely questions.

### Tests

| Program | Shows | SPIM prints |
|---|---|---|
| `test26.tc` | **CFG**: `if` in `while` in `if` (Week 9's take-home shape) | `33` |
| `test27.tc` | **folding + copy propagation**: the whole program folds to 4 `PRINT`s (54 → 28 instructions) | `1480.5-3` |
| `test28.tc` | **CSE** across a branch (reused); after a change (recomputed); on one path only (*not* reused) | `27216` |
| `test29.tc` | **DCE**: dead locals removed; a global assignment and a call kept; a call blocking CSE | `4812` |
| `test_demo.tc` | the demo program (`demo/demo.tc`) | `555.5highY1` |
| every other test | `o3ac`/`os` goldens: optimized 3AC and MIPS; `-spim` runs them optimized | unchanged |

`cfg` goldens exist for `test12`, `test13`, `test16`, `test22`, `test26`–`test29`, and `test_demo`.
`opt` goldens exist for `test19`, `test26`–`test29`, and `test_demo`.

## Step by step

1. Run `python run_tests.py`. Everything from earlier weeks passes; the `cfg`, `opt`, `o3ac` and
   `os` checks fail.
2. **Part A.** Before coding, draw the CFG of `tests/test26.tc` from its `.3ac` by hand. Then
   implement `cfg.py` and test:
   ```bash
   python main.py -cfg tests/test26.tc
   python run_tests.py test12 test13 test16 test26       # cfg: ok
   ```
3. **Part B.** Implement `opt_local.py`. Test with only these two passes, comparing your report with
   the **first two sections** (up to `--- available expressions`) of
   `tests/test27.opt.expected.txt`:
   ```bash
   python main.py -optreport -passes fold,copy tests/test27.tc
   ```
4. **Part C.** Implement `opt_cse.py`. Same check with `-passes fold,copy,cse` on `test28`, up to
   `--- liveness`. Check the gen/kill/IN/OUT lines first; they are the data-flow analysis itself.
5. **Part D.** Implement `opt_dce.py`. Now everything should pass:
   ```bash
   python run_tests.py
   python run_tests.py -spim        # Linux/WSL: every program, plain AND optimized, on SPIM
   ```
6. **Experiment** (part of the write-up):
   - change `∩` to `∪` in `available_expressions()` and run `test28` with `-spim`;
   - start `OUT` at `set()` instead of the full universe, and run the loop example in
     `docs/optimization_reference.md` #3.

   Explain what you see, then change both back.
7. **Rehearse the demo** with `docs/demo_runbook.md`.

## Deliverable (final)

- The CFG builder and all four passes (`python run_tests.py -spim`, or `python run_tests.py`
  plus QtSpim checks of the optimized `.s` files).
- For **two** programs of your own (or your Week 9–11 take-homes): the `-optreport` before/after
  traces, the CFG (`-cfg`, rendered), and the MIPS instruction counts, with a short explanation of
  every change each pass made.
- The step-6 experiment write-up, including **why a single-block CSE would miss** `z = a * b` in
  `test28`'s `f`, and **why reusing `p` in `g` would be wrong**.
- The **live demo** (`docs/demo_runbook.md`), and your final compiler repository.

## Getting unstuck

- **`os: FAIL` but `o3ac: ok`**: the optimized 3AC is right, so the problem is in how it was
  edited: a stale `TripleRef`, or a deleted triple still referenced. Run `-O -compile` and compare
  the `.spim` with `tests/<name>.os.expected.txt`.
- **`spim-O: FAIL`**: your optimizer changed what the program prints. Use `-optreport` to find
  the first pass whose output differs from the golden report.
- **CSE eliminates nothing in a loop**: OUT must start as the full set of facts, not empty
  (`docs/optimization_reference.md` #3).
- **DCE removes a call, or an assignment to a global**: neither may ever be removed
  (`docs/optimization_reference.md` #4).
- **Labels or `TripleRef`s look wrong after a pass**: you edited `triples` without `compact()`;
  the pipeline does that between passes, so a pass itself should only `delete()` and
  `replace_uses()`.

If you're still stuck, post in the Week 12 GitHub Issues.
