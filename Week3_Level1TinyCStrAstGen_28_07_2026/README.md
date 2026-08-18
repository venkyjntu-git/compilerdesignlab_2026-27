# Week 3 — Level 1 Parser + AST (Stages 1a → 1b)

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
Week 3 focuses on the second step:

```text 
Source Program → Lexer → Parser → AST
```

## What are we building?

This week you will build the parser for the TinyCStr compiler and use it to construct an Abstract Syntax Tree (AST).

The lexer from Week 2 converts the source program into tokens. The parser takes those tokens and checks whether they follow the grammar of TinyCStr.

The parser also builds an AST that represents the structure of the program.

For example:

```text
x = a + b * c
```


The corresponding AST is:

```text
        =
       / \
      x   +
         / \
        a   *
           / \
          b   c
```

The tree clearly shows that multiplication is performed before addition.


## What are we trying to do this week?

The goal is to complete the TinyCStr parser in two stages:

* **Stage 1a — Basic grammar**
  * Program structure
  * Variable declarations
  * Assignment statements
  * print statements
  * Integer constants
  * Identifiers
* **Stage 1b — Arithmetic expressions**
  * `+`
  * `-`
  * `*`
  * `/`
  * `%`
  * Operator precedence
  * Operator associativity

By the end of the week, the parser should:

* Recognize valid Level 1 TinyCStr programs.
* Report syntax errors.
* Build the correct AST.
* Preserve the correct precedence and associativity of arithmetic operators.

## What's already provided (do not modify)

- `main.py` — updated this week: `-ast` is added to generate the ast, `-parse` runs a syntax-check-only pass. 

- `tinycstr_lexer.py` — a **verified reference lexer** (Level 1, Stages 1a+1b complete). 
- `ast_nodes.py` — the AST node classes (`ASTNode` base, `Num`, `Var`, `Assign`, `Print`,`BinOp`), plus the shared `pretty()` and `to_dot()` tree-walkers. Fully implemented — this week's learning objective is the parser that *builds* these trees, not the node classes themselves.
- `SymbolTable.py` — `DataType`, `SymbolTableEntry`, `SymbolTable`. Fully implemented.
- `Function.py` / `Program.py` — plain program-structure containers (Not as AST nodes — see `docs/grammar_ast_reference.md`). Fully implemented.

## What you need to do

- `tinycstr_parser.py` — the actual exercise. Grammar rules are `TODO(week-3, stage-1a)` / `TODO(week-3, stage-1b)` parts for you to fill in, staged the same way Week 2's lexer was.

## What's provided to help you

- `docs/grammar_ast_reference.md` — the exact Level 1 grammar (Stage 1a and 1b) and the AST-vs-program-structure design rule this week is built around.
- `docs/sly_parser_help.md` — SLY parser-specific mechanics: `return`, precedence-tuple ordering , reading the conflict debug log, `p.expr0`/`p.expr1` disambiguation, and `error(self, token)` when `token is None`.
- `tests/` — three `.tc` programs and their exact expected AST text
  (`.expected.txt`), including the take-home's Example 2 precedence check.
  `python3 main.py -ast/-parse ...` staged the same way as Week 2.

## What you need to do, step by step

1. Read `docs/grammar_ast_reference.md` and `docs/sly_parser_help.md` fully first.
2. Implement every `TODO(week-3, stage-1a)` in `tinycstr_parser.py`.
3. Run `pyton3 main.py -ast test.tc` should pass test cases 
4. Implement every `TODO(week-3, stage-1b)` — precedence table first, then the arithmetic `expr` rules. Before moving on, deliberately look at SLY's shift-reduce conflict output once and  you have to actually read it, not just trust that `precedence` fixed things.
5. Manually run `python main.py -ast <file>` on all three files in `tests/` and check the resulting `.ast` files against the `.expected.txt` files once.
7. Render at least one AST as a Graphviz diagram: write a small script using `to_dot()` from `ast_nodes.py`, save the output to a `.dot` file, then `dot -Tpng out.dot -o out.png`
8. Take-home: parse `c=a+b*a+a*a;` produce
   its AST, and hand-trace `c`'s value to confirm your AST's shape matches the expected precedence/associativity, not just that some tree came out. Write 5 additional test programs covering both stages.

## What you should understand by the end of Week 3

You should be able to explain:

* What a parser does in a compiler
* The difference between lexical analysis and syntax analysis
* What a grammar is
* How SLY parser rules correspond to grammar productions
* What an AST is and why compilers use it
* The difference between an AST and the concrete syntax of a program
* How arithmetic operator precedence is represented in a parser
* What associativity means
* What a shift-reduce conflict is
* How precedence declarations help to resolve shift-reduce conflicts
* How a parser can construct an AST while recognizing the input

## Getting unstuck

If you're still stuck, post in the Week 3 GitHub Issues 
