"""
TinyCStr compiler driver.

Usage:
    python main.py [options] file

"""
import argparse
import sys

from tinycstr_lexer import TinyCStrLexer
from tinycstr_parser import TinyCStrParser
from ast_nodes import ASTNode, FunctionCall, Return, pretty, to_dot
from type_checker import check_program
from SymbolTable import DataType


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


class _FunctionRoot(ASTNode):
    """WEEK 8: a display-only root so a whole function body renders as ONE DOT tree."""

    def __init__(self, func):
        self.func = func

    def label(self):
        return f"Function {self.func.getName()}"

    def children(self):
        return self.func.getStatementsAstList()


class _ProgramRoot(ASTNode):
    """WEEK 10: one DOT tree for the whole program -- one child per function."""

    def __init__(self, program):
        self.program = program

    def label(self):
        return "Program"

    def children(self):
        return [_FunctionRoot(f) for f in self.program.getFunctions()]


def write_dot(source_path):
    """WEEK 8: -dot writes file.dot; render with `dot -Tpng file.dot -o file.png`."""
    program, had_error = _parse_source(source_path)
    if had_error:
        print(f"[main.py] '{source_path}' has a syntax error -- no .dot written.",
              file=sys.stderr)
        return
    functions = program.getFunctions()
    root = _FunctionRoot(functions[0]) if len(functions) == 1 else _ProgramRoot(program)
    to_dot(root, filename=source_path + ".dot")


def _type_name(datatype):
    return datatype.name.lower()


def _signature(name, return_type, param_types):
    """WEEK 10: C-style text for a signature, e.g. `int add(int, int)`."""
    return f"{_type_name(return_type)} {name}({', '.join(_type_name(t) for t in param_types)})"


def write_symtab(source_path, out_file):
    program, had_error = _parse_source(source_path)
    if had_error:
        print("# parse error -- cannot show symbol table", file=out_file)
        return
    globals_table = program.getGlobalSymbolTable()  # WEEK 8
    if globals_table.table:
        print("Global", file=out_file)
        for entry in globals_table.table:
            print(f"  {entry.getSymbolName()}: {entry.getDataType()}", file=out_file)
    # WEEK 10: the function table -- printed only for programs that have
    # prototypes or more than one function, so Level 1-3 output is unchanged.
    functions = program.getFunctions()
    if program.getPrototypes() or len(functions) > 1:
        print("Functions", file=out_file)
        for proto in program.getPrototypes():
            print(f"  {_signature(proto.getName(), proto.getReturnType(), proto.getParamTypes())}"
                  f";   (prototype, line {proto.getLineno()})", file=out_file)
        for func in functions:
            print(f"  {_signature(func.getName(), func.getReturnType(), func.getParamTypes())}"
                  f"   (definition, line {func.getLineno()})", file=out_file)
    for func in functions:
        print(f"Function {func.getName()}", file=out_file)
        params = func.getParamSymbolTable().table          # WEEK 10
        for entry in params:
            print(f"  {entry.getSymbolName()}: {entry.getDataType()} (parameter)", file=out_file)
        symtab = func.getLocalSymbolTable()
        if not symtab.table and not params:
            print("  (no local variables)", file=out_file)
        for entry in symtab.table:
            print(f"  {entry.getSymbolName()}: {entry.getDataType()}", file=out_file)


def write_check(source_path, out_file):
    program, had_error = _parse_source(source_path)
    if had_error:
        print("# parse error -- cannot type-check", file=out_file)
        return
    warnings = []                                   # WEEK 10
    errors = check_program(program, warnings)
    if errors:
        print(f"{len(errors)} type error(s) found:", file=out_file)
        for e in errors:
            print(f"  {e}", file=out_file)
    else:
        print("No type errors found.", file=out_file)
    if warnings:
        print(f"{len(warnings)} warning(s):", file=out_file)
        for w in warnings:
            print(f"  {w}", file=out_file)
    print(file=out_file)
    print("Type-checked AST (with any inserted casts):", file=out_file)
    for func in program.getFunctions():
        print(f"Function {func.getName()}", file=out_file)
        for stmt in func.getStatementsAstList():
            print(pretty(stmt, indent=1), file=out_file)


def _type_check_gate(program, out_file):
    errors = check_program(program)
    if errors:
        print(f"# {len(errors)} type error(s) found -- cannot proceed:", file=out_file)
        for e in errors:
            print(f"# {e}", file=out_file)
        return False
    return True


def _contains_call_or_return(node):
    if isinstance(node, (FunctionCall, Return)):
        return True
    return any(_contains_call_or_return(child) for child in node.children())


def uses_level4(program):
    """
    WEEK 10: True if the program needs anything the Level 3 back end can't
    translate yet -- a second function, a prototype, a call, a return, or a
    non-int return type. Calls, activation records and the MIPS calling
    convention are Week 11's work.
    """
    functions = program.getFunctions()
    if len(functions) > 1 or program.getPrototypes():
        return True
    if functions[0].getReturnType() != DataType.INT:
        return True
    return any(_contains_call_or_return(stmt) for stmt in functions[0].getStatementsAstList())


def write_3ac_debug(source_path, out_file):
    program, had_error = _parse_source(source_path)
    if had_error:
        print("# parse error -- cannot generate 3AC", file=out_file)
        return
    if not _type_check_gate(program, out_file):
        return
    if uses_level4(program):  # WEEK 10
        not_implemented_stage('function-call 3ac generation', planned_week=11, out_file=out_file)
        return
    program.generateTripleTAC()
    func = program.getFunctions()[0]
    out_file.write(func.renderTripleTAC() + "\n")


def write_compile(source_path, out_file):
    program, had_error = _parse_source(source_path)
    if had_error:
        print("# parse error -- cannot compile", file=out_file)
        return
    if not _type_check_gate(program, out_file):
        return
    if uses_level4(program):  # WEEK 10 -- see write_3ac_debug()
        not_implemented_stage('function-call compile', planned_week=11, out_file=out_file)
        return
    program.generateTripleTAC()
    program.compile()
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
    parser.add_argument('-dot', action='store_true',
                        help="[not in original spec] Write the AST as Graphviz DOT to file.dot")
    parser.add_argument('-symtab', action='store_true',
                         help="Show symbol table in file.sym (or out.sym)")
    parser.add_argument('-check', action='store_true',
                         help="[not in original spec] Run the type checker, "
                              "write errors + checked AST to file.check")
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

    if args.dot:
        write_dot(args.file)  # WEEK 8

    if args.symtab:
        with open(args.file + ".sym", "w") as f:
            write_symtab(args.file, f)

    if args.check:
        with open(args.file + ".check", "w") as f:
            write_check(args.file, f)

    if args.threeac:
        with open(args.file + ".3ac", "w") as f:
            write_3ac_debug(args.file, f)

    if args.compile:
        with open(args.file + ".spim", "w") as f:
            write_compile(args.file, f)  # Levels 1-3 (WEEK 9: control flow + globals)


if __name__ == '__main__':
    main()
