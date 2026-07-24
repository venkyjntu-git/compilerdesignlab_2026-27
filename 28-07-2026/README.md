# Week 3 — Level 1 Parser + AST (Stages 1a → 1b)

## What's already provided (do not modify)

- `main.py` — updated this week: `-ast` is added to generate the ast, `-parse` runs a syntax-check-only pass. 

- `tinycstr_lexer.py` — a **verified reference lexer** (Level 1, Stages 1a+1b complete). 
- `ast_nodes.py` — the AST node classes (`ASTNode` base, `Num`, `Var`, `Assign`, `Print`,`BinOp`), plus the shared `pretty()` and `to_dot()` tree-walkers. Fully implemented — this week's learning objective is the parser that *builds* these trees, not the node classes themselves.
- `SymbolTable.py` — `DataType`, `SymbolTableEntry`, `SymbolTable`. Fully implemented.
- `Function.py` / `Program.py` — plain program-structure containers (NOT AST nodes — see `docs/grammar_ast_reference.md`). Fully implemented.

## What you need to do

- `tinycstr_parser.py` — the actual exercise. Grammar rules are `TODO(week-3, stage-1a)` / `TODO(week-3, stage-1b)` parts for you to fill in, staged the same way Week 2's lexer was.

## What's provided to help you

- `docs/grammar_ast_reference.md` — the exact Level 1 grammar (Stage 1a and 1b) and the AST-vs-program-structure design rule this week is built around.
- `docs/sly_parser_help.md` — SLY parser-specific mechanics: `return` vs. `p[0]`, precedence-tuple ordering , reading the conflict debug log, `p.expr0`/`p.expr1` disambiguation, and `error(self, token)` when `token is None`.
- `docs/grading_rubric.md` — point-by-point breakdown, with the precedence-table check weighted
  heavily since it's the easiest place to be silently wrong.
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

## Getting unstuck

If you're still stuck, post in the Week 3 GitHub Issues, so the answer is visible to every one.
