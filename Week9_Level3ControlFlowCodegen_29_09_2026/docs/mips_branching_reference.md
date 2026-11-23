# MIPS Branching Reference (Week 9)

Everything in this file was checked by running the generated code on **SPIM 8.0**. Every golden
`tests/*.spim_output.expected.txt` was recorded from a real SPIM run.

## 1. The instructions you need

| 3AC | MIPS | Notes |
|---|---|---|
| `L0:` | `L0:` | same name: a 3AC label becomes a MIPS label |
| `goto L0` | `j L0` | unconditional jump |
| `if_false c goto L0` (int/char `c`) | `beq $t0, $zero, L0` | jump when the condition register equals 0 |
| `if_false c goto L0` (double `c`) | `li.d $f2, 0.0` / `c.eq.d $f0, $f2` / `bc1t L0` | see #2 |

The rest of the branch family, so you can read the generated code:

| Instruction | Branches when | Real or pseudo? |
|---|---|---|
| `beq r1, r2, L` / `bne r1, r2, L` | `r1 == r2` / `r1 != r2` | real |
| `blt` / `bgt` / `ble` / `bge r1, r2, L` | `<` / `>` / `<=` / `>=` | **pseudo**: SPIM expands each to `slt` + `bne`/`beq` using `$at` |
| `b L` | always | pseudo for `beq $zero, $zero, L` |
| `j L` | always | real (jump, not branch) |
| `bc1t L` / `bc1f L` | FPU condition flag true / false | real; the flag is set by `c.eq.d`, `c.lt.d`, `c.le.d` |

`$zero` is register 0, which always reads as 0, so `beq $t0, $zero, L` means "if `$t0` is 0".

## 2. A double condition (`if (d)`, `while (d)`)

There is no "branch if this double is zero" instruction. Compare it with 0.0, held in a second FPU
register, then branch on the FPU's condition flag:

```mips
li.d   $f2, 0.0
c.eq.d $f0, $f2       # flag := (d == 0.0)
bc1t   L2             # flag true  ->  d is zero  ->  condition FALSE  ->  jump
```

`bc1t` is right here because `if_false` jumps when the condition is false. Week 7's `gen_select()`
tests a double condition the same way but uses `bc1f`, because the ternary jumps to its
then-value when the condition is true. Test with `tests/test15.tc`, which exercises both a
non-zero and a zero double condition and prints `40.625nonzerozero`.

## 3. Label numbering: 3AC labels first, then the back end's own

The back end still invents labels of its own: each comparison materializes 0/1 with a
`Ltrue`/`Lend` pair (Week 7), and so does each ternary. To keep these from colliding with the
3AC's labels, `MIPSGenerator` (provided) **starts its own numbering after the 3AC's**. In
`tests/test12.tc` the 3AC uses `L0` and `L1`, so the comparison inside the loop condition gets
`L2` and `L3`:

```mips
    L0:                        # 3AC: loop top
    lw $t0, 4($fp)             # i
    lw $t1, 0($fp)             # n
    ble $t0, $t1, L2           # back end's own label: comparison is true
    li $t2, 0
    b L3
    L2:
    li $t2, 1
    L3:                        # $t2 = (i <= n) as 0/1
    beq $t2, $zero, L1         # if_false (4) goto L1   -- leave the loop
    ...                        # loop body
    j L0                       # goto L0                -- the back edge
    L1:                        # 3AC: loop exit
```

A program with no `if`/`while` has no 3AC labels, so its `.s` numbering is unchanged from Week 7.

## 4. Globals live in `.data`, as `g_<name>`

A local is at an offset from the frame pointer, such as `lw $t0, 4($fp)`. A global has no frame,
so it gets a fixed, labelled slot in `.data`, and is read and written by label:

```mips
.data
g_a: .word 0
g_b: .word 0
.align 3              # a double must sit on an 8-byte boundary
g_c: .double 0.0
.text
    ...
    lw  $t0, g_a      # pseudo-instructions: SPIM expands each to lui + lw/sw via $at
    sw  $t0, g_b
    s.d $f0, g_c
```

`MIPSGenerator.address(name)` (provided) returns `4($fp)` for a local and `g_name` for a global.
`load()` and `store_to_var()` use it, so your new methods never need to care where a variable
lives.

**Why the `g_` prefix?** Slide 6's Example 3 declares a global named `b`, and `b` is a MIPS
mnemonic (branch). Emitting the label as-is, as `b: .word 0`, is rejected by SPIM:

```
spim: (parser) syntax error on line 3 of file noprefix.s
	  b: .word 0
	   ^
```

The prefix also keeps globals apart from the back end's `L…` and `Lstr…` labels.

## 5. Why straight-line register allocation still works with jumps

The allocator hands out `$t0`–`$t9` / `$f0`–`$f30` in the order the code is *written*, but jumps
mean the code no longer *runs* in that order. This is still safe, because of an invariant:

> **No temporary register holds a live value at the end of any statement, and so none is live at
> any label.**

Every temporary is created and consumed within a single statement's triples, and labels only
ever appear *between* statements. Whichever path reaches a label, no register's contents matter
at that point, so the allocator's bookkeeping is correct on every path.

That invariant is why this week's provided `tac_to_mips.py` **changes one Week 7 rule**. A
register is now freed by the triple that *consumes* it, also when it was reached through a
`TripleRef`. Week 7 only freed freshly-loaded registers, so every `TripleRef` leaked a register
until the end of the function. `tests/test_regpressure.tc`, a single six-term expression, used up
all ten `$t` registers and crashed the Week 7 back end with `ValueError` in `alloc_int()`; loop
bodies hit that limit quickly. 3AC generated from an AST uses every triple's result exactly once,
so freeing on consumption is safe. The register numbers in the Level 2 `.s` goldens changed as a
result, and their SPIM output did not.

## 6. Running your code on SPIM

```bash
python main.py -compile tests/test12.tc      # writes tests/test12.tc.spim
spim -file tests/test12.tc.spim              # Linux / WSL: sudo apt install spim
```

SPIM prints its banner, up to a `Loaded: .../exceptions.s` line, and then your program's output:
`55`. On Windows, load the `.spim` file in **QtSpim** (File → Reinitialize and Load File, then
Run), or use WSL. With the command-line `spim` installed, `python run_tests.py -spim` also runs
every test on SPIM and compares what it prints with `tests/*.spim_output.expected.txt`.

`print` writes no newline, so several prints run together, for example `test13` prints `20`
(meaning `2`, then `0`). Read the `.tc` file to split them up.

## 7. Optional extra: a wasted instruction pattern

Look at the loop condition in #3. It takes **seven** instructions (plus two labels) to compute
`i <= n` as a 0/1 value and then test that value against zero. One instruction could do the same
job directly:

```mips
    lw  $t0, 4($fp)
    lw  $t1, 0($fp)
    bgt $t0, $t1, L1           # leave the loop when NOT (i <= n)
```

Fusing a comparison with the `if_false` that consumes it is a classic small optimization, and one
reason this week's lab plan lists `blt`/`bge` among the branch instructions. For extra credit:
when a `RelOpTriple` is immediately followed by an `IfFalseTriple` whose condition refers to it,
emit nothing for the comparison and let `gen_iffalse()` emit the *negated* branch (`<=` becomes
`bgt`, `==` becomes `bne`, and so on). This needs a one-triple lookahead, because `gen_relop()`
runs before `gen_iffalse()` sees it. Afterwards, `run_tests.py -spim` will report `s: FAIL`, since
your `.s` now differs from the goldens, but every `run-on-spim` must still say `ok`. Leave this
until everything else passes; Week 12's optimization passes return to this kind of saving.
