"""
Four classic optimizations on triples, using the CFG of practice 6.

  1. constant folding        compute  4 * 2  at compile time            (one triple)
  2. copy propagation        after  b = 8,  use 8 instead of b          (one block)
  3. common subexpressions   x * y already in c?  use c                 (whole CFG,
                             -- needs AVAILABLE EXPRESSIONS                data-flow)
  4. dead code elimination   remove  t = ...  if t is never read again  (whole CFG,
                             -- needs LIVENESS                             data-flow)

Editing triples: a pass only REPLACES operands and MARKS triples deleted;
compact() then removes them, renumbers, and fixes every (k) reference.
"""
from three_address_code import (BinOpTriple, RelOpTriple, AssignTriple, PrintTriple,
                                IfFalseTriple, TripleRef)
from cfg import build_cfg

# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
FIELDS = {BinOpTriple: ('arg1', 'arg2'), RelOpTriple: ('arg1', 'arg2'),
          AssignTriple: ('arg1',), PrintTriple: ('arg1',), IfFalseTriple: ('cond',)}


def fields(t):
    return FIELDS.get(type(t), ())


def is_const(op):
    return isinstance(op, str) and op.lstrip('-').isdigit()


def is_var(op):
    return isinstance(op, str) and not is_const(op)


def replace_uses(triples, old, new):
    for t in triples:
        for f in fields(t):
            if getattr(t, f) == old:
                setattr(t, f, new)


def compact(triples):
    """Drops deleted triples, renumbers the rest, fixes every TripleRef."""
    kept = [t for t in triples if not getattr(t, 'deleted', False)]
    new_index = {t.index: i for i, t in enumerate(kept)}
    for t in kept:
        for f in fields(t):
            op = getattr(t, f)
            if isinstance(op, TripleRef):
                setattr(t, f, TripleRef(new_index[op.index]))
        t.index = new_index[t.index]
    return kept


def show(triples):
    return "\n".join("    " + t.render() for t in triples)


def fmt(s):
    return "{" + ", ".join(sorted(s)) + "}"


# ----------------------------------------------------------------------
# 1. constant folding
# ----------------------------------------------------------------------
def fold(t):
    """The constant value of triple t (as text), or None if it isn't constant."""
    if not isinstance(t, (BinOpTriple, RelOpTriple)):
        return None
    if not (is_const(t.arg1) and is_const(t.arg2)):
        return None
    a, b = int(t.arg1), int(t.arg2)
    if t.op == '/':
        if b == 0:
            return None                       # leave the error for run time
        q = abs(a) // abs(b)                  # MIPS div truncates toward zero:
        return str(q if (a < 0) == (b < 0) else -q)   # -7/2 is -3, not Python's -4
    result = {'+': a + b, '-': a - b, '*': a * b, '<': a < b, '>': a > b, '<=': a <= b,
              '>=': a >= b, '==': a == b, '!=': a != b}[t.op]
    return str(int(result))                   # True/False -> 1/0


def constant_folding(triples):
    count = 0
    for t in triples:
        value = fold(t)
        if value is not None:
            replace_uses(triples, TripleRef(t.index), value)   # every use of (k) -> constant
            t.deleted = True
            count += 1
    return count


# ----------------------------------------------------------------------
# 2. copy propagation -- inside ONE basic block
# ----------------------------------------------------------------------
def copy_propagation(blocks):
    count = 0
    for b in blocks:
        copies = {}                            # x -> what x is a copy of (variable or constant)
        for t in b.triples:
            for f in fields(t):                # use the copy
                if is_var(getattr(t, f)) and getattr(t, f) in copies:
                    setattr(t, f, copies[getattr(t, f)])
                    count += 1
            if isinstance(t, AssignTriple):    # x changes: forget what involved x
                copies = {v: s for v, s in copies.items() if t.dest not in (v, s)}
                if isinstance(t.arg1, str) and t.arg1 != t.dest:
                    copies[t.dest] = t.arg1
    return count


# ----------------------------------------------------------------------
# 3. common subexpression elimination -- AVAILABLE EXPRESSIONS
#    A fact "c=x*y" means: variable c holds the value of x * y.
#    FORWARD, MUST:  IN[B] = intersection of OUT[pred],  OUT[B] = gen ∪ (IN - kill)
# ----------------------------------------------------------------------
def fact_of(triples, t):
    """`c = (k)` with (k) = `* x, y`  creates the fact  ('*', 'x', 'y', 'c')."""
    if isinstance(t, AssignTriple) and isinstance(t.arg1, TripleRef):
        e = triples[t.arg1.index]
        if isinstance(e, BinOpTriple) and isinstance(e.arg1, str) and isinstance(e.arg2, str) \
                and t.dest not in (e.arg1, e.arg2):
            return (e.op, e.arg1, e.arg2, t.dest)
    return None


def available_expressions(triples, blocks):
    facts = {f for t in triples for f in [fact_of(triples, t)] if f}
    killed = lambda var: {f for f in facts if var in (f[1], f[2], f[3])}
    gen, kill = {}, {}
    for b in blocks:
        g, k = set(), set()
        for t in b.triples:
            if isinstance(t, AssignTriple):
                g -= killed(t.dest)
                k |= killed(t.dest)
                f = fact_of(triples, t)
                if f:
                    g.add(f)
                    k.discard(f)
        gen[b.number], kill[b.number] = g, k
    IN = {b.number: set() for b in blocks}
    OUT = {b.number: set(facts) for b in blocks}       # start from "everything available"
    changed = True
    while changed:
        changed = False
        for b in blocks:
            new_in = set.intersection(*[OUT[p.number] for p in b.preds]) if b.preds else set()
            new_out = gen[b.number] | (new_in - kill[b.number])
            if (new_in, new_out) != (IN[b.number], OUT[b.number]):
                IN[b.number], OUT[b.number], changed = new_in, new_out, True
    return IN, OUT, gen, kill, killed


def common_subexpressions(triples, blocks):
    IN, OUT, gen, kill, killed = available_expressions(triples, blocks)
    count = 0
    for b in blocks:
        avail = set(IN[b.number])
        for t in b.triples:
            if isinstance(t, BinOpTriple) and isinstance(t.arg1, str) and isinstance(t.arg2, str):
                holders = sorted(f[3] for f in avail if f[:3] == (t.op, t.arg1, t.arg2))
                if holders:                                   # already computed: reuse it
                    replace_uses(triples, TripleRef(t.index), holders[0])
                    t.deleted = True
                    count += 1
            if isinstance(t, AssignTriple):
                avail -= killed(t.dest)
                f = fact_of(triples, t)
                if f:
                    avail.add(f)
    table = [f"    {b.name}  gen={fmt(map(fact_text, gen[b.number]))}  "
             f"kill={fmt(map(fact_text, kill[b.number]))}  IN={fmt(map(fact_text, IN[b.number]))}  "
             f"OUT={fmt(map(fact_text, OUT[b.number]))}" for b in blocks]
    return count, "\n".join(table)


def fact_text(f):
    return f"{f[3]}={f[1]}{f[0]}{f[2]}"


# ----------------------------------------------------------------------
# 4. dead code elimination -- LIVENESS
#    BACKWARD, MAY:  OUT[B] = union of IN[succ],  IN[B] = use ∪ (OUT - def)
#    (nothing is live after the program ends)
# ----------------------------------------------------------------------
def uses(t):
    return {getattr(t, f) for f in fields(t) if is_var(getattr(t, f))}


def liveness(blocks):
    use, define = {}, {}
    for b in blocks:
        u, d = set(), set()
        for t in b.triples:
            u |= uses(t) - d                   # read before being written in this block
            if isinstance(t, AssignTriple):
                d.add(t.dest)
        use[b.number], define[b.number] = u, d
    IN = {b.number: set() for b in blocks}
    OUT = {b.number: set() for b in blocks}
    changed = True
    while changed:
        changed = False
        for b in reversed(blocks):             # information flows backward
            new_out = set().union(*[IN[s.number] for s, _ in b.succs])
            new_in = use[b.number] | (new_out - define[b.number])
            if (new_in, new_out) != (IN[b.number], OUT[b.number]):
                IN[b.number], OUT[b.number], changed = new_in, new_out, True
    return IN, OUT, use, define


def delete_value(triples, ref):
    """Delete the computation (k) -- and whatever computed ITS operands."""
    t = triples[ref.index]
    t.deleted = True
    for f in fields(t):
        if isinstance(getattr(t, f), TripleRef):
            delete_value(triples, getattr(t, f))


def dead_code(triples, blocks):
    IN, OUT, use, define = liveness(blocks)
    count = 0
    for b in blocks:
        live = set(OUT[b.number])
        for t in reversed(b.triples):          # walk the block backward
            if getattr(t, 'deleted', False):
                continue
            if isinstance(t, AssignTriple) and t.dest not in live:
                t.deleted = True               # nobody reads this value: remove it
                count += 1
                if isinstance(t.arg1, TripleRef):
                    delete_value(triples, t.arg1)
                continue
            if isinstance(t, AssignTriple):
                live.discard(t.dest)
            live |= uses(t)
    table = [f"    {b.name}  use={fmt(use[b.number])}  def={fmt(define[b.number])}  "
             f"IN={fmt(IN[b.number])}  OUT={fmt(OUT[b.number])}" for b in blocks]
    return count, "\n".join(table)


# ----------------------------------------------------------------------
# the whole pipeline, printing every step
# ----------------------------------------------------------------------
def optimize(triples):
    print(f"==== before optimization ({len(triples)} triples)")
    print(show(triples))

    def local(triples):
        total = 0
        while True:                            # repeat: each pass can enable the other
            n = copy_propagation(build_cfg(triples)) + constant_folding(triples)
            triples = compact(triples)
            total += n
            if n == 0:
                return triples, total

    triples, n = local(triples)
    print(f"\n==== 1+2. constant folding + copy propagation: {n} change(s)")
    print(show(triples))

    blocks = build_cfg(triples)
    n, table = common_subexpressions(triples, blocks)
    triples, _ = local(compact(triples))       # CSE leaves copies like d = c behind
    print(f"\n==== 3. common subexpression elimination: {n} eliminated")
    print("  available expressions (c=x*y: c holds x*y):")
    print(table)
    print(show(triples))

    total, first_table = 0, None
    while True:                                # removing one assignment can kill another
        n, table = dead_code(triples, build_cfg(triples))
        first_table = first_table or table
        triples = compact(triples)
        total += n
        if n == 0:
            break
    print(f"\n==== 4. dead code elimination: {total} assignment(s) removed")
    print("  liveness (first round):")
    print(first_table)
    print(show(triples))
    return triples
