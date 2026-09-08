# Compiler Design Lab 2026–27 — TinyCStr
 
A hands-on compiler construction lab. Over 12 weeks you build a complete compiler — lexer,
parser, AST, semantic analysis, three-address code, optimizations, and a MIPS backend that
runs on the SPIM simulator — for **TinyCStr**, a small statically-typed procedural language
(`int`, `double`, `char`, `string`; relational and ternary operators; `if-else`/`while`;
functions with a mandatory `main`).
 
Implementation is in Python using **[SLY (Sly Lex Yacc)](https://sly.readthedocs.io/en/latest/sly.html)**.
The course structure is inspired by Prof. Uday Khedker's
[Implementation of Programming Languages Course](https://www.cse.iitb.ac.in/~uday/sclp-web/#About) at IIT Bombay.

--- 
## Course map (levels and weekly deliverables)

| Week | Focus | Level / Stage | Deliverable |
|---|---|---|---|
| 1 | Setup + TinyCStr orientation | — | Verified SLY + SPIM env  |
| 2 | Lexer | L1a → L1b | Lexer for integers, then arithmetic tokens |
| 3 | Parser + AST | L1a → L1b | AST for Assignments, then full expression grammar |
| 4 | 3AC + MIPS | L1 | End-to-end L1 compiler, SPIM-verified |
| 5 | Lexer + parser | L2a → L2c | Types, casting, relational/ternary ops |
| 6 | Semantic analysis | L2 | Symbol table, type checking |
| 7 | 3AC+ MIPS codegen | L2 | Mixed-type MIPS, SPIM-verified |
| — | *Optional:* Toolchain survey | — | Ungraded, self-contained extra hour |
| 8 | Lexer + parser | L3a → L3b | `if`, then `else`/`while` |
| 9 | Control-flow 3AC + MIPS | L3 | CFG, branching, SPIM-verified |
| 10 | Lexer + parser | L4a → L4b | Multi-function scoping, then params/`return` |
| 11 | Activation records | L4 | Full calling convention on MIPS |
| 12 | Optimizations | — | Constant folding, copy propagation, CSE, dead code elimination, loop unrolling |

Full rationale for the level/stage breakdown is in `CDLabPlan2026_27.pdf`.
---

## Submitting your work


 Fork + Pull Request
1. Fork this repository once.
2. Each week, merge upstream `main` into your fork before lab.
3. Commit your completed week's folder to a branch named `weekNN-<your-roll-number>`.
4. Open a PR from that branch into your own fork's `main`. Tag the instructor as reviewer.
