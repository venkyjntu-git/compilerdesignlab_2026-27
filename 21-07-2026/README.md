# Week 2 — Level 1 Lexer (Stages 1a → 1b)

## What's already provided

- `main.py` — the **course-wide compiler driver**, not a Week-2-only script. Implements
  `-tokens` fully (writes `<file>.toks`); `-parse`, `-ast`, `-symtab`, `-compile` are present as
  safe parts that print a "not implemented yet" message for now. Later weeks replace one part at a time — this file's structure and argument parsing won't change.
- `tinycstr_lexer.py` — a skeleton `TinyCStrLexer(Lexer)` class. The token set, class structure, and comments are in place; the actual token rules are `TODO(week-2, ...)` parts for you to fill in, staged into Stage 1a and Stage 1b sections.
- `tests/` — three `.tc` programs and their exact expected token streams
  (`.expected.txt`), used to self-check your work.
- `docs/token_reference.md` — the exact Level 1 token set and grammar rules, 
- `docs/sly_help.md` — the SLY-specific mechanics you need this week (keyword disambiguation, match ordering, ignore rules, line tracking, error handling).
- `docs/grading_rubric.md` — point-by-point breakdown of how this week is graded.

## What you need to do

1. Read `docs/token_reference.md` and `docs/sly_help.md` fully before writing code.
2. Implement every `TODO(week-2, stage-1a)` in `tinycstr_lexer.py`.
3. Run `python3 main.py -tokens tests/stage1a_trivial.tc` and compare the output with stage1a_trivial.expected.txt
4. Implement every `TODO(week-2, stage-1b)`.
5. Run `python3 main.py -tokens tests/program.tc` on all three files in `tests/` and check the output against the `.expected.txt` files once
6. Write the 5 additional take-home test programs (see the lab plan),
   run them through `main.py`, and include the actual output in your submitted report.

