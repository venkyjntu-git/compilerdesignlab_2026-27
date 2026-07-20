"""
TinyCStr compiler driver.

Usage:
    python3 main.py [options] file

This is the single entry point for the whole course -- each week wires up
one more stage instead of adding a new script. As of Week 2, only -tokens
is implemented. 

Options:
    -h, --help          print this help message and exit
    -tokens             write tokens to stdout
"""
import argparse
import sys

from tinycstr_lexer import TinyCStrLexer


def write_tokens(source_path, out_file):
    """
    Tokenizes source_path with TinyCStrLexer and writes one line per token,
    'TYPE value lineno', to out_file. Illegal characters are written as
    'ERROR char lineno' lines, interleaved at the point they occur in the
    file.
    """
    with open(source_path) as f:
        source = f.read()
    lexer = TinyCStrLexer(error_sink=out_file)
    for tok in lexer.tokenize(source):
        print(f"{tok.type} {tok.value} {tok.lineno}", file=out_file)


def build_arg_parser():
    parser = argparse.ArgumentParser()
 
    parser.usage = "python3 main.py [options] file"
 
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
    parser.add_argument('file', help="TinyCStr Program")
    
    return parser


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not args.file:
        parser.print_usage()
        sys.exit(1)

    if args.tokens:
        tokens_file_name = args.file + ".toks"
        with open(tokens_file_name, "w") as tokens_file:
            write_tokens(args.file, tokens_file)  # WEEK 2: implemented

    if args.parse:
        print("Not implemented yet!")

    if args.ast:
        print("Not implemented yet!")

    if args.symtab:
        print("Not implemented yet!")

    if args.compile:
        print("Not implemented yet!")


if __name__ == '__main__':
    main()
