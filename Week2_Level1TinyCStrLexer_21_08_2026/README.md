# Week 2 — Level 1 Lexer (Stages 1a → 1b)

## What is "Level 1" of TinyCStr?

**Level 1** of TinyCStr contains a basic set of language features. Each subsequent level builds on the previous level by adding new language features.

At Level 1, TinyCStr supports:

* A single `int main(){ ... }` function
* `int` variable declarations
* Integer constants
* Assignment statements
* `print` statements
* Arithmetic operators: `+`, `-`, `*`, `/`, `%`

The compiler will gradually support these features through different stages:

```text
Level 1
  ├── Week 2 → Lexer
  ├── Week 3 → Parser + AST
  └── Week 4 → Three-Address Code + MIPS
```

By the end of Week 4, the complete Level 1 compiler will be able to process a TinyCStr program from **source code to executable MIPS code**.

Week 2 focuses only on the first step:

```text
Source Program → Lexer → Tokens
```

## What are we building?

This week build the **lexer** for the TinyCStr compiler.

A lexer reads the source program character by character and converts it into a sequence of **tokens**. These tokens will be used by the parser in the next stage of the compiler.

For example:

```text
int a;
a = 10 + 20;
print a;
```

is converted into tokens such as:

```text
INT  ID  SEMICOLON
ID  ASSIGN  NUMBER  PLUS  NUMBER  SEMICOLON
PRINT  ID  SEMICOLON
```

This week focuses only on **lexical analysis**. The parser, AST generation, code generation, and compilation stages will be added in later weeks.

## What are we trying to do this week?

The goal is to complete the TinyCStr lexer in two stages:

* **Stage 1a — Basic tokens**

  * Keywords: `int`, `print`
  * Identifiers
  * Integer constants
  * Assignment operator `=`
  * Punctuation: `;`, `{`, `}`, `,`, `(`, `)`

* **Stage 1b — Arithmetic operators**

  * `+`
  * `-`
  * `*`
  * `/`
  * `%`

By the end of the week, the lexer should recognize all Level 1 TinyCStr tokens and report lexical errors without stopping at the first error.

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


## What you should understand by the end of Week 2

You should be able to explain:

* What a lexer does in a compiler
* What a token is
* The difference between a **keyword** and an **identifier**
* How regular expressions are used to recognize tokens
* How SLY's `Lexer` class works
* Why token matching order matters
* How ignored characters and comments are handled
* How line numbers are maintained
* How lexical errors can be reported while allowing lexical analysis to continue


