"""
Dead code elimination via LIVENESS analysis.

Your work (part D): use_def(), liveness() and eliminate_dead_code().
uses_defs() (one triple's uses and definition) is provided.

A variable is LIVE at a point if some path from that point USES it
before (re)defining it. An assignment `x = ...` whose x is dead right
after it -- on every path -- computes a value nobody will ever read: it
can be removed, together with the pure computation feeding it.

Data-flow equations -- BACKWARD, MAY (union), per block B:
    OUT[B] = union of IN[S] over all successors S
             (a block with no successors -- the exit -- has OUT = all globals:
              after the function returns, its caller may read any global)
    IN[B]  = use[B]  union  (OUT[B] - def[B])
  use[B]: variables read in B before any assignment to them in B
  def[B]: variables assigned in B
Start every IN at {} and iterate until nothing changes.

Calls: the callee may READ any global, so a CALL uses every global. It
does not count as DEFINING them (it may or may not assign them).

What is never removed: an assignment to a GLOBAL (another function, or
the caller, may read it), and a CALL (it may print or change globals) --
if `x = f();` is dead, only the assignment goes and the call stays.
"""
from three_address_code import AssignTriple, CallTriple, TripleRef
from ir_utils import is_deleted, delete, operands, is_variable, delete_unused_value


def uses_defs(triple, global_names):
    """(variables this triple reads, variable it assigns or None)."""
    uses = {op for op in operands(triple) if is_variable(op)}
    if isinstance(triple, CallTriple):
        uses |= global_names
    defined = triple.dest if isinstance(triple, AssignTriple) else None
    return uses, defined


def use_def(block, global_names):
    """
    TODO(week-12, part D): return (use, def) for one block.
    Walk its non-deleted triples FORWARD with uses_defs(t, global_names):
      use: a variable read BEFORE any assignment to it in this block
           (so add `uses - def-so-far`)
      def: every variable assigned in this block
    """
    raise NotImplementedError("implement opt_dce.use_def()")


def liveness(cfg, global_names):
    """
    TODO(week-12, part D): solve the equations in the module docstring.
    Return (IN, OUT, use, def), dicts from block number to a set of names.

      use/def per block with use_def()
      initialise IN[b] = OUT[b] = set() for every block
      repeat until a full sweep changes nothing -- visiting the blocks in
      REVERSE order (reversed(cfg.blocks)): information flows backward:
          OUT[b] = UNION of IN[s] over b.succs,
                   or set(global_names) when b has no successors (the exit)
          IN[b]  = use[b] | (OUT[b] - def[b])
    """
    raise NotImplementedError("implement opt_dce.liveness()")


def eliminate_dead_code(triples, cfg, global_names):
    """
    TODO(week-12, part D): ONE round of dead code elimination. Returns
    (number removed, IN, OUT, use, def) -- the last four from liveness().

    For each block, start from live = set(OUT[b.number]) and walk its
    non-deleted triples BACKWARD (reversed(b.triples)):
      - an AssignTriple whose dest is NOT in live and NOT a global is dead:
            delete(t); count it;
            if t.arg1 is a TripleRef: delete_unused_value(triples, t.arg1.index)
              (removes the pure computation that fed it -- or, for a call,
               keeps the call and just drops its result)
            and continue: a removed triple reads nothing.
      - any other triple: uses, defined = uses_defs(t, global_names);
            remove `defined` from live (if not None), THEN add `uses`.
            (Order matters: in `x = x + 1`, x is live BEFORE the triple.)
    The pipeline calls this repeatedly until a round removes nothing.
    """
    raise NotImplementedError("implement opt_dce.eliminate_dead_code()")
