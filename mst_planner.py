"""
mst_planner.py
==============
Minimum Spanning Tree (MST) with Prim's and Kruskal's algorithms (by hand).

Infrastructure question: "What is the cheapest set of roads that still connects
every intersection?"  An MST always has exactly (V - 1) roads and no loops.

  Prim    - grows ONE tree from a start intersection, always adding the
            cheapest road that reaches a new intersection.  (heap)
  Kruskal - sorts ALL roads by cost and adds the cheapest one that does not
            create a loop.  A Union-Find structure detects loops.  (sorting)

If the city is not fully connected, Prim only covers the start intersection's
area, while Kruskal returns a minimum spanning FOREST (one tree per area).
"""
import heapq

from graph_model import unique_edges


# --------------------------------------------------------------------------
# Prim
# --------------------------------------------------------------------------
def prim(adj, start=None, trace=True):
    if not adj:
        return {"algorithm": "Prim", "edges": [], "total_cost": 0, "steps": [],
                "spanning": True, "covered": []}
    if start is not None and start not in adj:
        raise ValueError(f"Starting intersection '{start}' does not exist in the network.")
    if start is None:
        start = next(iter(adj))

    in_tree = {start}
    heap = [(cost, start, v) for v, cost in adj[start].items()]
    heapq.heapify(heap)                      # candidate roads leaving the tree
    edges, steps, total = [], [], 0

    while heap and len(in_tree) < len(adj):
        cost, u, v = heapq.heappop(heap)     # cheapest candidate road
        if v in in_tree:                     # both ends already connected -> would make a loop
            if trace:
                steps.append({"road": f"{u} — {v}", "cost": cost,
                              "decision": "Skipped (both ends already in the tree)",
                              "total": total})
            continue
        in_tree.add(v)
        edges.append((u, v, cost))
        total += cost
        if trace:
            steps.append({"road": f"{u} — {v}", "cost": cost,
                          "decision": f"Selected (adds {v})", "total": total})
        for nb, c in adj[v].items():
            if nb not in in_tree:
                heapq.heappush(heap, (c, v, nb))

    return {"algorithm": "Prim", "start": start, "edges": edges, "total_cost": total,
            "steps": steps, "spanning": len(in_tree) == len(adj),
            "covered": sorted(in_tree)}


# --------------------------------------------------------------------------
# Kruskal (with Union-Find)
# --------------------------------------------------------------------------
class UnionFind:
    """Keeps track of which intersections are already connected to each other."""

    def __init__(self, items):
        self.parent = {x: x for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path compression
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False                     # already connected -> adding would make a loop
        self.parent[ra] = rb
        return True


def kruskal(adj, trace=True):
    roads = sorted(unique_edges(adj), key=lambda e: (e[2], e[0], e[1]))   # cheapest first
    uf = UnionFind(adj)
    edges, steps, total = [], [], 0

    for u, v, cost in roads:
        if uf.union(u, v):
            edges.append((u, v, cost))
            total += cost
            decision = "Accepted"
        else:
            decision = "Rejected (would form a loop)"
        if trace:
            steps.append({"road": f"{u} — {v}", "cost": cost,
                          "decision": decision, "total": total})
        if len(edges) == len(adj) - 1:
            break

    trees = len(adj) - len(edges)            # forest with k trees has V-k edges
    return {"algorithm": "Kruskal", "edges": edges, "total_cost": total,
            "steps": steps, "spanning": trees <= 1, "trees": trees}
