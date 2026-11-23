"""
Control-flow graph (CFG) of one function's triples.

Read docs/optimization_reference.md #1 first. Your work (part A):
find_leaders() and add_edges(). build_cfg() and the rendering are provided.

A BASIC BLOCK is a maximal run of triples that always executes from its
first triple to its last: control enters only at the top and leaves only
at the bottom. The CFG has one node per block, and an edge B -> C when
control can pass from the end of B directly to the start of C.

Leaders -- the first triple of each block (Week 9's
docs/control_flow_3ac_reference.md):
  1. the first triple of the function;
  2. every LabelTriple (something may jump to it);
  3. the triple right after a GotoTriple, IfFalseTriple or ReturnTriple.

Edges, decided by a block's LAST triple:
  goto L        -> the block starting with label L            (only that)
  if_false c L  -> the block of L ("false" edge) AND the next block ("true")
  RETURN        -> none: the function's exit
  anything else -> the next block (fall-through), if there is one

A CALL does NOT end a block: control comes back to the very next triple,
so within this function the call behaves like any other instruction.

Every TripleRef refers to a triple in the SAME block -- a statement's
triples never span a jump -- and the optimizer relies on that.
"""
from three_address_code import LabelTriple, GotoTriple, IfFalseTriple, ReturnTriple
from ir_utils import live_triples


class BasicBlock:
    def __init__(self, number, triples):
        self.number = number
        self.triples = triples          # the triple OBJECTS of this block, in order
        self.succs = []                 # successor BasicBlocks
        self.preds = []                 # predecessor BasicBlocks
        self.edge_labels = {}           # successor number -> "true"/"false" (if_false only)

    @property
    def name(self):
        return f"B{self.number}"

    def last(self):
        return self.triples[-1]

    def add_edge(self, succ, label=None):
        self.succs.append(succ)
        succ.preds.append(self)
        if label:
            self.edge_labels[succ.number] = label


class CFG:
    def __init__(self, blocks):
        self.blocks = blocks

    def entry(self):
        return self.blocks[0] if self.blocks else None

    def block_of_label(self, label):
        for b in self.blocks:
            first = b.triples[0]
            if isinstance(first, LabelTriple) and first.label == label:
                return b
        raise ValueError(f"no block starts with label {label}")


def find_leaders(triples):
    """
    TODO(week-12, part A): return the SORTED list of positions (0-based
    indexes into `triples`) of every leader -- rules 1-3 in the module
    docstring. Use a set while collecting: one triple can be a leader for
    two reasons (a label right after a goto). Rule 3 must not add a
    position past the end of the list.
    """
    raise NotImplementedError("implement cfg.find_leaders()")


def add_edges(cfg):
    """
    TODO(week-12, part A): connect the blocks, using each block's LAST
    triple (b.last()) and the "Edges" rules in the module docstring.
      - the next block in order is cfg.blocks[i + 1] (if there is one)
      - the block a label starts: cfg.block_of_label(label)
      - b.add_edge(succ) records both directions (succs and preds);
        for an if_false pass "false" (to the label's block) and "true"
        (to the next block) as the label -- the goldens print them.
    Order matters for the goldens: for if_false, add the "false" edge first.
    """
    raise NotImplementedError("implement cfg.add_edges()")


def build_cfg(triples):
    """Provided: splits the (non-deleted) triples at the leaders, then adds the edges."""
    triples = live_triples(triples)
    leaders = find_leaders(triples) + [len(triples)]
    blocks = [BasicBlock(n, triples[start:end])
              for n, (start, end) in enumerate(zip(leaders, leaders[1:]))]
    cfg = CFG(blocks)
    add_edges(cfg)
    return cfg


# ----------------------------------------------------------------------
# Rendering -- provided
# ----------------------------------------------------------------------
def _names(blocks):
    return " ".join(b.name for b in blocks) if blocks else "-"


def cfg_to_text(cfg):
    lines = []
    for b in cfg.blocks:
        succ_text =" ".join(s.name + (f"[{b.edge_labels[s.number]}]"
                                       if s.number in b.edge_labels else "")
                             for s in b.succs) or "exit"
        lines.append(f"{b.name}   preds: {_names(b.preds)}   succs: {succ_text}")
        for t in b.triples:
            lines.append(f"    {t.render()}")
    return "\n".join(lines)


def cfg_to_dot(cfg, graph_name="CFG"):
    lines = [f"digraph {graph_name} {{", "  node [shape=box, fontname=Courier];"]
    for b in cfg.blocks:
        body = "\\l".join(t.render().replace('"', '\\"') for t in b.triples) + "\\l"
        lines.append(f'  {b.name} [label="{b.name}\\n{body}"];')
    for b in cfg.blocks:
        for s in b.succs:
            label = b.edge_labels.get(s.number)
            attr = f' [label="{label}"]' if label else ""
            lines.append(f"  {b.name} -> {s.name}{attr};")
    lines.append("}")
    return "\n".join(lines) + "\n"
