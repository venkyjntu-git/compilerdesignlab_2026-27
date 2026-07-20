# Week 2 Grading Rubric — Level 1 Lexer

Total: 20 points. Maps directly to the stated deliverable: `tinycstr_lexer.py` (Stages 1a + 1b)
+ a token-dump test report for 6 programs.

| Item | Points | Pass condition |
|---|---|---|
| Stage 1a: declarations & assignment tokens (`INT`, `ID`, `NUMBER`, `ASSIGN`, `SEMI`, `COMMA`) | 4 | `stage1a_trivial.tc` output matches `stage1a_trivial.expected.txt` exactly |
| Stage 1a: `PRINT` keyword correctly disambiguated from `ID` | 2 | A variable named e.g. `printer` or `printed` still lexes as `ID`, not `PRINT` + extra chars |
| Stage 1a: `LBRACE`/`RBRACE` | 1 | Present and correctly typed in `stage1b_example1` output (used for `{`/`}`) |
| Stage 1b: arithmetic operators (`PLUS`, `MINUS`, `TIMES`, `DIVIDE`) | 3 | `stage1b_example1.tc` output matches `stage1b_example1.expected.txt` exactly |
| Stage 1b: `LPAREN`/`RPAREN` | 1 | Correctly typed in `stage1b_example1` output (`main()`) |
| Comment handling | 2 | Comments after code on the same line are fully discarded, no partial tokens leak through |
| Line-number tracking | 3 | Every token's line number is correct across a 7-line multi-line program; wrong line numbers on otherwise-correct tokens lose these points even if token *types* are right |
| Illegal-character error handling | 3 | `illegal_char.tc` output matches `illegal_char.expected.txt` exactly, including correct interleaving of `ERROR` lines with valid tokens, and the lexer does not stop after the first error |
| Take-home: 5 additional test programs + report | 1 | Programs collectively exercise both stages plus at least one deliberate illegal character; report shows actual tool output, not hand-written/predicted output |

**Note on partial credit:** a lexer that gets token *types* right but line numbers wrong is not
"basically correct" — every later week's error messages depend on Week 2's line tracking being
solid, so line-number correctness is weighted accordingly rather than treated as a minor
detail.

**Common zero-credit mistakes:** submitting a lexer that only works on the exact example files
and crashes on any other well-formed Stage-1a/1b program; hand-editing the `.expected.txt`
files to match your output instead of fixing your lexer (this is checked — the golden files are
compared against the instructor's originals, not your copy).
