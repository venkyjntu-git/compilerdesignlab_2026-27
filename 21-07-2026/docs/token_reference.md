# TinyCStr — Level 1 Token Reference (Week 2)

This is the *only* part of the TinyCStr grammar you need for Week 2. Ignore everything else in the language specifications (types other than `int`, control flow, functions) — those come in later weeks. 

## Stage 1a token set

| Token    | Matches                          | Example        |
|----------|-----------------------------------|----------------|
| `INT`    | the literal keyword `int`         | `int`          |
| `PRINT`  | the literal keyword `print`       | `print`        |
| `ID`     | identifier: starts with letter or `_`, followed by any number of letters/digits/`_` | `a`, `count`, `_tmp1` |
| `INTEGER` | one or more decimal digits        | `5`, `40`      |
| `ASSIGN` | `=`                                | `=`            |
| `SEMICOLON`   | `;`                                | `;`            |
| `LBRACE` | `{`                                | `{`            |
| `RBRACE` | `}`                                | `}`            |
| `COMMA`  | `,`                                | `,`            |
| `LPAREN`  | `(`                               | `(`     |
| `RPAREN`  | `)`                               | `)`     |

## Stage 1b token set (add on top of 1a)

| Token     | Matches | Example |
|-----------|---------|---------|
| `PLUS`    | `+`     | `+`     |
| `MINUS`   | `-`     | `-`     |
| `TIMES`   | `*`     | `*`     |
| `DIVIDE`  | `/`     | `/`     |
| `REMAINDER`| `%`     |  `%`    |

## Rules that apply throughout

- **Identifiers vs. keywords:** `int` and `print` are reserved words. `interest`, `printer`, `int1` are all valid *identifiers*, not keywords — your lexer must not match a prefix. See `docs/sly_cheatsheet.md` for handling
- **Whitespace:** spaces and tabs between tokens are insignificant and produce no token.
- **Comments:** `//` starts a comment that runs to the end of the physical line. A comment can appear after code on the same line. There are no multi-line comments in TinyCStr.
- **Newlines:** not a token, but every token must carry line number (`tok.lineno`), because error messages require line no.
- **Case sensitivity:** TinyCStr is case-sensitive. `Int`, `INT`, `Print` are all plain identifiers, *not* keywords.
- **What is explicitly out of scope this week:** `main`, `double`, `char`, `string`, relational operators, `?:`, casts — none of these get special tokens yet. `main` is just an `ID` for now.

## Two example programs (from the course slides)

**Trivial Stage 1a program** ( simple program with assignment, print statements):
```
int main(){
int a;
a = 5;
print a;
}
```

**Example 1** (Stage 1b — the first program requiring `LPAREN`/`RPAREN`/`PLUS`, since `main()`
itself needs parentheses):
```
int main(){
     int a,b,c;
     a=5;
     b=5;
     c=a+b;   // all statements are similar to C, except print
    print c;    // print is predefined operator in TinyCStr which prints the value of c
}
```
