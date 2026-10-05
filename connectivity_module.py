"""
connectivity_module.py
======================
Graph traversal with BFS and DFS (both written by hand).

  BFS  - visits intersections level by level ("all neighbours first").
         Uses a QUEUE  (first in, first out).
  DFS  - follows one road as far as possible, then backtracks.
         Uses a STACK  (last in, first out).

To make results reproducible, neighbours are always visited in alphabetical order.
Both algorithms only reach intersections that are CONNECTED to the start, so they
also tell us which parts of the city are cut off.
"""
from collections import deque


def bfs(adj, start, trace=True):
    if start not in adj:
        raise ValueError(f"Starting intersection '{start}' does not exist in the network.")
    visited = {start}
    queue = deque([start])
    order, parent, level, steps = [], {start: None}, {start: 0}, []

    while queue:
        node = queue.popleft()                 # take from the FRONT
        order.append(node)
        for nb in sorted(adj[node]):
            if nb not in visited:
                visited.add(nb)                # mark when we ADD to the queue
                parent[nb] = node
                level[nb] = level[node] + 1
                queue.append(nb)               # add to the BACK
        if trace:
            steps.append({"step": len(order), "visit": node,
                          "container_after": list(queue)})

    return _package("BFS", start, order, parent, level, steps, "Queue after this step")


def dfs(adj, start, trace=True):
    """Iterative DFS with an explicit stack (gives the same order as the recursive version)."""
    if start not in adj:
        raise ValueError(f"Starting intersection '{start}' does not exist in the network.")
    visited, order, parent, level, steps = set(), [], {}, {}, []
    stack = [(start, None)]                    # (node, who pushed it)

    while stack:
        node, came_from = stack.pop()          # take from the TOP
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        parent[node] = came_from
        level[node] = 0 if came_from is None else level[came_from] + 1
        # push in reverse so the alphabetically-first neighbour is popped first
        for nb in sorted(adj[node], reverse=True):
            if nb not in visited:
                stack.append((nb, node))
        if trace:
            steps.append({"step": len(order), "visit": node,
                          "container_after": [n for n, _ in stack]})

    return _package("DFS", start, order, parent, level, steps, "Stack after this step (top = right)")


def _package(name, start, order, parent, level, steps, container_label):
    tree_edges = [(parent[n], n) for n in order if parent[n] is not None]
    return {"algorithm": name, "start": start, "order": order, "parent": parent,
            "level": level, "tree_edges": tree_edges, "trace": steps,
            "container_label": container_label}


def connected_components(adj):
    """List of groups of intersections that can reach each other."""
    seen, components = set(), []
    for node in adj:
        if node not in seen:
            group = bfs(adj, node, trace=False)["order"]
            seen.update(group)
            components.append(group)
    return components


def is_connected(adj):
    return len(connected_components(adj)) <= 1


def check_path_exists(adj, source, target):
    """Check if target is reachable from source using BFS.
    Returns (is_reachable, shortest_hop_path)."""
    if source not in adj:
        raise ValueError(f"Source intersection '{source}' does not exist in the network.")
    if target not in adj:
        raise ValueError(f"Target intersection '{target}' does not exist in the network.")
    if source == target:
        return True, [source]
    res = bfs(adj, source, trace=False)
    if target not in res["parent"]:
        return False, []
    # Reconstruct path using parent pointers
    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = res["parent"].get(curr)
    path.reverse()
    return True, path
