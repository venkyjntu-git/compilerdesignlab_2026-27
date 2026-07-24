# TinyCStr — Level 1 Grammar & AST Reference (Week 3)

This is the *only* grammar you need for Week 3. No control flow, no functions beyond a single `main`, no types beyond `int` — those come in later weeks.

## Stage 1a grammar

```
program    : func_def

func_def  : INT ID LPAREN RPAREN LBRACE stmt_list RBRACE

stmt_list  : stmt_list stmt
           | empty

stmt       : decl
           | assign
           | print_stmt

decl       : INT id_list SEMICOLON          

id_list    : id_list COMMA ID
           | ID

assign     : ID ASSIGN expr SEMICOLON       

print_stmt : PRINT expr SEMICOLON           

expr       : NUMBER                    
           | ID                        

empty      :
```

## Stage 1b grammar (extends `expr` only)

```
expr : expr PLUS expr      
     | expr MINUS expr     
     | expr TIMES expr     
     | expr DIVIDE expr    
     | LPAREN expr RPAREN  
     | NUMBER
     | ID
```

Everything else (program, func_def, stmt_list, stmt, decl, id_list, assign, print_stmt) is unchanged from Stage 1a.

## The core design rule: AST vs. program structure

Three different kinds of object come out of parsing, and they are **not** the same kind of thing, on purpose:

| Kind | Examples | 
|---|---|
| **AST nodes** (`ast_nodes.py`) | `Num`, `Var`, `Assign`, `Print`, `PlusAST` |
| **Program-structure containers** (`Program.py, Function.py`) | `Program`, `Function` |
| **Symbol table entries** (`SymbolTable.py`) | `SymbolTableEntry` |

**A `decl` statement (`int a;`) produces no AST node.** Parsing a declaration is a pure side effect: insert a `SymbolTableEntry(name, DataType.INT)` into the current function's `SymbolTable`, and contribute nothing to the statement list. This is different from `Assign` and `Print`, which *do* need to add into an AST 

Example: for `int a; a = 5; print a;`, the AST is exactly two nodes (`Assign`, `Print`) — `int
a;` is invisible in the AST, visible only as an entry in `func.getLocalSymbolTable()`.


## AST node shapes (`ast_nodes.py`, provided — do not modify)

- `Num(value)` — leaf, integer literal
- `Var(name)` — leaf, identifier reference
- `Assign(var, expr)` — `var` is a `Var`, `expr` is any expression node
- `Print(expr)`
- `BinOp(op, left, right)` — Stage 1b only; `op` is `'+' | '-' | '*' | '/'`

Every node implements `label()` (one-line display text) and `children()` (list of child nodes).
`pretty(node, indent)` and `to_dot(node)` in `ast_nodes.py` are generic tree-walkers built on
top of those two methods — use them, no need to write your own print function.

## Program-structure shapes (provided — do not modify)

- `Function(returnType, name)` — holds `statementsAstList` (the AST, decl-free) and
  `localSymbolTable` (a `SymbolTable`)
- `Program()` — holds a list of `Function` objects (just one, `main`, for Level 1)

## Two canonical example programs (from the course slides)

**Stage 1a trivial program** (no operators):
```
int main(){
    int a;
    a = 5;
    print a;
}
```

**Example 1** (Stage 1b — arithmetic):
```
int main(){
     int a,b,c;
     a=5;
     b=5;
     c=a+b;   // all statements are similar to C, except print
    print c;    // print is predefined operator in TinyCStr which prints the value of c
}
```

**Take-home — Example 2's expression only.** 
The take-home deliberately scopes down to just the one expression line,
`c=a+b*a+a*a;`, dropped into a corrected, valid wrapper:
```
int main(){
    int a,b,c;
    a=5;
    b=5;
    c=a+b*a+a*a;
    print c;
}
```

Exact expected AST text for all three programs is in `tests/*.expected.txt`. Diff your
output against these to check.
