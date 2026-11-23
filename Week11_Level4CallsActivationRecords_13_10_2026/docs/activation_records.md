# Activation Records and the TinyCStr Calling Convention (Week 11)

Every code excerpt in this file comes from the goldens in `tests/`, and every test program was run
on **SPIM 8.0**.

## 1. The activation record (stack frame)

Each *call* of a function gets its own block of stack memory, its **activation record**, holding
that call's parameters, locals, and the bookkeeping needed to return. Recursion works because
`fact(5)`, `fact(4)`, ... are five separate *activations*, each with its own `n` in its own frame.

The stack grows **downward**, toward lower addresses. Within a function, `$fp` points to the
bottom of its frame, and every local or parameter is at a fixed offset from it:

```
  higher addresses
  ┌──────────────────────────┐
  │ caller's frame ...       │
  ├──────────────────────────┤ <- $sp when the caller executes jal
  │ stack arguments          │    frame_size + 8 + k ($fp)    (k = position in the argument area)
  ├──────────────────────────┤
  │ saved $ra                │    frame_size + 4 ($fp)
  │ saved $fp (caller's)     │    frame_size + 0 ($fp)
  ├──────────────────────────┤
  │ register parameters,     │    after the locals
  │   homed from $a0-$a3     │
  │ local variables          │    0 ($fp) ...
  └──────────────────────────┘ <- $fp = $sp
  lower addresses
```

`Function.layoutFrame()` (provided) assigns these offsets, and `-symtab`'s variables are exactly
the ones placed here. Example: `int add(int a1, int a2)` in `tests/test19.tc` has no locals and two
register parameters, so `frame_size = 8`, `a1` is at `0($fp)` and `a2` at `4($fp)`. `double
mult(double m1, double m2)` gets both arguments on the stack (doubles always go there, #2), so
`m1` is at `8($fp)` and `m2` at `16($fp)`, above its saved `$fp`/`$ra`.

**Prologue and epilogue.** These are unchanged since Week 4. They already saved `$ra` and `$fp`,
because `main` itself is *called* by SPIM's start-up code:

```mips
f_add:
    subu $sp, $sp, 4         # push the return address
    sw   $ra, 0($sp)
    subu $sp, $sp, 4         # push the caller's frame pointer
    sw   $fp, 0($sp)
    addiu $fp, $sp, -8       # new frame: 8 bytes
    move $sp, $fp
    sw $a0, 0($fp)           # home the register arguments   <- NEW this week
    sw $a1, 4($fp)
    ...                      # body
    ret_add:                 # every `return` jumps here     <- NEW this week
    addiu $sp, $fp, 8        # drop the frame
    lw    $fp, 0($sp)        # restore the caller's $fp
    addiu $sp, $sp, 4
    lw    $ra, 0($sp)        # restore the return address
    addiu $sp, $sp, 4
    jr    $ra                # back to the caller
```

**Why "home" the register arguments?** Storing `$a0`–`$a3` into the frame first means the body
reads every parameter from memory, exactly like a local, so there is no new code path. It also
keeps them safe: `print` overwrites `$a0`, and any nested call reloads `$a0`–`$a3` with *its*
arguments. A parameter left in `$a0` would be destroyed by either.

## 2. The calling convention

Caller and callee must agree on these rules exactly; `calling_convention.py` (provided) is the
single place they live.

| What | Where |
|---|---|
| argument *i* (0-based), `int`/`char`/`string`, *i* < 4 | `$a`*i* |
| any `double` argument, and any argument at *i* ≥ 4 | the **stack argument area**, in parameter order, 4 bytes (int-family) or 8 (double) each, the first at the lowest address |
| return value, `int`/`char`/`string` | `$v0` |
| return value, `double` | `$f0` |
| return address | `$ra`, set by `jal`, used by `jr $ra` |
| **caller-saved** (the callee may destroy them) | `$t0`–`$t9`, `$f0`–`$f30`, `$a0`–`$a3`, `$v0` |
| **callee-saved** (restored before returning) | `$fp`, `$ra`; `$s0`–`$s7` are never used by this compiler |

Registers are numbered by **position**: in `weighted(int a, double w, int b, int c, int d, int e)`
(`tests/test23.tc`), `a` is in `$a0`, `w` goes to the stack, `b` is in `$a2`, `c` in `$a3`, and
`d`, `e` go to the stack. `$a1` is simply unused.

**Differences from the real MIPS O32 convention** (deliberate simplifications):
- O32 passes leading `double` arguments in `$f12`/`$f14`. TinyCStr puts every `double` on the
  stack, partly because our temporary allocator hands out `$f12`–`$f18` like any other register.
- O32 makes the caller reserve 16 bytes of "home" space for `$a0`–`$a3`. Here the callee homes them
  in its own frame (#1).

## 3. A call, step by step (the caller's side: `gen_call()`)

Here is `x = 10 * 3 + sum6(1, 2, 3, 4, 5, 6);` from `tests/test23.tc`:

```mips
    li $t0, 10
    li $t1, 3
    mul $t2, $t0, $t1        # 30 -- still needed AFTER the call
    subu $sp, $sp, 4         # 1. SAVE live temporaries ($t2)
    sw $t2, 0($sp)
    subu $sp, $sp, 8         # 2. ARGUMENTS: reserve the stack area (two ints)...
    li $t0, 1
    move $a0, $t0            #    ...the first four in $a0-$a3...
    li $t0, 2
    move $a1, $t0
    li $t0, 3
    move $a2, $t0
    li $t0, 4
    move $a3, $t0
    li $t0, 5
    sw $t0, 0($sp)           #    ...the 5th and 6th on the stack
    li $t0, 6
    sw $t0, 4($sp)
    jal f_sum6               # 3. CALL ($ra := address of the next instruction)
    addiu $sp, $sp, 8        #    pop the argument area
    move $t0, $v0            # 4. RESULT, copied out of $v0 into a fresh register
    lw $t2, 0($sp)           # 5. RESTORE $t2 (30)
    addiu $sp, $sp, 4
    add $t1, $t2, $t0        # 30 + 21
```

The order of these five steps matters:
- **1 before 2**: the saved registers must sit *above* the argument area, so that the callee finds
  its stack arguments right at the `$sp` it was called with.
- **4 before 5**: for a `double` result in `$f0`, a register being restored may itself be `$f0`.
  In `y = ((x > 0) ? 1.5 : 2.5) + weighted(...)`, `1.5` is in `$f0` during the call:

  ```mips
      jal f_weighted
      addiu $sp, $sp, 16
      mov.d $f2, $f0           # 4. the result (7.5) moves out of $f0 first...
      l.d $f0, 0($sp)          # 5. ...then 1.5 comes back into $f0
      addiu $sp, $sp, 8
      add.d $f4, $f0, $f2      # 1.5 + 7.5 = 9
  ```

  With steps 4 and 5 swapped, `tests/test23.tc` prints `y` as `3` instead of `9` on SPIM: the
  restore overwrites the result, so the program computes 1.5 + 1.5.

**Why PARAM emits nothing on its own.** `gen_param()` only records the triple. The call can save
the live registers (step 1) only after it knows which registers hold its own arguments, which are
used up by the call and need no saving. That is known only at the `CALL`.

## 4. Why temporaries need saving at all

Our register allocator is per *function*, and every function uses `$t0`, `$t1`, ... from scratch.
After `jal`, the callee has certainly reused them. A value computed *before* a call and used
*after* it must therefore survive in memory. From `fib` (`tests/test22.tc`):

```mips
    jal f_fib                # fib(n - 1)
    move $t0, $v0            # its result: needed after the NEXT call
    lw $t1, 0($fp)
    li $t2, 2
    sub $t3, $t1, $t2        # n - 2
    subu $sp, $sp, 4         # save $t0 across fib(n - 2)
    sw $t0, 0($sp)
    move $a0, $t3
    jal f_fib                # fib(n - 2)
    move $t1, $v0
    lw $t0, 0($sp)           # fib(n - 1) is back
    addiu $sp, $sp, 4
    add $t2, $t0, $t1
```

This is **caller-saves**: the caller saves only what it still needs, and knows exactly what that
is (the registers currently allocated). The alternative, **callee-saves**, has every function
save the registers it is about to use; that is what MIPS's `$s0`–`$s7` are for. Since Week 9 no
temporary is live at the end of a statement, so saves happen only for calls nested *inside*
expressions, and in most programs there are none at all. Compare `test19`'s `main` with
`test23`'s.

## 5. Labels

| Label | For | Example |
|---|---|---|
| `main` | `main` (SPIM's start-up code does `jal main`) | `main:` |
| `f_<name>` | every other function | `f_add:`, `jal f_add` |
| `ret_<name>` | the epilogue, target of `return` | `j ret_add` |
| `L<n>` | 3AC labels, then the back end's own | numbered across the **whole program** |
| `g_<name>` / `Lstr<n>` | globals / string literals (Week 9) | |

The prefix on function labels is not cosmetic. Example 4's function `add` is a MIPS instruction
name. Emitted unprefixed, SPIM rejects the program:

```
spim: (parser) syntax error on line 24 of file noprefix_fn.s
	  add
	  ^
```

## 6. Running out of registers? Not for variables

The lab plan's take-home asks for "a function with more local variables than fit comfortably in
registers, forcing at least one stack-resident local". In this compiler, **every** local and
parameter has lived in the stack frame since Week 4, with registers holding only short-lived
temporaries, so no local ever "spills": they all are already in memory. The take-home therefore
asks you to push the part that *can* run out (`README.md`): more than four arguments, `double`
arguments, and calls nested inside expressions, which need saved temporaries.

## 7. Things the convention does NOT protect you from

- **No `return` on some path**: an `int` function that falls off its end returns whatever
  happens to be in `$v0` at that moment. The Week 10 checker deliberately doesn't check this.
- **Deep recursion** uses one frame per active call. SPIM's stack is large, but not infinite.
