# MIPS / SPIM Reference (Week 4)

This week's codegen follows the **Frame-based Linkage Convention**:
<https://chortle.ccsu.edu/AssemblyTutorial/Chapter-28/ass28_06.html> — from the very first
program, including `main`, so the convention stays consistent once functions with real
parameters and calls arrive (Week 10-11).

## Every generated `.s` file has this shape

```mips
.text
.globl main
main:
    subu $sp, $sp, 4
    sw   $ra, 0($sp)
    subu $sp, $sp, 4
    sw   $fp, 0($sp)
    addiu $fp, $sp, -<frame_size>
    move $sp, $fp

    ...body: one or more triples, each a few lw/li/op/sw or move lines...

    addiu $sp, $fp, <frame_size>
    lw    $fp, 0($sp)
    addiu $sp, $sp, 4
    lw    $ra, 0($sp)
    addiu $sp, $sp, 4
    jr    $ra
```

No `.data` section — every declared variable lives in `main`'s own stack frame, addressed as
`offset($fp)`. `frame_size` is `symbol_table.size()` (already-implemented on `SymbolTable`) —
**only** the declared locals' total size. Triple (temporary) results live in `$t` registers
this week, not on the stack, so nothing extra needs to be reserved for them — see
`docs/register_allocation_reference.md`.

## The prologue, matched to the linkage convention's numbered steps

| Convention step | Code |
|---|---|
| 1. Push `$ra` | `subu $sp,$sp,4` / `sw $ra,0($sp)` |
| 2. Push caller's `$fp` | `subu $sp,$sp,4` / `sw $fp,0($sp)` |
| 3. Push any `$s0-$s7` altered | *(none this week — see below)* |
| 4. `$fp = $sp - space_for_variables` | `addiu $fp,$sp,-<frame_size>` |
| 5. `$sp = $fp` | `move $sp,$fp` |

**No `$s`-register saves this week (step 3):** that step exists for subroutines that need a
register to hold a value *across a call to another subroutine*. Level 1 has no function calls
yet — `main` doesn't call anything and nothing calls it except SPIM's own startup code — so
there's nothing to protect. Relevant again starting Week 10.

## The epilogue

| Convention step | Code |
|---|---|
| 15. Return value in `$v0`/`$v1` | *(none — `main` doesn't return a value to a TinyCStr caller)* |
| 16. `$sp = $fp + space_for_variables` | `addiu $sp,$fp,<frame_size>` |
| 17. Pop saved `$s` registers | *(none this week)* |
| 18. Pop caller's `$fp` | `lw $fp,0($sp)` / `addiu $sp,$sp,4` |
| 19. Pop `$ra` | `lw $ra,0($sp)` / `addiu $sp,$sp,4` |
| 20. Return | `jr $ra` |

`emit_prologue()`/`emit_epilogue()` in `tac_to_mips.py` are **provided, not a TODO** — this is
an exact instruction sequence, and any deviation corrupts the stack in ways that are hard to
debug from the symptom alone.

## Why no explicit exit syscall is needed

`main`'s epilogue ends in plain `jr $ra`, not `li $v0,10`/`syscall`. This was **verified
directly on real SPIM**, not assumed: SPIM's own default startup code calls `main` via
`jal main`, and once `main` returns via `jr $ra`, the startup code performs the exit itself. A
minimal frame-based test program (2 locals, no explicit exit) was run standalone on real SPIM
before this convention was trusted for the full pipeline — it printed its output and terminated
cleanly.

## Registers used this week

| Register | Use |
|---|---|
| `$fp` | frame pointer — every variable access is `offset($fp)` |
| `$sp` | stack pointer — only touched by the prologue/epilogue |
| `$ra` | return address — saved/restored by the prologue/epilogue, used by `jr $ra` |
| `$t0`–`$t9` | general-purpose scratch, allocated on demand per triple — see `docs/register_allocation_reference.md` for the allocation strategy |
| `$a0` | holds the value to print, right before the print syscall |
| `$v0` | syscall selector |

## Instructions and pseudo-instructions used this week

| Instruction | Effect |
|---|---|
| `li reg, N` | `reg = N` |
| `lw reg, offset($fp)` | `reg = memory[$fp + offset]` |
| `sw reg, offset($fp)` | `memory[$fp + offset] = reg` |
| `add/sub rd, rs, rt` | real MIPS instructions |
| `mul/div rd, rs, rt` | **pseudo-instructions** — SPIM's assembler expands the 3-operand form into the real 2-operand `mult`/`div` + `mflo` sequence automatically |
| `addiu rd, rs, imm` | `rd = rs + imm` (all the frame-size arithmetic) |
| `subu rd, rs, rt` | `rd = rs - rt` (register form, only used for the fixed `$sp` push adjustments) |
| `move rd, rs` | pseudo-instruction, `rd = rs`; also used to move a value into `$a0` before printing |
| `jr $ra` | return — jump to the address in `$ra` |
| `syscall` | performs whatever `$v0` currently selects (`1` = print int in `$a0`) |


## Running your generated code

```bash
python main.py -compile program.tc      # writes program.tc.spim
spim -file program.tc.spim              # runs it
```
