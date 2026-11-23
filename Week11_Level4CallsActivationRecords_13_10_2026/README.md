# Week 11 — Level 4: Activation Records and the Full MIPS Calling Convention

Last week the front end learned functions: parameters, prototypes, calls, `return`, and their
semantic checks. `-3ac`/`-compile` still stopped with *"planned for Week 11"*. This week, calls go
through **the whole pipeline**, down to MIPS code that SPIM runs: `jal`/`jr $ra`, arguments in
`$a0`–`$a3` and on the stack, results in `$v0`/`$f0`, and a **stack frame (activation record)**
for every call, so that even recursion works. At the end of this week you have the **complete
L1–L4 TinyCStr compiler**.

## What we're trying to do this week

1. **Activation records**: the stack frame layout, `$sp`/`$fp`, and the calling convention:
   `$a0`–`$a3` for the first four (int-family) arguments, `$v0` for an int result, `$ra` via
   `jal`/`jr`, and which registers the caller and the callee must save.
2. **3AC**: `PARAM`, `CALL` and `RETURN`. **MIPS**: the call sequence, parameter homing in the
   prologue, and `return` jumping to the epilogue.
3. **Run on SPIM**: Example 4 (Slide 7, corrected), the Week 10 test programs, and Week 10's
   take-home programs, checking that arguments arrive and results come back.

## Current file contents

### What's already provided (do not modify)

- **`calling_convention.py`** — **new**: the convention as code, the single place that caller and
  callee agree on:
  - `arg_locations()`: which argument goes to which register or stack slot;
  - `function_label()` / `return_label()`.
- **`three_address_code.py`** — **changed**: `ParamTriple`, `CallTriple`, `ReturnTriple`.
- **`Function.py`** — **changed**: `layoutFrame()` assigns every local and parameter its offset
  from `$fp` (the picture in `docs/activation_records.md` #1).
- **`Program.py`** — **changed**: label numbers continue across functions; `compile()` produces one
  `.s` file for the whole program.
- **`tac_to_mips.py`**, provided this week:
  - one generator per function, with a shared `ProgramContext` (one string pool, no duplicate
    labels);
  - `lookup()` through locals → parameters → globals;
  - `gen_param()`;
  - function labels, and the epilogue label that `return` jumps to;
  - `live_registers()`, for saving temporaries across a call.
- **`tac_generator.py`** — the label counter continues across functions; Levels 1–3 complete.
- **`type_checker.py`** — Week 10's exercise, now fully implemented, plus one line: a call records
  its callee's declared return type (`node.return_type`).
- **`tinycstr_lexer.py`, `tinycstr_parser.py`** — Week 10's exercise, fully implemented.
- **`main.py`** — **changed**:
  - Week 10's "planned for Week 11" gate is removed;
  - `-3ac` prints one block per function;
  - `-compile` writes the whole program.

### What you need to do

| File | TODO | |
|---|---|---|
| `tac_generator.py` | `gen_call()` | arguments first, then `PARAM`s, then `CALL` |
| `tac_generator.py` | `gen_return()` | `RETURN` |
| `tac_to_mips.py` | `emit_home_params()` | prologue: store `$a0`–`$a3` into the frame |
| `tac_to_mips.py` | `gen_call()` | **the call sequence**: save, arguments, `jal`, result, restore |
| `tac_to_mips.py` | `gen_return()` | result into `$v0`/`$f0`, jump to the epilogue |

### Documentation

- **`docs/activation_records.md`** — start here. It covers:
  - the frame picture, the prologue/epilogue, and why arguments are homed;
  - the full convention (and how it simplifies MIPS O32);
  - the call sequence, step by step, on real generated code, with *why the order matters*;
  - caller-saves vs. callee-saves;
  - the label scheme, and why SPIM rejects an unprefixed `add:`.
- **`docs/calls_3ac_reference.md`** covers:
  - the three triples and the translation scheme;
  - what goes wrong if a `PARAM` is emitted before all arguments are evaluated;
  - `fib`'s 3AC;
  - multi-function `-3ac` output.

### Tests

Every `.spim_output.expected.txt` was recorded by running the reference compiler's output on
**SPIM 8.0** and checked against a hand computation.

| Program | What it exercises | SPIM prints |
|---|---|---|
| `test17.tc` | a `void` function, no parameters; separate locals named `x` | `25251` |
| `test19.tc` | **Example 4, corrected**: globals, `int` and `double` functions, `double` arguments on the stack | `-50` |
| `test20.tc` | an `int` argument converted to a `double` parameter; a call as an argument | `4924.516` |
| `test21.tc` | global vs. local `count`; `void` `return;`; `return` from inside a loop | `1004` |
| `test22.tc` | **recursion**: `fact`, and `fib`, whose first result must survive the second call | `12055` |
| `test23.tc` | **6 arguments** (two on the stack), `double` arguments, temporaries saved across calls, including one in `$f0` | `51921` |
| `test24.tc` | `string`/`char` parameters and results; a call in a loop condition; a `void` function | `FPzeron=3` |
| `test25.tc` | **Week 10's take-home**: loop-based `factorial`, `min`/`max`; arguments are passed by value | `72065` |
| `test4`–`test16`, ... | **regression**: Level 1–3 programs, same output as before | |

`print` writes no newline, so `25251` means `25`, `25`, `1`.

## Step by step

1. Read `docs/activation_records.md` #1–#2. Then, **on paper**, draw the stack at the moment
   `fact(1)` starts executing in `tests/test22.tc` (`main` → `fact(5)` → ... → `fact(1)`): every
   frame, its saved `$fp`/`$ra`, and its `n`. Keep the drawing; it is part of the deliverable.
2. Run `python run_tests.py`. Level 1–3 tests pass, and the Level 4 ones fail at `3ac` with
   `NotImplementedError`.
3. Read `docs/calls_3ac_reference.md`, then implement `gen_call()` and `gen_return()` in
   `tac_generator.py`. Test the `.3ac` files: `python run_tests.py test17 test19 test22`.
4. Implement `gen_return()` and `emit_home_params()` in `tac_to_mips.py`, then the simple cases
   of `gen_call()`: no saves, register arguments only (steps 2–4 of its docstring). Test
   `test17`, `test19`, `test20`, `test22`.
5. Read `docs/activation_records.md` #3–#4, then finish `gen_call()`: stack arguments, saving and
   restoring live temporaries (steps 1 and 5). Test `test23`. It fails in a characteristic way if
   steps 4 and 5 are in the wrong order; try it.
6. **Run everything on SPIM**: `python run_tests.py -spim` (Linux/WSL with `spim`). With QtSpim,
   load each `tests/<name>.tc.spim` and compare against the table above.

## Take-home (due at the start of Week 12's lab)

The lab plan asks for a function with "more local variables than fit comfortably in registers,
forcing a stack-resident local". In this compiler **every** local already lives in the stack
frame (`docs/activation_records.md` #6). So instead, stress the parts of the convention that
*can* run out:

Write a TinyCStr program with a function that has **at least six parameters** (so that some are
passed on the stack), at least one of them `double`, **and** at least five locals. Call it from
`main` inside an expression that keeps another value live across the call, for example
`r = k * 2 + f(...)`, and call it once more with one of its arguments being *another call*.
Then:

1. predict the exact output by hand;
2. compile it, and mark in the generated `.s` where each argument is placed, where the callee
   reads each parameter, and where the live value is saved and restored;
3. run it on SPIM and confirm the output matches your prediction.

**Deliverable:**
- the complete L1–L4 compiler: `python run_tests.py -spim` all PASS, or every output checked by
  hand on QtSpim;
- your stack drawing for `fact(1)`;
- the annotated, SPIM-verified take-home program.

## Getting unstuck

- **SPIM: `Attempt to execute non-instruction`, or it jumps somewhere strange**: the stack is
  unbalanced. Every `subu $sp` in `gen_call()` needs a matching `addiu $sp` (argument area and
  saved registers).
- **A parameter's value is wrong inside the callee**: check `emit_home_params()`. Then check that
  the caller put argument *i* in `$a`*i* by **position**: `f(int, double, int)` uses `$a0` and
  `$a2`.
- **Recursion returns the right value once, then garbage**: something live across the recursive
  call isn't being saved. `fib`'s first result is the classic case (`docs/activation_records.md`
  #4).
- **`y` in `test23` is 3 instead of 9**: you restored the saved registers before copying the result
  out of `$f0`.
- **An infinite loop on SPIM after a function returns**: `return` must `j ret_<name>`, and the
  epilogue must restore `$ra` before `jr $ra`. `$ra` is overwritten by every `jal`, which is why
  the prologue saves it.

If you're still stuck, post in the Week 11 GitHub Issues.
