"""
TinyCStr compiler driver.

Usage:
    python main.py [options] file 

options:
-tokens  for tokens 
-ast     for abstract syntax trees
-parse   for parsing checking acceptance yes/no
"""
import argparse
import sys

from tinycstr_lexer import TinyCStrLexer
from tinycstr_parser import TinyCStrParser
from ast_nodes import pretty


def write_tokens(source_path, out_file):
    """
    Tokenizes source language program with TinyCStrLexer and writes one line per
    token, 'TYPE value lineno', to out_file. Illegal characters are
    written as 'ERROR char lineno'
    """
    with open(source_path) as f:
        source = f.read()
    lexer = TinyCStrLexer()
    for tok in lexer.tokenize(source):
        print(f"{tok.type} {tok.value} {tok.lineno}", file=out_file)


def _parse_source(source_path):
    """
    Parses TinyCStr program, reports if there is any error 
    """
    with open(source_path) as f:
        source = f.read()
    lexer = TinyCStrLexer()
    parser = TinyCStrParser()
    program = parser.parse(lexer.tokenize(source))
    return program, parser.had_error


def write_ast(source_path, out_file):
    """
    Parses TinyCStr program and writes the AST for every function's
    statement list to out_file. 
    """
    program, had_error = _parse_source(source_path)
    if had_error:
        print("# parse error -- AST may be incomplete", file=out_file)
        return
    for func in program.getFunctions():
        print(f"Function {func.getName()}", file=out_file)
        for stmt in func.getStatementsAstList():
            print(pretty(stmt, indent=1), file=out_file)


def check_parse_only(source_path):
    """
    Parses TinyCStr program and reports success/failure WITHOUT building or
    returning a usable Program object to the caller -- lighter-weight
    than -ast, called for -parse option.
    """
    _, had_error = _parse_source(source_path)
    return not had_error



def build_arg_parser():
    parser = argparse.ArgumentParser()
    parser.usage = "python main.py [options] file"
    parser.add_argument('-tokens', action='store_true',
                         help="Show tokens in file.toks (or out.toks)")
    parser.add_argument('-parse', action='store_true',
                         help="Stop processing with parsing")
    parser.add_argument('-ast', action='store_true',
                         help="Show abstract syntax trees in file.ast (or out.ast)")
    parser.add_argument('-symtab', action='store_true',
                         help="Show symbol table in file.sym (or out.sym)")
    parser.add_argument('-compile', action='store_true',
                         help="Compile the program and generate spim code in file.spim (or out.spim)")
    parser.add_argument('file', help="TinyC Program")
    return parser


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.tokens:
        tokens_file_name = args.file + ".toks"
        with open(tokens_file_name, "w") as tokens_file:
            write_tokens(args.file, tokens_file)  # WEEK 2: implemented

    if args.parse:
        args.ast = False
        args.compile = False
        ok = check_parse_only(args.file)  # WEEK 3: implemented
        if ok:
            print(f"[main.py] '{args.file}' parses successfully (Level 1 grammar).")
        else:
            print(f"[main.py] '{args.file}' has a syntax error -- see messages above.",
                  file=sys.stderr)
            sys.exit(1)

    if args.ast:
        ast_file_name = args.file + ".ast"
        with open(ast_file_name, "w") as ast_file:
            write_ast(args.file, ast_file)  # WEEK 3: implemented

    if args.symtab:
        print("Symbol table full option not implemented yet.")

    if args.compile:
        print("Compile full option not implemented yet.")


if __name__ == '__main__':
    main()
