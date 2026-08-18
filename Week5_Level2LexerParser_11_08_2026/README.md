# Week 5 — Level 2 Lexer + Parser (Stages 2a → 2c)

## What is "Level 2" of TinyCStr?

TinyCStr compiler is developed step by step. Each level adds new features to the previous level, keeping the compiler working at every stage.

- **Level 1** (Weeks 2–4): a single `int main(){ ... }` function; `int`-only declarations;
  assignment and `print` statements; the four arithmetic operators `+ - * /`. By the end of
  Week 4 this had a complete pipeline: lexer → parser → AST → three-address code → MIPS →
  runs on SPIM.
- **Level 2** (this week, plus Weeks 6–7): adds three new *kinds*
  of language feature on top of Level 1:
  1. **More types** — `double`, `char`, `string`, alongside the existing `int`.
  2. **More operators** — relational operators (`< > <= >= == !=`) and the ternary operator
     (`cond ? a : b`).
  3. **Explicit casting** — `(double)expr`, `(int)expr` —  *single
     expression* mix types (e.g. dividing an `int` as a `double`).

 Every Level 1 program is still a valid Level 2 program; the grammar just accepts more now.

## What we're trying to do this week

Specifically: extend the **lexer and parser only** to recognize and correctly parse Level 2
syntax, producing the correct AST shape. This week's goal is 
is: given a Level 2 program, does the parser produce the AST you'd expect?

The work is staged, each stage adding one piece before the next:

- **Stage 2a** — `double` declarations and real constants. 
- **Stage 2b** — `char`/`string` declarations and constants, plus all six relational operators
  (one new AST node, `RelOp`, covers all of them). 
- **Stage 2c** — casts and the ternary operator. This is where mixed-type expressions first
  become legal (`(double)a / b`), casts need special precedence handling (SLY's `%prec` mechanism), and the ternary operator needs to be right-associative for chained ternaries to nest correctly.

Note: Level 1's lexer/parser rules are already complete and working (carried over from Weeks 2–4) —
you're extending them, not rewriting them.

## Current file contents

### What's already provided (do not modify)

- **`ast_nodes.py`** — AST node classes. `Var`, `Assign`, `Print`, `BinOp` are unchanged from
  Level 1. Three things are new this week:
  - **`Const(value, type)`** — the generic constant node, used for *every* constant kind
    (int, double, char, string). Unlike Level 1's old `Num` node (which only ever held numbers
    and inferred nothing about type), `Const` carries an explicit `type` field — a
    `SymbolTable.DataType` value (`DataType.INT`, `DataType.DOUBLE`, etc.) 
  - **`RelOp(op, left, right)`** — one node covering all six relational operators, the same
    shape as `BinOp`.
  - **`Cast(target_type, expr)`** — `target_type` is a `DataType` value (`DataType.DOUBLE` /
    `DataType.INT`), matching `Const`'s convention.
  - **`Ternary(cond, then_expr, else_expr)`**.
- **`SymbolTable.py`** — `DataType` now has `INT`, `DOUBLE`, `CHAR`, `STRING`,
  `getSizeOfType()` returns a real byte size for all four (`INT`→4, `DOUBLE`→8, `CHAR`→1,
  `STRING`→4), and offset assignment (`assignOffsetsToSymbols()`).
- **`Function.py`, `Program.py`, `three_address_code.py`, `tac_generator.py`, `tac_to_mips.py`**
  — the entire Level 1 codegen pipeline from Week 4, **fully implemented** 
- **`main.py`** — the driver. `-tokens`, `-ast`, `-parse` work fully on any Level 1 or Level 2
  program. `-3ac` and `-compile` work only for Level 1 programs

### What you need to do

- **`tinycstr_lexer.py`** — Level 1 token rules (INT, ID, NUMBER, PRINT, ASSIGN, arithmetic
  operators, etc.) are complete; leave them alone. The full Level 2 token set is already
  *declared* in `tokens = {...}` (`DOUBLE`, `REAL_CONST`, `CHAR`, `STRING`, `CHAR_CONST`,
  `STRING_CONST`, `LT`/`GT`/`LE`/`GE`/`EQ`/`NE`, `QUESTION`, `COLON`) — your job is writing the
  actual lexer *rules* for them, staged 2a → 2b → 2c per the comments in the file.
- **`tinycstr_parser.py`** — same structure: Level 1 grammar is complete, your TODOs are the
  Level 2 grammar rules (new `decl` alternatives for each type, new `expr` alternatives for
  constants/relational operators/casts/ternary), plus the trickiest part of the week — extending
  the `precedence` tuple correctly for relational operators, ternary, and casts.

### Documentation

- **`docs/level2_token_reference.md`** — the exact Level 2 token/grammar additions per stage,
  
- **`docs/sly_help2.md`** — the SLY-specific mechanics this week's grammar work actually needs:
  precedence-tuple ordering for relational/ternary operators, and the `%prec` idiom casts
  require (a plain precedence entry isn't enough on its own to get `(double)a/b` parsing
  correctly).

### Tests

`tests/test4.tc` (Stage 2a: `int` + `double`, declared and used separately),
`tests/test5.tc` (Stage 2b: `char`/`string` declarations, relational operators),
`tests/test6.tc` (Stage 2c: using type casting and a ternary) — each with  `.toks`/`.ast` output to
diff against.

## Step by step

1. Read `docs/level2_token_reference.md` fully before writing any code.
2. Implement Stage 2a's lexer + parser TODOs. Test:
   ```bash
   python main.py -tokens -ast tests/test4.tc
   diff tests/test4.tc.toks tests/test4.toks.expected.txt
   diff tests/test4.tc.ast tests/test4.ast.expected.txt
   ```
 
3. Implement Stage 2b. Test against `tests/test5.tc` the same way (tokens/AST only)

4. Read `docs/sly_help2.md` 5 carefully before starting Stage 2c — casts are the
   trickiest grammar work in the whole course so far.
5. Implement Stage 2c. Test against `tests/test6.tc` (the corrected Example 3). Specifically
   verify the AST shows `Cast` wrapping only the immediately-following operand, not a whole
   division — that's the one mistake that doesn't show up as a syntax error.
6. Take-home: write 5 TinyCStr(L2) programs — one per sub-stage, plus one combining all of them
   with at least one nested ternary and one chained cast — and produce their ASTs.

## Getting unstuck

If you're still stuck, post in the Week 5 GitHub Issues. 
