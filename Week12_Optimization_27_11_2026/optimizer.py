"""
The optimization pipeline -- provided, do not modify.

    python main.py -O -compile prog.tc          optimized MIPS
    python main.py -O -3ac prog.tc              optimized 3AC
    python main.py -O -passes fold,copy ...     only some passes
    python main.py -optreport prog.tc           prog.tc.opt: before/after every pass,
                                                the data-flow tables, MIPS instruction counts

Order of the passes, per function:
  1. LOCAL: copy propagation + constant folding, repeated until neither
     changes anything (each enables the other: a propagated constant can
     be folded, and a folded constant can be propagated further).
  2. CSE (available expressions). It turns `y = a * b` into the copy
     `y = x`, so step 1 runs once more afterwards.
  3. DCE (liveness), repeated until a round removes nothing: removing one
     assignment can make an earlier one dead.
After every pass, ir_utils.compact() renumbers the triples.
"""
from cfg import build_cfg, cfg_to_text
from ir_utils import compact
from opt_local import constant_folding, copy_propagation
from opt_cse import eliminate_common_subexpressions
from opt_dce import eliminate_dead_code

ALL_PASSES = ('fold', 'copy', 'cse', 'dce')


def _fmt_fact(f):
    op, a, b, _, holder = f
    return f"{holder}={a}{op}{b}"


def _fmt_set(items):
    return "{" + ", ".join(sorted(items)) + "}"


class Report:
    """Collects the human-readable trace of one function's optimization."""

    def __init__(self):
        self.lines = []

    def section(self, title, triples=None):
        self.lines.append(f"--- {title}")
        if triples is not None:
            self.lines.extend(t.render() for t in triples)

    def text(self, line):
        self.lines.append(line)


def _local(triples, passes, global_names):
    folded = copied = 0
    while True:
        n_copy = copy_propagation(build_cfg(triples), global_names) if 'copy' in passes else 0
        n_fold = constant_folding(triples) if 'fold' in passes else 0
        triples = compact(triples)
        folded += n_fold
        copied += n_copy
        if n_copy == 0 and n_fold == 0:
            return triples, folded, copied


def optimize_function(function, global_names, passes=ALL_PASSES, report=None):
    triples = function.tripleTACstmts.triples
    rep = report or Report()
    rep.section(f"3AC before optimization ({len(triples)} triples)", triples)

    if 'fold' in passes or 'copy' in passes:
        triples, folded, copied = _local(triples, passes, global_names)
        rep.section(f"after constant folding + copy propagation: {folded} folded, "
                    f"{copied} operand(s) propagated ({len(triples)} triples)", triples)

    if 'cse' in passes:
        cfg = build_cfg(triples)
        n, IN, OUT, gen, kill = eliminate_common_subexpressions(triples, cfg, global_names)
        rep.section("available expressions (a fact holder=a op b: holder holds a op b)")
        for b in cfg.blocks:
            rep.text(f"{b.name}  gen={_fmt_set(map(_fmt_fact, gen[b.number]))}  "
                     f"kill={_fmt_set(map(_fmt_fact, kill[b.number]))}  "
                     f"IN={_fmt_set(map(_fmt_fact, IN[b.number]))}  "
                     f"OUT={_fmt_set(map(_fmt_fact, OUT[b.number]))}")
        triples = compact(triples)
        rep.section(f"after common subexpression elimination: {n} eliminated "
                    f"({len(triples)} triples)", triples)
        if 'fold' in passes or 'copy' in passes:
            triples, folded, copied = _local(triples, passes, global_names)
            rep.section(f"after constant folding + copy propagation (again): {folded} folded, "
                        f"{copied} operand(s) propagated ({len(triples)} triples)", triples)

    if 'dce' in passes:
        total, rounds, first = 0, 0, None
        while True:
            cfg = build_cfg(triples)
            n, IN, OUT, use, define = eliminate_dead_code(triples, cfg, global_names)
            if first is None:
                first = (cfg, IN, OUT, use, define)
            triples = compact(triples)
            rounds += 1
            total += n
            if n == 0:
                break
        cfg, IN, OUT, use, define = first
        rep.section("liveness (first round)")
        for b in cfg.blocks:
            rep.text(f"{b.name}  use={_fmt_set(use[b.number])}  def={_fmt_set(define[b.number])}  "
                     f"IN={_fmt_set(IN[b.number])}  OUT={_fmt_set(OUT[b.number])}")
        rep.section(f"after dead code elimination: {total} assignment(s) removed in "
                    f"{rounds} round(s) ({len(triples)} triples)", triples)

    function.tripleTACstmts.triples = triples
    return rep


def optimize_program(program, passes=ALL_PASSES, with_report=False):
    """Optimizes every function. Returns {function name: Report} if with_report."""
    global_names = {e.getSymbolName() for e in program.getGlobalSymbolTable().table}
    reports = {}
    for function in program.getFunctions():
        rep = optimize_function(function, global_names, passes, Report() if with_report else None)
        reports[function.getName()] = rep
    return reports


def program_cfg_text(program):
    """-cfg output: one CFG per function."""
    parts = []
    for function in program.getFunctions():
        cfg = build_cfg(function.tripleTACstmts.triples)
        header = f"function {function.getName()}:" if len(program.getFunctions()) > 1 else None
        parts.append((header + "\n" if header else "") + cfg_to_text(cfg))
    return "\n".join(parts)


def count_instructions(asm_text):
    """Static count: lines of the .text section that are instructions (not labels/directives)."""
    count = 0
    in_text = False
    for line in asm_text.splitlines():
        s = line.strip()
        if s == ".text":
            in_text = True
            continue
        if s == ".data":
            in_text = False
            continue
        if in_text and s and not s.endswith(":") and not s.startswith("."):
            count += 1
    return count
