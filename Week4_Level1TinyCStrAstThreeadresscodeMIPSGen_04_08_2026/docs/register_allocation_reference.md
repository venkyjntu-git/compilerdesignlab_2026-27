# Register Allocation Reference (Week 4)

This week's `tac_to_mips.py` builds directly on
`practice_examples/5_practice_examples_MIPS/tac_to_mips.py` ("Lab Practice 5") — read that
file and its `README.md` first if you haven't already; this document only covers what's
*different* here.

## The strategy, recapped

Ten scratch registers, `$t0`–`$t9`, tracked as a simple available/unavailable list.
`allocate_registers()` hands out the first free one; `deallocate_register()` frees it again.
When a triple's result is computed, the register holding it is recorded in
`triple_index_to_reg[triple.index]` — so when a *later* triple references that result via a
`TripleRef`, it reuses that register directly, **no reload from memory at all**. Only real
variables and literals ever go through `load()` (a `lw`/`li`).

## What's different from the practice example

**Real addresses, not a placeholder.** The practice example's `load()`/`store()` wrote
`disp($fp)of<name>` — its own README (section 6) explicitly calls this "a teaching placeholder,
not actual MIPS assembly syntax," with section 10 ("Home Work Extension") describing exactly
this week's task: replace it with a real offset from a symbol table. `SymbolTable.py`'s
`assignOffsetsToSymbols()` (already implemented) does the offset computation;
`resolve_address()` here is where you look it up and format it as real MIPS (`f"{offset}($fp)"`).

**`PrintTriple` is handled.** The practice example's one demo program (`x = (a+b)*(c-d)`) never
printed anything. Every TinyCStr program does. Resolve the operand the same way as any other
(`TripleRef` → reuse register; literal/variable → `load()`), then `move $a0, reg` / `li $v0,1` /
`syscall`.

**A real prologue/epilogue wraps the whole function**, per the
[Frame-based Linkage Convention](https://chortle.ccsu.edu/AssemblyTutorial/Chapter-28/ass28_06.html)
— see `docs/mips_spim_reference.md`. The practice example had no function/frame concept at all.
One consequence: `frame_size` is now `symbol_table.size()` **only** — just the declared
variables — because triple results live in registers this week, not in their own stack slots.
There's no separate "temporary displacement" bookkeeping to do at all (an earlier draft of this
material had exactly that, in a `frame_layout.py` module — it's gone this week, precisely
because register-based triples don't need it).

## Worked example: `c = a + b*a + a*a;`

Triples (from `tac_generator.py`, unchanged):
```
(0) a = 5
(1) b = 5
(2) * b, a
(3) + a, (2)
(4) * a, a
(5) + (3), (4)
(6) c = (5)
(7) PRINT c
```

Walking `(2)` through `(6)` (skipping the two plain assignments):

| Triple | What happens | Register state after |
|---|---|---|
| `(2) * b, a` | fresh-load `b`→`$t0`, fresh-load `a`→`$t1`, `mul $t2,$t0,$t1`, record `(2)→$t2`, free `$t0`,`$t1` | `$t2` live (triple 2's result) |
| `(3) + a, (2)` | fresh-load `a`→`$t0`; `(2)` is a `TripleRef` → reuse `$t2` directly, **no load**; `add $t1,$t0,$t2`; record `(3)→$t1`; free `$t0` (fresh) | `$t1` live (triple 3's result); `$t2` still marked used |
| `(4) * a, a` | fresh-load `a`→`$t0`, fresh-load `a`→`$t3` (`$t2` still unavailable), `mul $t4,$t0,$t3`, record `(4)→$t4`, free `$t0`,`$t3` | `$t1`,`$t4` live |
| `(5) + (3), (4)` | both are `TripleRef`s → reuse `$t1` and `$t4` directly, no loads; `add $t0,$t1,$t4` (allocator picks `$t0`, the lowest free index); record `(5)→$t0` | `$t0` live |
| `(6) c = (5)` | `(5)` is a `TripleRef` → reuse `$t0`; `sw $t0, 8($fp)`; **`store()` always frees its register**, so `$t0` is freed here | none live |


## A known limitation: some registers "leak" until reused elsewhere

Look closely at the trace above: after triple `(3)` consumes `(2)`'s value (in `$t2`), nothing
ever explicitly frees `$t2` — it stays marked unavailable even though triple `(2)`'s result is
never needed again. The same happens to `$t1` and `$t4` after triple `(5)` consumes them. This
is a direct consequence of the simple allocator only freeing a register in two places:
`store()` (always) and the "was this operand freshly loaded this call" check in `gen_instr()`
(never for a reused `TripleRef`). A `TripleRef`'s register is only ever freed if it's later
consumed by an `AssignTriple` — never just because nothing will reference it again.

**This does not break Level 1's programs** — with only 10 registers and TinyCStr(L1) programs
using at most a handful of triples per function, the leak never accumulates far enough to run
out. It *would* become a real problem for a long enough expression chain (eventually
`allocate_registers()` would raise `RuntimeError("Registers are not available")`). Matching the
practice example's own framing (its README section 9: "a simple approach... not a complete
register allocator"), this is left as-is rather than fixed — a natural discussion point, and a
reasonable stretch goal, would be tracking each triple's *last use* and freeing its register
eagerly at that point instead of only at assignment time.
