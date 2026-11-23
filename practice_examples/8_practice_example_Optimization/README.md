# Lab Practice 8 - Code Optimization on the Control-Flow Graph

This exercise takes the three-address code and CFG of **practice 6** and improves the code with
four classic optimizations:

| # | Optimization | Works on | Needs |
|---|---|---|---|
| 1 | constant folding | one triple | — |
| 2 | copy propagation | one basic block | — |
| 3 | common subexpression elimination (CSE) | the whole CFG | **available expressions** (data-flow analysis) |
| 4 | dead code elimination (DCE) | the whole CFG | **liveness** (data-flow analysis) |

It supports Week 12. `ExprAstLexer.py`, `ast_nodes.py`, `three_address_code.py`,
`tac_generator.py` and `cfg.py` are the same as in practice 6. The new files are
`optimizer.py` and `interpreter.py`.

Run it:

```text
python ExprAstParser.py
```

---
# 1. The Example Program

```text
a = 4;
b = a * 2;              // folding + copy propagation: b = 8
c = x * y;
unused = c + 1;         // dead: never read
if (x > b) {
    d = x * y;          // x * y is available (in c): reuse
} else {
    d = 0;
}
e = x * y;              // available on BOTH paths: reuse
x = x + 1;
f = x * y;              // x changed: NOT available, recompute
print d + e + f + b;
```

`x` and `y` are never assigned: think of them as **inputs** whose values the compiler doesn't
know. Its CFG has four blocks: `B0` (everything up to the `if`), `B1` (then), `B2` (else), and
`B3` (after the `if`).

---
# 2. The One Rule

> **An optimization must never change what the program prints.**

`interpreter.py` runs the triples directly. The program is run before and after optimization,
with inputs that take *both* branches of the `if`:

```text
inputs {'x': 3, 'y': 5}:   before [43]   after [43]   same
inputs {'x': 20, 'y': 2}:  before [130]  after [130]  same
triples: 25 before, 18 after
```

---
# 3. Constant Folding

If both operands of a triple are constants, compute it **now** and use the result instead:

```text
(1) * 4, 2      ->  8          every use of (1) becomes 8, and (1) is deleted
```

Folding must give exactly the value the program would compute when it runs. For integer
division that means truncating toward zero, as MIPS does: `-7 / 2` is `-3` (Python's `//` would
give `-4`). Division by zero is **not** folded; the program fails at run time, exactly as it
would without optimization.

---
# 4. Copy Propagation

After `b = 8`, later uses of `b` **in the same block** can use `8` directly, until `b` is assigned
again:

```text
(0) a = 4              (0) a = 4
(1) * a, 2       ->    (1) * 4, 2   -> folded: b = 8
(2) b = (1)
(7) > x, b             (6) > x, 8
```

Folding and copy propagation feed each other (`a = 4` lets `a * 2` fold, which lets `b`
propagate), so they are repeated until nothing changes.

**Why only one block?** In `print d + e + f + b` (block `B3`), `b` is *not* replaced by `8`,
although that would be correct here. `B3` can be reached from two blocks, and a local pass can't
know that `b = 8` holds on every path into it. Proving that is the job of a *data-flow analysis*,
like the two that follow.

---
# 5. Common Subexpressions - Available Expressions

A **fact** `c=x*y` means "*the variable `c` holds the value of `x * y`*". It is

- **created** by `c = x * y`;
- **killed** by any assignment to `c`, `x` or `y` (after `x = x + 1`, `c` no longer equals `x * y`).

An expression is **available** at the start of a block if it holds on **every** path into the
block. This is a forward data-flow analysis:

```text
IN[B]  = intersection of OUT[P] over all predecessors P        (IN of the first block = {})
OUT[B] = gen[B] ∪ (IN[B] - kill[B])
```

Repeat over all blocks until nothing changes. The program prints the result:

```text
B0  gen={c=x*y, unused=c+1}  kill={}                       IN={}                   OUT={c=x*y, unused=c+1}
B1  gen={d=x*y}              kill={}                       IN={c=x*y, unused=c+1}  OUT={c=x*y, d=x*y, unused=c+1}
B2  gen={}                   kill={d=x*y}                  IN={c=x*y, unused=c+1}  OUT={c=x*y, unused=c+1}
B3  gen={f=x*y}              kill={c=x*y, d=x*y, e=x*y}    IN={c=x*y, unused=c+1}  OUT={f=x*y, unused=c+1}
```

So at the start of `B1` and of `B3`, `x * y` is available, held in `c`:

```text
d = x * y   ->   d = c          (B1)
e = x * y   ->   e = c          (B3: available from BOTH B1 and B2)
f = x * y   stays               (x = x + 1 just killed c=x*y)
```

- **Why "intersection"?** `d=x*y` is in `OUT[B1]` but not in `OUT[B2]`. Coming through the else
  branch, `d` holds `0`, so `IN[B3]` must not contain `d=x*y`. Requiring a fact on *every* path
  is what makes the optimization safe.
- **Why start every OUT at "all facts"?** With a loop, a block's predecessor may not have been
  computed yet. Starting with "everything is available" and removing what isn't finds the most
  reuse; starting from `{}` is safe too, but misses reuse inside loops.

---
# 6. Dead Code - Liveness

A variable is **live** at a point if some path from there **reads** it before writing it again.
An assignment to a variable that is not live right after it is **dead** and can be removed.
Liveness is computed **backward**, from the end of the program:

```text
OUT[B] = union of IN[S] over all successors S          (nothing is live at the end)
IN[B]  = use[B] ∪ (OUT[B] - def[B])
```

- `use[B]`: variables read in `B` before being written there.
- `def[B]`: variables written in `B`.

The program prints the result:

```text
B0  use={x, y}            def={a, b, c, unused}  IN={x, y}            OUT={b, c, x, y}
B1  use={c}               def={d}                IN={b, c, x, y}      OUT={b, c, d, x, y}
B2  use={}                def={d}                IN={b, c, x, y}      OUT={b, c, d, x, y}
B3  use={b, c, d, x, y}   def={e, f, x}          IN={b, c, d, x, y}   OUT={}
```

Walking each block backward from `OUT`:
- `unused` and `a` are not in `OUT[B0]`, and not read later in `B0`: **dead**, removed.
- `e = c` is dead too. After CSE, copy propagation turned `+ d, e` into `+ d, c`, so nothing reads
  `e` any more.

The final program has 18 triples instead of 25:

```text
(0) b = 8                 (9)  L1:
(1) * x, y                (10) + x, 1
(2) c = (1)               (11) x = (10)
(3) > x, 8                (12) * x, y
(4) if_false (3) goto L0  (13) f = (12)
(5) d = c                 (14) + d, c
(6) goto L1               (15) + (14), f
(7) L0:                   (16) + (15), b
(8) d = 0                 (17) PRINT (16)
```

---
# 7. Editing Triples Safely

A triple is named by its *position*. After `(3)` is deleted, the old `(4)` becomes the new `(3)`,
and every reference `(4)` elsewhere must change too. So the passes never remove triples directly.
They

1. **replace** uses (`replace_uses`: every `(1)` becomes `8`),
2. **mark** triples deleted, and then
3. `compact()` removes them, renumbers, and fixes every reference at once.

---
# 8. Home Work Extension

1. **Break the analysis on purpose.** In `available_expressions()`, change `set.intersection` to
   `set().union` (a *may* analysis instead of a *must* analysis), and use this program:

   ```text
   p = 0;
   if (x > 8)
       p = x * y;
   q = x * y;
   print p + q;
   ```

   With `x = 20` the output is still right, but with `x = 3` the optimized program prints `0`
   instead of `15`. Explain why from the IN/OUT tables, and why testing only one input would have
   missed the bug. Then change it back.
2. Add a `while` loop that recomputes `x * y` in its body, and check that CSE still finds it.
   Then start every OUT at `set()` instead of all facts. What changes, and why?
3. Copy propagation leaves `b = 8` in place and `+ (15), b` reading it. Which analysis would be
   needed to replace that `b` by `8` across blocks? (Hint: it is a forward *must* analysis, like
   available expressions.)

---
# 9. Key Takeaway

> **Local optimizations look at one triple or one block. Global optimizations need a data-flow
> analysis over the CFG: forward and "on every path" (∩) to know what is *available*, backward
> and "on some path" (∪) to know what is still *live*. Whatever an optimization changes, the
> program must print exactly what it printed before.**

```text
Triples
 ↓
CFG (practice 6)
 ↓
constant folding + copy propagation         (local, repeated)
 ↓
available expressions  →  CSE                (global, forward, must)
 ↓
liveness  →  dead code elimination           (global, backward, may)
 ↓
Smaller program -- same output
```
