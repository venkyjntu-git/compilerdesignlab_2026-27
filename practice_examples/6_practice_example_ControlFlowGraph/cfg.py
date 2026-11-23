"""
Control-Flow Graph (CFG) from triples, in three steps:

  1. LEADERS -- the first triple of each basic block:
       - the first triple of the program
       - every label                      (something may jump to it)
       - the triple after goto / if_false (the jump may skip it)
  2. BASIC BLOCKS -- from each leader up to (not including) the next one.
  3. EDGES -- decided by the LAST triple of each block:
       goto L        ->  block of L
       if_false c L  ->  block of L   (condition FALSE)
                         next block   (condition TRUE: fall through)
       anything else ->  next block   (fall through)
"""
from three_address_code import LabelTriple, GotoTriple, IfFalseTriple


class BasicBlock:
    def __init__(self, number, triples):
        self.number = number
        self.triples = triples
        self.succs = []     # list of (BasicBlock, edge label)
        self.preds = []

    @property
    def name(self):
        return f"B{self.number}"


def find_leaders(triples):
    leaders = {0} if triples else set()
    for i, t in enumerate(triples):
        if isinstance(t, LabelTriple):
            leaders.add(i)
        if isinstance(t, (GotoTriple, IfFalseTriple)) and i + 1 < len(triples):
            leaders.add(i + 1)
    return sorted(leaders)


def build_cfg(triples):
    leaders = find_leaders(triples)
    bounds = leaders + [len(triples)]
    blocks = [BasicBlock(n, triples[bounds[n]:bounds[n + 1]]) for n in range(len(leaders))]

    def block_of(label):
        for b in blocks:
            if isinstance(b.triples[0], LabelTriple) and b.triples[0].label == label:
                return b

    def connect(b, succ, how=""):
        b.succs.append((succ, how))
        succ.preds.append(b)

    for i, b in enumerate(blocks):
        last = b.triples[-1]
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        if isinstance(last, GotoTriple):
            connect(b, block_of(last.label))
        elif isinstance(last, IfFalseTriple):
            connect(b, block_of(last.label), "false")
            if nxt:
                connect(b, nxt, "true")
        elif nxt:
            connect(b, nxt)
    return blocks


def cfg_to_text(blocks):
    lines = []
    for b in blocks:
        succ = " ".join(s.name + (f"[{how}]" if how else "") for s, how in b.succs) or "exit"
        preds = " ".join(p.name for p in b.preds) or "-"
        lines.append(f"{b.name}   preds: {preds}   succs: {succ}")
        lines.extend("    " + t.render() for t in b.triples)
    return "\n".join(lines)


def cfg_to_dot(blocks, filename="cfg.dot"):
    """Render with:  dot -Tpng cfg.dot -o cfg.png"""
    lines = ["digraph CFG {", "  node [shape=box, fontname=Courier];"]
    for b in blocks:
        body = "\\l".join(t.render() for t in b.triples) + "\\l"
        lines.append(f'  {b.name} [label="{b.name}\\n{body}"];')
    for b in blocks:
        for s, how in b.succs:
            lines.append(f'  {b.name} -> {s.name}' + (f' [label="{how}"]' if how else "") + ";")
    lines.append("}")
    with open(filename, "w") as f:
        f.write("\n".join(lines) + "\n")
