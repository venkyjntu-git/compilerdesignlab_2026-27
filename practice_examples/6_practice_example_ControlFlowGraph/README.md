# Lab Practice 6 - Control Flow: Labels, Jumps and the Control-Flow Graph

This exercise extends the expression language of practices 2–5 with **statements that change the
order of execution**: `if`, `if-else`, `while`, `print`, and blocks `{ ... }`. It shows:

1. how such statements become **three-address code with labels and jumps**, and
2. how that code is cut into **basic blocks** and connected into a **control-flow graph (CFG)**.

It supports Week 9 (control-flow 3AC + MIPS branching, and drawing the CFG by hand) and Week 12
(building the CFG automatically).

Run it:

```text
python ExprAstParser.py
```

---
# 1. The Small Language

```text
P    -> stmts
S    -> id = E ;  |  print E ;  |  { stmts }
      | if ( C ) S  |  if ( C ) S else S  |  while ( C ) S
C    -> E relop E                relop: <  >  <=  >=  ==  !=
E, T, F                          exactly as in practice 2 (+ - * /, parentheses)
```

A comparison `C` produces **1 (true)** or **0 (false)**, as in C.

---
# 2. Three New Triples

Until now every triple simply ran after the one before it. Three new triples change that:

| Triple | Example | Meaning |
|---|---|---|
| `LabelTriple` | `(3) L0:` | a place that can be jumped to; does nothing itself |
| `GotoTriple` | `(13) goto L0` | always continue at `L0` |
| `IfFalseTriple` | `(5) if_false (4) goto L1` | if `(4)` is **0**, continue at `L1`; otherwise go on to the next triple |

Why "if **false**"? The code of a branch comes right after its condition. If the condition is
true we simply carry on into it; we only need to jump when it is false, to *skip* the branch.

---
# 3. Translating the Statements

`<c>` means "the triples computing the condition", and `c` the operand they return.

```text
if (c) S               if (c) S1 else S2          while (c) S
---------              ------------------         -----------
    <c>                    <c>                    Ltop:
    if_false c Lend        if_false c Lelse           <c>
    <S>                    <S1>                       if_false c Lend
Lend:                      goto Lend                  <S>
                       Lelse:                         goto Ltop      <- jump BACK
                           <S2>                   Lend:
                       Lend:
```

- `goto Lend` after `S1` is essential: without it, the then-part would run straight on into the
  else-part.
- In a `while`, `Ltop` is placed **before** the condition, so that the condition is tested again
  on every iteration.
- Labels come from `new_label()`, the **fresh-label allocator** (`L0`, `L1`, `L2`, ...). The same
  label is never handed out twice.

---
# 4. The Example Program

```text
n = 10;
i = 1;
s = 0;
while (i <= n) {
    if (i > 5)
        s = s + i;
    i = i + 1;
}
print s;
```

It produces:

```text
(0) n = 10
(1) i = 1
(2) s = 0
(3) L0:                      <- while: Ltop
(4) <= i, n
(5) if_false (4) goto L1     <- leave the loop
(6) > i, 5
(7) if_false (6) goto L2     <- skip s = s + i
(8) + s, i
(9) s = (8)
(10) L2:                     <- if: Lend
(11) + i, 1
(12) i = (11)
(13) goto L0                 <- back to the condition
(14) L1:                     <- while: Lend
(15) PRINT s
```

---
# 5. Step 1 - Leaders

A **basic block** is a sequence of triples that always runs from its first triple to its last:
control enters only at the top and leaves only at the bottom. The first triple of each block is
called a **leader**. A triple is a leader if it is

1. the **first** triple of the program,
2. a **label** (some jump may arrive there), or
3. the triple **right after** a `goto` or `if_false` (the jump may have skipped it).

For the example:

```text
(0)   rule 1   first triple
(3)   rule 2   L0:
(6)   rule 3   after (5) if_false
(8)   rule 3   after (7) if_false
(10)  rule 2   L2:
(14)  rule 2   L1:      (it is also after (13) goto -- one triple, two reasons)
```

`find_leaders()` returns `[0, 3, 6, 8, 10, 14]`.

---
# 6. Step 2 - Basic Blocks

Each block runs from one leader up to the triple before the next leader:

```text
B0 = (0)..(2)     B1 = (3)..(5)     B2 = (6)..(7)
B3 = (8)..(9)     B4 = (10)..(13)   B5 = (14)..(15)
```

---
# 7. Step 3 - Edges

The **last** triple of each block decides where control can go next:

| Last triple | Edges |
|---|---|
| `goto L` | to the block that starts with `L`, and nowhere else |
| `if_false c goto L` | to the block of `L` (**false**), and to the next block (**true**) |
| anything else | to the next block (fall through) |

The program prints:

```text
B0   preds: -   succs: B1
B1   preds: B0 B4   succs: B5[false] B2[true]
B2   preds: B1   succs: B4[false] B3[true]
B3   preds: B2   succs: B4
B4   preds: B2 B3   succs: B1
B5   preds: B1   succs: exit
```

`cfg.png` is the same graph, drawn by Graphviz from `cfg.dot`:

```text
        B0
        |
        v
  +---> B1 ----false----> B5 (print s) -> exit
  |     | true
  |     v
  |     B2 ----false----+
  |     | true          |
  |     v               |
  |     B3              |
  |     |               |
  |     v               |
  +---- B4 <------------+
   back edge (goto L0)
```

Things to notice:
- The **back edge** `B4 → B1` is what makes this a loop. In a CFG, a loop is always a cycle.
- `B1` has two predecessors, one from before the loop and one from the end of the loop body.
- The inner `if` without `else` forms a small "diamond": `B2 → B3 → B4`, plus the short cut
  `B2 → B4`.

---
# 8. Drawing a CFG by Hand

Use the same three steps on paper:

1. Write the triples down, numbered.
2. Circle the leaders (rules 1–3), and draw a line above each one: the pieces are the blocks.
3. For each block, look at its last triple and draw the edges (table in section 7). Label the
   two edges of an `if_false` as true/false.

Check yourself: a block that ends with `goto` has **exactly one** successor, and a block that
ends with `if_false` has **exactly two**.

---
# 9. Home Work Extension

1. Change `inp` in `ExprAstParser.py` to a program with an `if-else` inside the `while` (count the
   even and the odd numbers up to `n`, using `i - (i / 2) * 2 == 0`). Draw the CFG by hand first,
   then run the program and compare. How many blocks does an `if-else` add, compared with an `if`?
2. Write a program with **two consecutive labels**: an `if` whose body ends with another `if`,
   such as `if (a > 0) { if (b > 0) x = 1; }`. Both `if`s end at the same point, so their two end
   labels are next to each other. You will find a block containing only a label. Is it a mistake?
3. Render the graph yourself: `dot -Tpng cfg.dot -o cfg.png` (Graphviz).

---
# 10. Key Takeaway

> **Control flow is expressed in three-address code by only two kinds of jumps, `goto` and
> `if_false`, plus labels to jump to. The CFG makes those jumps visible: basic blocks are the
> nodes, possible jumps and fall-throughs are the edges.**

```text
AST
 ↓
Triples with labels and jumps
 ↓
Leaders  →  Basic blocks  →  Edges
 ↓
Control-Flow Graph
```

The CFG is the starting point for optimizations (practice 8), which reason about *all the paths*
a program can take.
