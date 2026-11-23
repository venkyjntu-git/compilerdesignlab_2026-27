"""
Global common subexpression elimination via AVAILABLE EXPRESSIONS.

Your work (part C): gen_kill() and available_expressions(). The facts
(fact_of, all_facts), the kill helpers, and the rewrite itself
(eliminate_common_subexpressions) are provided.

An expression `a op b` is AVAILABLE at a point p, held in variable x,
when on EVERY path to p the statement `x = a op b` was executed and
since then none of a, b, x was changed. At such a point a later
`a op b` need not be computed again: x already holds its value.

What a "fact" is here. Textbook CSE keeps the value in a compiler
temporary. Our triples have no named temporaries -- a triple's value
lives only inside its own statement (Week 9's register invariant) -- so
the value is reused from the VARIABLE it was assigned to. A fact is

    (op, arg1, arg2, type, holder)      e.g.  ('+', 'a', 'b', INT, 'x')

created by the triple pair   (k) + a, b : INT    (k+1) x = (k)
whose operands are both variables/constants (not TripleRefs).

Data-flow equations -- FORWARD, MUST (intersection), per block B:
    IN[entry] = {}
    IN[B]     = intersection of OUT[P] over all predecessors P
    OUT[B]    = gen[B]  union  (IN[B] - kill[B])
Start every OUT (except the entry's) at the FULL set of facts -- the
"must" analysis' optimistic start -- and iterate until nothing changes.

What kills a fact:  an assignment to arg1, arg2 or holder; and a CALL,
for any fact naming a GLOBAL (the callee may assign globals).
"""
from three_address_code import BinOpTriple, AssignTriple, CallTriple, TripleRef
from ir_utils import is_deleted, delete, replace_uses


def fact_of(triples, assign):
    """The fact created by `assign` (an AssignTriple), or None."""
    if not isinstance(assign.arg1, TripleRef):
        return None
    t = triples[assign.arg1.index]
    if not isinstance(t, BinOpTriple) or is_deleted(t):
        return None
    if isinstance(t.arg1, TripleRef) or isinstance(t.arg2, TripleRef):
        return None
    if assign.dest in (t.arg1, t.arg2):         # x = x + 1: x no longer holds x + 1
        return None
    return (t.op, t.arg1, t.arg2, t.result_type, assign.dest)


def all_facts(triples):
    facts = set()
    for t in triples:
        if isinstance(t, AssignTriple) and not is_deleted(t):
            f = fact_of(triples, t)
            if f is not None:
                facts.add(f)
    return facts


def killed_by_assign(facts, var):
    return {f for f in facts if var in (f[1], f[2], f[4])}


def killed_by_call(facts, global_names):
    return {f for f in facts if {f[1], f[2], f[4]} & global_names}


def gen_kill(triples, block, universe, global_names):
    """
    TODO(week-12, part C): return (gen, kill) for one block, two sets of
    facts such that OUT[B] = gen | (IN[B] - kill) holds for ANY IN[B].

    Walk the block's non-deleted triples in order, starting from two
    empty sets:
      - AssignTriple to x:  k = killed_by_assign(universe, t.dest);
            gen -= k ; kill |= k       (x, or an operand, just changed)
            then f = fact_of(triples, t); if f is not None:
            gen.add(f) ; kill.discard(f)   (re-created after the kill)
      - CallTriple:         k = killed_by_call(universe, global_names);
            gen -= k ; kill |= k
    """
    raise NotImplementedError("implement opt_cse.gen_kill()")


def available_expressions(triples, cfg, global_names):
    """
    TODO(week-12, part C): solve the equations in the module docstring.
    Return (IN, OUT, gen, kill, universe) -- the first four are dicts
    from block NUMBER (b.number) to a set of facts.

      universe = all_facts(triples)
      gen/kill per block with gen_kill()
      initialise: IN[b] = set() for every block,
                  OUT[b] = set(universe) for every block   <- the "must" start
      repeat until a full sweep over cfg.blocks changes nothing:
          IN[b]  = set() for the entry block (cfg.entry()) and any block with
                   no predecessors, else the INTERSECTION of OUT[p] over b.preds
                   (set.intersection(*[...]) )
          OUT[b] = gen[b] | (IN[b] - kill[b])

    Why start OUT at the full universe? Try starting at set() on test28's
    loop-free f, then on a program with a loop: docs/optimization_reference.md #3.
    """
    raise NotImplementedError("implement opt_cse.available_expressions()")


def eliminate_common_subexpressions(triples, cfg, global_names):
    """
    Replaces each BinOp `a op b` that is available on entry to it by the
    variable holding it. Returns (number eliminated, IN, OUT, gen, kill).
    """
    IN, OUT, gen, kill, universe = available_expressions(triples, cfg, global_names)
    eliminated = 0
    for b in cfg.blocks:
        avail = set(IN[b.number])
        for t in b.triples:
            if is_deleted(t):
                continue
            if isinstance(t, BinOpTriple) and not isinstance(t.arg1, TripleRef) \
                    and not isinstance(t.arg2, TripleRef):
                key = (t.op, t.arg1, t.arg2, t.result_type)
                holders = sorted(f[4] for f in avail if f[:4] == key)
                if holders:
                    replace_uses(triples, TripleRef(t.index), holders[0])
                    delete(t)
                    eliminated += 1
                    continue
            if isinstance(t, AssignTriple):
                avail -= killed_by_assign(universe, t.dest)
                f = fact_of(triples, t)
                if f is not None:
                    avail.add(f)
            elif isinstance(t, CallTriple):
                avail -= killed_by_call(universe, global_names)
    return eliminated, IN, OUT, gen, kill
