# Week 9 — Level 3: Control-Flow Three-Address Code and MIPS Branching

Last week the parser learned `if`, `if-else`, `while`, blocks and global declarations, but
`-3ac`/`-compile` stopped with *"planned for Week 9"*. This week, Level 3 programs go through
**the whole pipeline**: AST → 3AC with **labels and jumps** → MIPS **branches** → running on SPIM.
By the end of the week you have a complete L1 + L2 + L3 compiler.

## What we're trying to do this week

1. **3AC with labels and jumps.** Turn `If` / `While` / `Block` statements into the three
   control-flow triples (`Label`, `Goto`, `IfFalse`), using a fresh-label allocator.
2. **The control-flow graph (CFG), by hand, first.** Before coding, draw the CFG of the `while`
   program `tests/test12.tc`. This connects the textbook CFG to the 3AC you're about to generate.
3. **MIPS branching.** Map labels and jumps to MIPS labels, `j`, and `beq` (plus the FPU's
   `c.eq.d`/`bc1t` for a `double` condition). Then run every Week 8 program on SPIM.

## Current file contents

### What's already provided (do not modify)

- **`tinycstr_lexer.py`, `tinycstr_parser.py`** — **Week 8's exercise, now fully implemented**:
  the reference Level 3 lexer and parser.
- **`three_address_code.py`** — **changed this week**: three new triples, `LabelTriple`,
  `GotoTriple`, and `IfFalseTriple(cond, cond_type, label)`.
- **`tac_to_mips.py`** — **changed this week**. Everything except your three TODOs is provided:
  - **Globals** live in `.data` as `g_<name>` (Example 3's global `b` would otherwise be a SPIM
    syntax error; `b` is an instruction).
  - Back-end labels are numbered after the 3AC's, so they never collide.
  - **A register-freeing fix**: Week 7's back end leaked a register per `TripleRef` and crashed on
    one 6-term expression (`tests/test_regpressure.tc`). See `docs/mips_branching_reference.md`
    #5; the Level 2 `.s` goldens changed register numbers, but print the same on SPIM.
- **`Function.py`, `Program.py`** — **changed**, small: the global symbol table now reaches the
  back end.
- **`main.py`** — **changed**: Week 8's "planned for Week 9" gate is removed.
- **`run_tests.py`** — **changed**: new **`-spim`** flag. If the command-line `spim` is installed,
  it runs each generated `.s` and checks what the **program prints**, not just the assembly text.
- **`type_checker.py`** — one-line **fix**: a `Cast` the checker inserts now carries its own
  `result_type`. Without it, a mixed comparison such as `i < 2.5` crashed 3AC generation
  (`tests/test_mixedcmp.tc`).
- **`ast_nodes.py`, `SymbolTable.py`, `type_rules.py`** — unchanged.

### What you need to do

- **`tac_generator.py`**:
  - `new_label()`: the fresh-label allocator.
  - `gen_block()`.
  - `gen_if()`: both forms, with and without `else`.
  - `gen_while()`.
- **`tac_to_mips.py`**:
  - `gen_label()`.
  - `gen_goto()`.
  - `gen_iffalse()`: an `int`/`char` condition and a `double` condition.

### Documentation

- **`docs/control_flow_3ac_reference.md`** covers:
  - the three new triples, and why the IR jumps on *false*;
  - the exact translation scheme for `if`, `if-else`, `while` and blocks;
  - the **label-order convention** the goldens depend on;
  - why the ternary still isn't lowered to jumps;
  - how to find basic blocks and draw a CFG, with a worked example (`test10`).
- **`docs/mips_branching_reference.md`** covers:
  - the branch instructions, and which are pseudo-instructions;
  - testing a `double` condition;
  - label numbering, and globals in `.data`;
  - **why straight-line register allocation still works with jumps**;
  - running on SPIM;
  - an optional extra-credit optimization.

### Tests

Every test with a `.spim_output.expected.txt` was compiled by the reference compiler and **run on
real SPIM (8.0)**; the expected output was recorded from that run and checked by hand.

| Program | What it exercises | SPIM prints |
|---|---|---|
| `test10.tc` | `if` (no else), around one statement and around a block | `110` |
| `test11.tc` | **Example 3 (Slide 6), corrected**: globals in `.data` + `if-else` + casts | `1.25` |
| `test12.tc` | `while`, sum of 1..10 — **draw its CFG first** | `55` |
| `test13.tc` | dangling else: nested `if` inside `if`, labels inside labels | `20` |
| `test14.tc` | globals (`double`, `string`), `while`, `else if` chain | `25medium` |
| `test15.tc` | **double** conditions: `while (d > 1.0)`, `if (d)` both non-zero and zero | `40.625nonzerozero` |
| `test16.tc` | a `while` nested in a `while`; a loop that never runs; empty blocks | `254` |
| `test_regpressure.tc` | 11 temporaries in one statement — the register-freeing fix | `36` |
| `test_mixedcmp.tc` | `int` vs `double` comparisons (an inserted `Cast` as a comparison operand) | `1171.5` |
| `test4`–`test9` | **regression**: Level 2 programs, same SPIM output as Week 7 | |
| `test_errors`, `test_l3_errors` | type errors still stop the pipeline before 3AC | |

`print` writes no newline, so `20` means `2` and then `0`.

## Step by step

1. Run `python run_tests.py` before changing anything. Level 1/2 tests pass, and Level 3 tests
   fail at `3ac` with `NotImplementedError`.
2. **Draw the CFG of `tests/test12.tc` on paper.** First write down its 3AC by hand, using the
   `while` scheme in `docs/control_flow_3ac_reference.md`. Then mark the leaders, box the basic
   blocks, and draw the edges. Which edge goes backwards, and which triple creates it? Keep the
   drawing; it is part of the deliverable, and you'll compare it with a generated CFG in Week 12.
3. Implement `new_label()` and `gen_block()`, then `gen_while()`. Test:
   ```bash
   python main.py -3ac tests/test12.tc
   python run_tests.py test12
   ```
   Compare `tests/test12.tc.3ac` with the 3AC you wrote by hand in step 2.
4. Implement `gen_if()`: first without `else` (`test10`), then with `else` (`test11`, `test13`).
   Watch the label order in `test13`'s nested `if`s.
5. Implement `gen_label()`, `gen_goto()`, then `gen_iffalse()` for an int condition. Test the
   `.s` with `python run_tests.py test10 test11 test12 test13`.
6. Add the `double` case of `gen_iffalse()` and test with `test15`.
7. **Run everything on SPIM.** On Linux/WSL (`sudo apt install spim`):
   ```bash
   python run_tests.py -spim
   ```
   With QtSpim on Windows, load each `tests/<name>.tc.spim` and check its output against the
   table above. Every line must be PASS, including the Level 2 regression tests.

## Take-home (due at the start of Week 10's lab)

Write a TinyCStr program with an **`if` nested inside a `while` nested inside an `if`** (three
levels), with at least one `else` somewhere. Then:

1. Hand-trace it: write down the value of every variable after each loop iteration, and the
   exact output you expect.
2. Compile it, run it on SPIM, and confirm the output matches your hand trace. If it doesn't,
   find out whether your trace or your compiler is wrong, and say which.
3. Draw its CFG from the generated `.3ac`.

**Deliverable:** the complete L1 + L2 + L3 compiler (`python run_tests.py -spim` all PASS, or all
outputs checked by hand on QtSpim); CFG diagrams for `test12.tc` and your take-home program; and
the SPIM-verified take-home program with its hand trace.

## Getting unstuck

- **An infinite loop on SPIM**: the `goto` at the end of a `while` must jump to `Ltop`, placed
  *before* the condition code. If `Ltop` is placed after the condition, the condition is never
  re-evaluated.
- **The then-branch also runs the else-branch**: you're missing the `goto Lend` after the
  then-branch.
- **The `.3ac` is right but the labels are numbered differently**: allocate all of a
  statement's labels before generating its condition and branches (the label-order convention).
- **`if (d)` behaves backwards for a double**: `gen_iffalse()` needs `bc1t` (jump when `d == 0.0`
  is true), not `bc1f`.

If you're still stuck, post in the Week 9 GitHub Issues.
