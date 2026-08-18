# Week 4 — Level 1: Three-Address Code and MIPS Code Generation

## What is "Level 1" of TinyCStr?

**Level 1** of TinyCStr contains a basic set of language features. Each subsequent level builds on the previous level by adding new language features.

At Level 1, TinyCStr supports:

- A single `int main(){ ... }` function
- `int` variable declarations
- Integer constants
- Assignment statements
- `print` statements
- Arithmetic operators: `+`, `-`, `*`, `/`, `%`

The compiler will gradually support these features through different stages:

```text
Level 1
  ├── Week 2 → Lexer
  ├── Week 3 → Parser + AST
  └── Week 4 → Three-Address Code + MIPS
```

By the end of Week 4, the complete Level 1 compiler will be able to process a TinyCStr program from source code to executable MIPS code.

This week completes the Level 1 compiler pipeline:

```text
Source Program
      ↓
    Lexer
      ↓
    Parser
      ↓
     AST
      ↓
Three-Address Code
      ↓
    MIPS
      ↓
   Execution
```

---

## What are we building?

In Week 3, the parser produced an Abstract Syntax Tree (AST).  
This week we use that AST to generate:

1. **Three-Address Code (TAC)** as an intermediate representation.
2. **MIPS assembly code** from the TAC.

The complete flow is:

```text
AST
 ↓
TAC / Triples
 ↓
MIPS Assembly
 ↓
SPIM Execution
```

This introduces two important compiler concepts:
- **Intermediate Code Generation**
- **Target Code Generation**

---

### Why do we need Three-Address Code?

Consider:

```c
x = a + b * c;
```

The AST represents the structure of the expression, but it is not yet convenient for generating machine instructions.  
We can first convert it into simpler intermediate instructions:

```text
t1 = b * c
t2 = a + t1
x = t2
```

Each instruction performs a simple operation.  
This is called **Three-Address Code (TAC)**.  
TAC provides an intermediate step between the AST and the target machine code.

```text
AST → Three-Address Code → MIPS
```

---

### Why are we using Triples?

There are different ways to represent Three-Address Code.  
One common representation is **quadruples**:

```text
(operator, argument1, argument2, result)
```

For `x = a + b * c`, we could write:

```text
0: ( *, b,  c,  t1 )
1: ( +, a,  t1, t2 )
2: ( =, t2, -,  x  )
```

**Triples** remove the explicit result field.  
Instead, the result of a triple is identified by its position:

```text
0: ( *, b,    c   )
1: ( +, a,    (0) )
2: ( =, (1),  x   )
```

Here:
- `(0)` means the result produced by triple 0.
- `(1)` means the result produced by triple 1.

Therefore, explicit temporary names such as `t1` and `t2` are not required.

---

## What are we trying to do this week?

The goal is to complete the Level 1 compiler by implementing:

### Part 1 — AST → Three-Address Code
Traverse the AST and generate triples for:
- Arithmetic expressions
- Assignment statements
- `print` statements

For example, `x = a + b * c;` should produce triples similar to:

```text
0: ( *, b,    c   )
1: ( +, a,    (0) )
2: ( =, (1),  x   )
```

### Part 2 — Three-Address Code → MIPS
Translate each triple into one or more MIPS instructions.

For example, `(0) * b, c` can be translated conceptually into:

```assembly
lw  $t0, <address-of-b>
lw  $t1, <address-of-c>
mul $t2, $t0, $t1
```

The result of triple 0 is now available in `$t2`.  
A later triple referring to `(0)` can therefore use `$t2`.

---

### Register Allocation

MIPS operations use registers. For example:

```assembly
add $t2, $t0, $t1
```

means `$t2 = $t0 + $t1`.

The code generator therefore needs to keep track of where values are stored:
- Triple 0 → `$t2`
- Triple 1 → `$t3`
- Triple 2 → `$t4`

If a later triple contains `(0)`, the code generator can resolve it to `$t2`.  
This week uses a simple register allocation strategy suitable for understanding the basic idea.

---

### Memory and Stack Frames

Variables need memory locations.  
The compiler uses the symbol table to assign offsets to variables in the function's stack frame.

Conceptually:

| Variable | Offset |
|---|---|
| `a` | `4($fp)` |
| `b` | `8($fp)` |
| `c` | `12($fp)` |
| `x` | `16($fp)` |

A variable can then be loaded using:

```assembly
lw $t0, 4($fp)
```

and stored using:

```assembly
sw $t1, 16($fp)
```

The stack frame provides a structured way to organize the memory used by the function.  
This is an important step toward understanding activation records and run-time memory organization.

---


## What do you need to do?

There are three main implementation tasks:

### 1. Generate Three-Address Code
Complete `tac_generator.py` by implementing the TODOs in:
- `gen_stmt()`
- `gen_expr()`

The generator should traverse the AST and produce triples.

### 2. Connect Function Compilation
Complete `Function.py`. The `compile()` method should:
1. Assign offsets to symbols.
2. Construct the MIPS generator.
3. Generate MIPS code.
4. Store the generated code for later output.

```text
Function → assignOffsetsToSymbols() → MIPSGenerator → generate() → MIPS code
```

### 3. Generate MIPS Code
Complete `tac_to_mips.py` by implementing:
- `resolve_address()`
- `load()`
- `store()`
- `gen_instr()`

These functions connect the intermediate representation to MIPS instructions.

---

Builds directly on practice examples 4 and 5.
## What's already provided (do not modify)

- `tinycstr_lexer.py`, `tinycstr_parser.py`, `ast_nodes.py` — unchanged.
- `SymbolTable.py` — `assignOffsetsToSymbols()`, `getSizeOfType()`, and
  `size()` fully implemented.
- `Program.py` — `Program.compile()` already just loops calling
  `function.compile()` for every function.
- `three_address_code.py` — the triple IR (`BinOpTriple`, `AssignTriple`, `PrintTriple`,
  `TripleRef`, `TripleTAC`).
- `main.py` — compile option flow `parse` →
  `program.generateTripleTAC()` → `program.compile()` → `func.getMipsCode()`.

## What you need to do

- `tac_generator.py` —  TODOs — `gen_stmt()`,`gen_expr()` 
- `Function.py` —  `compile()` : call `assignOffsetsToSymbols()`, construct a `MIPSGenerator`, call `generate()`, store the result.
- `tac_to_mips.py` — TODOs: `resolve_address()`, `load()`, `store()`,
  `gen_instr()`. 

## What's provided to help you

- `docs/register_allocation_reference.md` — exactly how this week's `tac_to_mips.py` differs
  from the practice example (real offsets, `PrintTriple`, prologue/epilogue), a full worked
  register-allocation trace for the precedence take-home program
- `docs/mips_spim_reference.md` — the Frame-based Linkage Convention mapped to actual MIPS,
  including why no explicit exit syscall is needed (verified on real SPIM).
- `tests/` — three `.tc` programs with exact golden triple-form `.3ac`, register-allocated
  frame-based `.s`, and expected SPIM console output — **every one of these was actually run on
  real SPIM** to generate.

## Step by step

1. Read `docs/register_allocation_reference.md` and the practice example it builds on.
2. Implement TODOs in `Function.py`, `tac_generate.py`,`tac_to_mips.py`
4. Test the full pipeline:
   ```bash
   python main.py -3ac -compile tests/test1.tc
   diff tests/test1.tc.3ac tests/test1.3ac.expected.txt
   diff tests/test1.tc.spim tests/test1.s.expected.txt
   ```
5. **Actually run it on SPIM** — a diff-matching `.s` is not the finish line:
   ```bash
   spim -file tests/test1.tc.spim
   ```
6. Take-home: 5 additional TinyCStr(L1) programs exercising all four operators, run through the
   full pipeline, actual SPIM console output included in your report.


---

## What you should understand by the end of Week 4

You should be able to explain:
- Why compilers use an intermediate representation
- What Three-Address Code is
- The difference between quadruples and triples
- How an AST can be traversed to generate TAC
- How triple indices represent intermediate results
- How triple references are resolved during code generation
- How variables and constants are loaded
- How values are stored back into memory
- What a stack frame is and why a compiler assigns offsets to variables
- What register allocation means and how registers can be reused
- How TAC instructions are translated into MIPS instructions
- How to test generated assembly using SPIM
- The complete flow from source code to executable target code

---

## Level 1 compiler — completed

At the end of Week 4, you have built a complete compiler pipeline for Level 1 TinyCStr:

```text
TinyCStr Source
       │
       ▼
    Lexer
       │
       ▼
    Parser
       │
       ▼
      AST
       │
       ▼
Three-Address Code (Triples)
       │
       ▼
MIPS Code Generator
       │
       ▼
 MIPS Assembly
       │
       ▼
     SPIM
       │
       ▼
 Program Output
```

This completes the first end-to-end TinyCStr compiler level. The next level will add new language features while reusing and extending the compiler infrastructure developed here.

---


## Getting unstuck

If you're still stuck, post in the Week 4 GitHub Issues thread  





