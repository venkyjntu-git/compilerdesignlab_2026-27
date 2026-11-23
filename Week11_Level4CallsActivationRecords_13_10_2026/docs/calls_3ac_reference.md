# Three-Address Code for Calls (Week 11)

Three triples, already defined in `three_address_code.py`, carry function calls through the IR:

| Triple | Rendered as | Meaning |
|---|---|---|
| `ParamTriple(arg, arg_type)` | `(5) PARAM (4) : INT` | one argument of the **next** `CALL` |
| `CallTriple(name, nargs, return_type, value_used)` | `(6) CALL fib, 1 : INT` | call `name` with the `nargs` preceding PARAMs; a `TripleRef` to it is the call's value |
| `ReturnTriple(arg, return_type)` | `(11) RETURN (10) : INT` / `(3) RETURN` | leave the function, handing `arg` (if any) back |

A call used as a statement (`bump();`) has `value_used=False`. For a non-`void` function, this
renders as `CALL f, 2 : INT (result unused)`, and the back end then doesn't keep the result in a
register.

## The translation scheme

```
f(e1, e2, ..., en)          <code for e1>      -> operand o1
                            <code for e2>      -> operand o2
                            ...
                            PARAM o1
                            PARAM o2
                            ...
                            CALL f, n

return e;                   <code for e>  ->  o
                            RETURN o

return;                     RETURN
```

**Evaluate every argument first, then emit all the PARAMs.** This guarantees that the PARAMs of
one call are *consecutive* and immediately precede their `CALL`, however deeply calls are
nested. The back end relies on that: it collects PARAMs until it reaches a `CALL`, then places
exactly those as the call's arguments.

Here is what goes wrong if each PARAM is emitted as soon as its argument is evaluated. Take
`f(1, g(2))`:

```
PARAM 1          <- f's first argument
PARAM 2          <- g's argument
CALL g, 1        <- the back end hands g BOTH pending PARAMs: g receives 1 instead of 2
PARAM (2)
CALL f, 2        <- and f receives only ONE argument
```

With arguments evaluated first, the order is correct:

```
PARAM 2
CALL g, 1
PARAM 1
PARAM (1)        <- g's result
CALL f, 2
```

**PARAM types.** `arg_type` is the *parameter's* type. The type checker already wrapped any
argument that needed converting in a `Cast` (Week 10), so the argument expression's
`result_type` *is* the parameter type. `half(s)` with an `int` variable `s` and a `double`
parameter becomes `CAST(DOUBLE) s` followed by `PARAM (k) : DOUBLE`.

## Example: `fib` from `tests/test22.tc`

```
int fib(int n){                          function fib:
    if (n < 2)                           (0) < n, 2 : cmp INT
        return n;                        (1) if_false (0) goto L1 : INT
                                         (2) RETURN n : INT
                                         (3) L1:
    return fib(n - 1) + fib(n - 2);      (4) - n, 1 : INT
}                                        (5) PARAM (4) : INT
                                         (6) CALL fib, 1 : INT
                                         (7) - n, 2 : INT
                                         (8) PARAM (7) : INT
                                         (9) CALL fib, 1 : INT
                                         (10) + (6), (9) : INT
                                         (11) RETURN (10) : INT
```

Triple (6)'s value is needed by (10), but call (9) happens in between. In the IR that is
invisible, but in MIPS the first result is sitting in a caller-saved register during the second
call. `docs/activation_records.md` #4 shows how the back end keeps it alive.

## Several functions in one program

- `-3ac` prints one block per function, headed `function <name>:`. A one-function program prints
  exactly as before, with no header. Triple numbers restart at `(0)` in each function, since a
  `TripleRef` never crosses a function boundary.
- **Label numbers do not restart.** `L0, L1, ...` continue from one function to the next
  (`Program.generateTripleTAC()` passes the counter along), because all functions end up in the
  same `.s` file, where a label may be defined only once. In `test22`, `fact` uses `L0` and `fib`
  starts at `L1`.
