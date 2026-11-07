"""
Query routing in a distributed key-value store (KVS) built on a Skip Graph.

Each node keeps only:
  - its label (position in the ordered key space)
  - the key-value pairs in its managed range [label, next label)
  - routing information: left/right neighbours at every level

A query is forwarded node to node using only that local information.
Run:  python skip_graph_kvs.py
"""

from __future__ import annotations


class Node:
    def __init__(self, label: int, membership: str):
        self.label = label
        self.membership = membership          # random bits, e.g. "01"
        self.max_level = len(membership)
        self.L: list[Node | None] = [None] * (self.max_level + 1)
        self.R: list[Node | None] = [None] * (self.max_level + 1)
        self.range_end: float = float("inf")  # set after the list is built
        self.data: dict[int, str] = {}

    def owns(self, key: int) -> bool:
        return self.label <= key < self.range_end

    def __repr__(self) -> str:
        return f"Node({self.label})"


def build_skip_graph(specs: list[tuple[int, str]]) -> list[Node]:
    """Create nodes and link them level by level by membership-vector prefix."""
    nodes = sorted((Node(lbl, mv) for lbl, mv in specs), key=lambda n: n.label)
    for i, n in enumerate(nodes):                       # managed ranges
        n.range_end = nodes[i + 1].label if i + 1 < len(nodes) else float("inf")
    max_level = max(n.max_level for n in nodes)
    for level in range(max_level + 1):
        groups: dict[str, list[Node]] = {}
        for n in nodes:
            if n.max_level >= level:
                groups.setdefault(n.membership[:level], []).append(n)
        for group in groups.values():                   # already sorted
            for a, b in zip(group, group[1:]):
                a.R[level], b.L[level] = b, a
    return nodes


def route(entry: Node, target: int, trace: list[str]) -> Node:
    """Forward a query for `target` until it reaches the owning node."""
    node, level = entry, entry.max_level
    trace.append(f"start at {node.label} (level {level})")
    while not node.owns(target):
        if target > node.label:
            nxt = node.R[level]
            ok = nxt is not None and nxt.label <= target
        else:
            nxt = node.L[level]
            # moving left: never pass the target, except the final level-0 step
            # into the left neighbour, which then owns it
            ok = nxt is not None and (nxt.label >= target or level == 0)
        if ok:
            trace.append(f"  level {level}: {node.label} -> {nxt.label}")
            node = nxt
        elif level > 0:
            trace.append(f"  level {level}: cannot move, drop to level {level - 1}")
            level -= 1
        else:
            break                                       # target below the first node
    trace.append(f"owner reached: {node.label} manages "
                 f"[{node.label}, {node.range_end})")
    return node


def get(entry: Node, key: int) -> str | None:
    trace: list[str] = []
    owner = route(entry, key, trace)
    print("\n".join(trace))
    return owner.data.get(key)


def range_query(entry: Node, low: int, high: int) -> list[tuple[int, str]]:
    """Find the node that owns `low`, then walk level-0 right links."""
    trace: list[str] = []
    node: Node | None = route(entry, low, trace)
    print("\n".join(trace))
    result: list[tuple[int, str]] = []
    visited = []
    while node is not None and node.label <= high:
        visited.append(node.label)
        result += sorted((k, v) for k, v in node.data.items() if low <= k <= high)
        node = node.R[0]
    print(f"  level-0 walk over nodes {visited}")
    return result


def put(nodes: list[Node], key: int, value: str) -> None:
    """Setup helper: place data directly on its owner."""
    for n in nodes:
        if n.owns(key):
            n.data[key] = value
            return


if __name__ == "__main__":
    # 8 nodes, 2-bit membership vectors (levels 0, 1, 2)
    specs = [(5, "00"), (13, "10"), (21, "01"), (30, "11"),
             (45, "00"), (62, "10"), (71, "01"), (80, "11")]
    nodes = build_skip_graph(specs)
    by_label = {n.label: n for n in nodes}

    for k, v in [(8, "lemon"), (31, "apple"), (37, "grape"), (42, "pear"),
                 (50, "mango"), (66, "kiwi"), (73, "plum"), (85, "fig")]:
        put(nodes, k, v)

    print("Routing table (level: left / right)")
    for n in nodes:
        links = ", ".join(
            f"L{lv}: {n.L[lv].label if n.L[lv] else '-'} / "
            f"{n.R[lv].label if n.R[lv] else '-'}"
            for lv in range(n.max_level, -1, -1))
        print(f"  {n.label:>2} [{n.membership}]  {links}")

    print("\nExact query: get(37) from entry node 5")
    print("  result:", get(by_label[5], 37))

    print("\nExact query: get(8) from entry node 80")
    print("  result:", get(by_label[80], 8))

    print("\nRange query: keys 40..75 from entry node 13")
    print("  result:", range_query(by_label[13], 40, 75))
