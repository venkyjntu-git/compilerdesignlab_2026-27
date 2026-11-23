# Code Optimization Reference (Week 12)

All numbers and outputs in this file come from running the reference compiler, and every
optimized program was run on **SPIM 8.0**: `python run_tests.py -spim` runs **every** test program
twice, unoptimized and with `-O`, and checks that both print exactly the same.

**The first rule of optimization: never change what the program does.** A pass that saves
instructions but changes one output is wrong, however clever it is.

## 0. One constraint from our IR

Our 3AC is **triples**: an intermediate value has no name, only a position `(k)`, and since
Week 9 the back end assumes a triple's value lives only *inside its own statement* (it is in a
register, freed by its single consumer). Two consequences shape every pass:

- A pass may **replace** a `TripleRef` by a constant or a variable, and may **delete** triples,
  but it must never make a triple's value needed in a *later* statement.
- So CSE (#3) reuses a value from the **variable** it was assigned to (`x = a * b; ... a * b` →
  `x`), not from a temporary. Textbook CSE invents a temporary `t = a * b` instead; in triples,
  that would need a new compiler-generated variable.

After any deletion, `ir_utils.compact()` (provided) renumbers the triples and fixes every
`TripleRef`, because triple `(4)` becomes `(3)` once `(3)` is gone.

## 1. The CFG (part A)

Leaders, blocks and edges are as in Week 9 (`docs/control_flow_3ac_reference.md` there), plus
`RETURN`: it ends a block with *no* successor (it leaves the function). A `CALL` does **not** end
a block, since control comes back to the next triple. `python main.py -cfg prog.tc` writes
`prog.tc.cfg` (text, as in the goldens) and `prog.tc.cfg.dot`
(`dot -Tpng prog.tc.cfg.dot -o cfg.png`).

`tests/test26.tc` is Week 9's take-home shape, an `if` in a `while` in an `if`. Its CFG
(`tests/test26.cfg.expected.txt`) has the back edge `B6 → B2`, the inner diamond
`B3 → {B4, B5} → B6`, and an outer edge `B0 → B8` that skips the whole loop. Compare it with your
Week 9 drawing. One difference to expect: `B7` contains only the label `L2`, because two labels
in a row (`L2:` and `L0:`) each start a block.

## 2. Local passes: constant folding + copy propagation (part B)

**Constant folding** must compute exactly what SPIM would at run time. These are the rules,
checked on SPIM before being written into the code:

| Case | SPIM result | Rule |
|---|---|---|
| `-7 / 2` (int) | `-3` | truncate toward zero. **Not** Python's `//`, which gives `-4` |
| `(int)2.7`, `(int)-2.7` | `2`, `-2` | truncate (`cvt.w.d`) = Python `int()` |
| int result outside 32 bits | `add` traps | don't fold |
| `x / 0` | run-time error | don't fold: the unoptimized program must fail the same way |
| `0.1 + 0.2` | `0.30000000000000004` | Python floats *are* IEEE doubles, so fold, using `repr()` text |

Folding can produce a **negative** constant (`0 - 5` → `-5`), which the source language can't
even write. `literal_kind()` was extended this week to accept it, and `li $t0, -5` /
`li.d $f0, -2.5` work on SPIM.

**Copy propagation** works within a block: after `x = y`, later uses of `x` become `y` until `x`
or `y` changes, or a `CALL` (which may change globals) intervenes. "y" may be a constant, and that
is what makes folding *cascade* in `tests/test27.tc`:

```
a = 4;  b = a * 3 + 2;   ->   b = 4 * 3 + 2   ->   b = 14   ->   print 14   (and a, b, c, r dead)
```

The whole program becomes four `PRINT`s of constants: **54 → 28 MIPS instructions**.
Copy propagation and folding alone reach 36 (`-passes fold,copy`). Dead-code elimination then
removes the assignments to `a`, `b`, `c`, `r` that nothing reads any more.

**Why only one block?** At the start of a block (a label), control can arrive along an edge
that never executed `x = y`. Doing it across blocks safely requires a data-flow analysis, the
kind built in #3.

## 3. CSE via available expressions (part C)

A **fact** `x=a*b` means "*x holds the value of a\*b*". Facts are created by the triple pair
`(k) * a, b` / `x = (k)`. They are killed by an assignment to `a`, `b` or `x`, and by a `CALL`
if any of the three is a global.

```
FORWARD, MUST (∩):   IN[entry] = {}      IN[B] = ∩ OUT[P] over predecessors P
                     OUT[B] = gen[B] ∪ (IN[B] − kill[B])
```

`tests/test28.tc`, function `f`, from its `.opt` report:

```
B0  gen={x=a*b}  kill={}               IN={}       OUT={x=a*b}     x = a * b; if (a > b)
B1  gen={}       kill={}               IN={x=a*b}  OUT={x=a*b}     y = a * b + 1   -> x + 1
B2  gen={}       kill={}               IN={x=a*b}  OUT={x=a*b}     y = 0
B3  gen={w=a*b}  kill={x=a*b, z=a*b}   IN={x=a*b}  OUT={w=a*b}     z = a * b  -> z = x;  a = a + 1;  w = a * b
```

- **What a single-block CSE would MISS:** `z = a * b` in B3 is a recomputation only across the
  branch: B3 is entered from B1 *or* B2. Only the global analysis sees that `x=a*b` holds on both.
- **What it must NOT reuse:** in `g`, `p = a * b` happens only on the `if` path, so at `q = a * b`
  the fact `p=a*b` is in OUT of one predecessor but not the other. The intersection drops it.
  Change `∩` to `∪` (a *may* analysis) and `g(2, 3)` returns `0` instead of `6`: the
  program's output changes on SPIM, and `run_tests.py -spim` reports `spim-O: FAIL`. (This mutant
  was actually run.)
- **Why start OUT at the full set?** With a loop, a block's predecessors include the loop's own
  end, which hasn't been computed yet on the first sweep. Starting from "everything is
  available" lets the iteration *remove* what isn't, rather than never discovering what is. In
  this loop (run both ways):

  ```
  x = a * b;
  while (i < n) { y = y + a * b; i = i + 1; }
  ```

  the full start finds `a * b` available in the loop body (1 eliminated). The empty start ends at
  `IN = {}` for the loop header and eliminates nothing. Both are *safe*, but only one is useful.

## 4. Dead code elimination via liveness (part D)

```
BACKWARD, MAY (∪):   OUT[B] = ∪ IN[S] over successors S     (no successors: all globals)
                     IN[B]  = use[B] ∪ (OUT[B] − def[B])
```

An assignment to a **local** that is dead right after it is removed, together with the pure
computation that fed it. Removing one can make an earlier one dead, so the pipeline repeats until
a round removes nothing. Three things are never removed (all in `tests/test29.tc`):

- **assignments to globals**: another function, or the caller after `return`, may read them;
- **calls**: `x = compute(0);` with `x` dead loses the assignment, but the call stays
  (`CALL compute, 1 : INT (result unused)`), because it changes `total`. A DCE that deletes the
  call too prints `11` instead of `12` (mutant run on SPIM);
- **anything a call might read**: a `CALL` *uses* every global.

`test29` also shows a call stopping CSE: `k = total * 2; bump(); m = total * 2;` keeps both
multiplications, because `bump()` may change `total`.

## 5. What the passes buy, and what they don't

Static MIPS instruction counts (`-optreport`'s last line), all tests:

| Program kind | Examples | Fewer instructions |
|---|---|---|
| straight-line, values known at compile time | `test6`, `test7`, `test8`, `test_regpressure`, `test27` | 48–64% |
| straight-line with some unknowns | `test4`, `test5`, `test9`, `test_mixedcmp` | 17–49% |
| control flow / functions with dead or reusable code | `test10`, `test11`, `test17`, `test26`, `test28`, `test29` | 5–15% |
| loops and functions where every value changes | `test12`, `test14`–`test16`, `test20`–`test22`, `test24` | 0% |

The last row is not a bug. These four passes can't touch a loop whose every variable changes on
every iteration. The classic next steps are:
- **loop-invariant code motion** (move `a * b` *out* of a loop);
- **branch folding** (`if_false 1 goto L` → nothing);
- **unreachable-code elimination**;
- **register allocation** that keeps variables in registers instead of reloading them every
  time; most of our instructions are such `lw`/`sw`.

Also keep in mind that these are **static** counts. A loop body that runs 1000 times weighs 1000
times more at run time than its line count suggests.
