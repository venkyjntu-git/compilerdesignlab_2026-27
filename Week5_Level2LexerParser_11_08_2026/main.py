"""
TinyCStr compiler driver.

Usage:
    python main.py [options] file

"""
import argparse
import sys

from tinycstr_lexer import TinyCStrLexer
from tinycstr_parser import TinyCStrParser
from ast_nodes import pretty


def write_tokens(source_path, out_file):
    with open(source_path) as f:
        source = f.read()
    lexer = TinyCStrLexer(error_sink=out_file)
    for tok in lexer.tokenize(source):
        print(f"{tok.type} {tok.value} {tok.lineno}", file=out_file)


def _parse_source(source_path, lexer_error_sink=None):
    with open(source_path) as f:
        source = f.read()
    lexer = TinyCStrLexer(error_sink=lexer_error_sink or sys.stderr)
    parser = TinyCStrParser()
    program = parser.parse(lexer.tokenize(source))
    return program, parser.had_error


def write_ast(source_path, out_file):
    program, had_error = _parse_source(source_path)
    if had_error:
        print("# parse error -- AST may be incomplete", file=out_file)
        return
    for func in program.getFunctions():
        print(f"Function {func.getName()}", file=out_file)
        for stmt in func.getStatementsAstList():
            print(pretty(stmt, indent=1), file=out_file)


def check_parse_only(source_path):
    _, had_error = _parse_source(source_path)
    return not had_error


def write_3ac_debug(source_path, out_file):
    program, had_error = _parse_source(source_path)
    if had_error:
        print("# parse error -- cannot generate 3AC", file=out_file)
        return
    try:
        program.generateTripleTAC()
    except Exception:
        not_implemented_stage(
            '3ac generation for Level 2 constructs (RelOp/Cast/Ternary, '
            'non-INT variables)', planned_week=6, out_file=out_file)
        return
    func = program.getFunctions()[0]
    out_file.write(func.renderTripleTAC() + "\n")


def write_compile(source_path, out_file):
    program, had_error = _parse_source(source_path)
    if had_error:
        print("# parse error -- cannot compile", file=out_file)
        return
    try:
        program.generateTripleTAC()
        program.compile()
    except Exception:
        not_implemented_stage(
            'compile for Level 2 constructs (RelOp/Cast/Ternary, '
            'non-INT variables)', planned_week=7, out_file=out_file)
        return
    func = program.getFunctions()[0]
    out_file.write(func.getMipsCode())


def not_implemented_stage(stage_name, planned_week, out_file=None):
    msg = (f"[main.py] '{stage_name}' is not implemented yet "
           f"(planned for Week {planned_week}); skipping.")
    print(msg, file=sys.stderr)
    if out_file is not None:
        print(f"# {stage_name} not implemented yet (Week {planned_week})", file=out_file)


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
    parser.add_argument('-3ac', action='store_true', dest='threeac',
                         help="[not in original spec] Show 3-address code (triples) in file.3ac")
    parser.add_argument('-compile', action='store_true',
                         help="Compile the program and generate spim code in file.spim (or out.spim)")
    parser.add_argument('file', help="TinyC Program")
    return parser


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)


    if args.tokens:
        with open(args.file + ".toks", "w") as f:
            write_tokens(args.file, f)

    if args.parse:
        args.ast = False
        args.compile = False
        ok = check_parse_only(args.file)
        if ok:
            print(f"[main.py] '{args.file}' parses successfully.")
        else:
            print(f"[main.py] '{args.file}' has a syntax error -- see messages above.",
                  file=sys.stderr)
            sys.exit(1)

    if args.ast:
        with open(args.file + ".ast", "w") as f:
            write_ast(args.file, f)

    if args.threeac:
        with open(args.file + ".3ac", "w") as f:
            write_3ac_debug(args.file, f)

    if args.symtab:
        with open(args.file + ".sym", "w") as f:
            not_implemented_stage('symtab', planned_week=6, out_file=f)

    if args.compile:
        with open(args.file + ".spim", "w") as f:
            write_compile(args.file, f)


if __name__ == '__main__':
    main()
