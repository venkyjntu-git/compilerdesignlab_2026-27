# Lab Practice 7 - Function Calls and Activation Records

Practice 5 generated MIPS for one expression, writing a variable's address as a placeholder:
`disp($fp)ofx`. This exercise finishes that idea for **functions**. Every *call* of a function
gets its own **activation record** (stack frame), every variable a real offset from `$fp`, and
the generated program **runs on SPIM**.

It supports Week 10 (functions, parameters, `return`) and Week 11 (activation records and the
MIPS calling convention).

Run it:

```text
python ExprAstParser.py          # prints triples, frame layouts, MIPS; writes program.s
spim -file program.s             # prints 25
```

---
# 1. The Small Language

```text
P        -> function function ...
function -> int id ( int p1, int p2, ... ) { stmts }      at most 4 parameters
S        -> id = E ;  |  return E ;  |  print E ;
F        -> NUMBER | id | ( E ) | id ( E, E, ... )        <- a call is an expression
```

Every value is an `int`. A **local variable** is any variable assigned in a function that is not
one of its parameters; there are no declarations.

The example program:

```text
int square(int x) {
    return x * x;
}
int sumOfSquares(int a, int b) {
    s = square(a) + square(b);
    return s;
}
int main() {
    print sumOfSquares(3, 4);
}
```

---
# 2. Three New Triples

| Triple | Example | Meaning |
|---|---|---|
| `ParamTriple` | `(0) PARAM a` | one argument of the **next** `CALL` |
| `CallTriple` | `(1) CALL square, 1` | call `square` with the 1 preceding `PARAM`; a reference `(1)` means its result |
| `ReturnTriple` | `(1) RETURN (0)` | give `(0)` back to the caller, and leave the function |

`sumOfSquares` becomes:

```text
(0) PARAM a
(1) CALL square, 1        <- (1) is square(a)
(2) PARAM b
(3) CALL square, 1        <- (3) is square(b)
(4) + (1), (3)
(5) s = (4)
(6) RETURN s
```

**All arguments are evaluated before the first `PARAM`.** In `f(1, g(2))`, the call `g(2)` must
be complete (`PARAM 2`, `CALL g`) *before* `PARAM 1`. Otherwise the code generator would collect
`PARAM 1` and `PARAM 2` together as `g`'s arguments.

---
# 3. The Activation Record

Each call needs its own copy of the function's parameters and locals. With recursion, the same
function may be active many times at once, so they can't live at fixed addresses. They live in
a block of stack memory created by the call and removed by its return:

```text
        higher addresses
        |  caller's frame       |
        +-----------------------+
        |  saved $ra            |   frame_size + 4 ($fp)
        |  saved $fp (caller's) |   frame_size + 0 ($fp)
        |  local variables      |
        |  parameters           |   0 ($fp), 4 ($fp), ...
        +-----------------------+  <- $fp  (= $sp)
        lower addresses              (the stack grows DOWN)
```

The program prints the layout of each frame. For `sumOfSquares`:

```text
Frame of sumOfSquares: 12 bytes of variables
   16($fp)  saved $ra
   12($fp)  saved $fp
    8($fp)  s  (local)
    4($fp)  b  (parameter)
    0($fp)  a  (parameter)
```

So `lw $t0, 4($fp)` reads `b`. This is the *real* form of practice 5's `disp($fp)ofb`.

---
# 4. Prologue and Epilogue

Every function starts by **building** its frame, and ends by **removing** it:

```asm
f_sumOfSquares:
    subu $sp, $sp, 4        # PROLOGUE: push $ra
    sw   $ra, 0($sp)
    subu $sp, $sp, 4        # push the caller's $fp
    sw   $fp, 0($sp)
    addiu $fp, $sp, -12     # new frame: 12 bytes
    move $sp, $fp
    sw $a0, 0($fp)          # parameter a from $a0
    sw $a1, 4($fp)          # parameter b from $a1
    ...
ret_sumOfSquares:
    addiu $sp, $fp, 12      # EPILOGUE: drop the frame
    lw    $fp, 0($sp)       # restore the caller's $fp
    addiu $sp, $sp, 4
    lw    $ra, 0($sp)       # restore the return address
    addiu $sp, $sp, 4
    jr    $ra               # back to the caller
```

- `$ra` must be saved because the function itself calls `square`, and every `jal` overwrites
  `$ra`. Without saving it, `sumOfSquares` could never get back to `main`.
- The arguments arrive in `$a0`, `$a1`. They are copied into the frame at once, so that the body
  reads them like any other variable, and so that the next call, which reloads `$a0`, can't
  destroy them.
- `return s;` becomes `move $v0, ...` and `j ret_sumOfSquares`: every `return` jumps to the
  epilogue.

---
# 5. The Calling Convention

Caller and callee must agree on where things are:

| What | Where |
|---|---|
| arguments 1–4 | `$a0`–`$a3` |
| result | `$v0` |
| return address | `$ra` (set by `jal`, used by `jr $ra`) |
| saved by the **callee** | `$ra`, `$fp` (prologue/epilogue) |
| saved by the **caller** | any `$t` register still needed after the call |

`main` is called too, by SPIM's start-up code (`jal main`). That is why it has the same prologue
and epilogue, and ends with `jr $ra`.

---
# 6. A Call, Step by Step

From `sumOfSquares`, the second call `square(b)`:

```asm
    jal f_square            # first call: square(a)
    move $t0, $v0           # its result -- still needed for the +
    subu $sp, $sp, 4        # 1. save $t0: square will reuse $t0 for itself!
    sw $t0, 0($sp)
    lw $t1, 4($fp)          # 2. argument b ...
    move $a0, $t1           #    ... into $a0
    jal f_square            # 3. call
    move $t1, $v0           # 4. the result, out of $v0
    lw $t0, 0($sp)          # 5. restore $t0
    addiu $sp, $sp, 4
    add $t2, $t0, $t1       # square(a) + square(b)
```

Step 1 is the subtle one. `square` uses `$t0`, `$t1`, `$t2` for its own work, so after the call,
`$t0` no longer holds `square(a)`. The caller knows which registers it is still using (the ones
allocated and not yet released), and saves exactly those.

---
# 7. The Stack During the Deepest Call

While `square(4)` runs, three frames are on the stack:

```text
        |  main's frame          |   no variables
        |------------------------|
        |  sumOfSquares(3, 4)    |   a=3  b=4  s=?
        |  saved $t0 = 9         |   <- square(3), saved by the caller
        |------------------------|
        |  square(4)             |   x=4               <- $fp, $sp
```

Each `return` removes the top frame and goes back to the one below.

---
# 8. Home Work Extension

1. Change `inp` so that `main` prints `sumOfSquares(1, 2) + sumOfSquares(3, 4)`. Find in the MIPS
   where the first result is saved and restored. Check the output (30) on SPIM.
2. Add a fifth parameter to a function. The generator stops with an error. Extend `FrameLayout`
   and `gen_call()` so that arguments 5, 6, ... are pushed on the stack by the caller, and read by
   the callee at **positive** offsets above its saved `$ra`.
3. This little language has no `if`, so a recursive function could never stop. Explain why
   recursion would nevertheless work with these frames: what does the stack look like during
   `fact(3)` → `fact(2)` → `fact(1)`? (Week 11's `tests/test22.tc` runs exactly this.)

---
# 9. Key Takeaway

> **A function call is a contract. The caller puts the arguments in `$a0`–`$a3`, saves what it
> still needs, and jumps with `jal`. The callee builds its own frame, finds its variables at fixed
> offsets from `$fp`, leaves the result in `$v0`, removes its frame and returns with `jr $ra`.**

```text
AST (functions)
 ↓
Triples with PARAM / CALL / RETURN
 ↓
Frame layout per function (offsets from $fp)
 ↓
Prologue  +  body  +  epilogue, and the call sequence at every CALL
 ↓
MIPS that runs on SPIM
```
