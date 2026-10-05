"""
route_planner.py
================
Shortest-route algorithms, written by hand so every line can be explained:

  * dijkstra()      - greedy, fast, needs NON-NEGATIVE costs
  * bellman_ford()  - repeated relaxation, also works with negative costs

Both work on the plain adjacency dictionary  adj = {node: {neighbour: cost}}.
Both record their "steps" so the web page can show the calculation.

Key idea shared by both algorithms - RELAXATION:
    "Is it cheaper to reach v by going through u than the best way I know so far?"
        if dist[u] + cost(u, v) < dist[v]:
            dist[v] = dist[u] + cost(u, v)      # better route found
            prev[v] = u                         # remember where we came from
"""
import heapq

INF = float("inf")


# --------------------------------------------------------------------------
# Dijkstra
# --------------------------------------------------------------------------
def dijkstra(adj, source, target=None, trace=True):
    """
    Dijkstra's algorithm with a priority queue (heap).

    1. dist[source] = 0, every other intersection = infinity.
    2. Repeatedly take the UNFINISHED intersection with the smallest distance.
       Its distance is now final (greedy choice - this is why costs can't be negative).
    3. Relax all roads leaving it.
    4. Stop when the queue is empty (or when `target` is finished).

    trace=True records every step for the web page. Pass trace=False for a pure
    (faster) run, which is what the benchmark does so the comparison is fair.

    Returns a dict with dist, prev (to rebuild the path) and steps (for display).
    """
    if source not in adj:
        raise ValueError(f"Source intersection '{source}' does not exist in the network.")
    if target is not None and target not in adj:
        raise ValueError(f"Target intersection '{target}' does not exist in the network.")

    dist = {node: INF for node in adj}
    prev = {node: None for node in adj}
    dist[source] = 0
    heap = [(0, source)]        # (distance, node) - heapq always pops the smallest
    settled = set()             # intersections whose distance is final
    steps = []

    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:        # stale heap entry (we found a shorter one earlier)
            continue
        settled.add(u)

        relaxations = []
        for v, cost in adj[u].items():
            if v in settled:
                continue
            candidate = d + cost
            improved = candidate < dist[v]
            if trace:
                relaxations.append({
                    "neighbor": v,
                    "edge_cost": cost,
                    "old_distance": dist[v],
                    "new_distance": candidate,
                    "updated": improved,
                })
            if improved:
                dist[v] = candidate
                prev[v] = u
                heapq.heappush(heap, (candidate, v))

        if trace:
            steps.append({
                "step": len(steps) + 1,
                "node": u,
                "distance": d,
                "relaxations": relaxations,
                "dist_snapshot": dict(dist),
                "settled": sorted(settled),
            })
        if target is not None and u == target:
            break

    return {"algorithm": "Dijkstra", "source": source, "dist": dist,
            "prev": prev, "steps": steps, "negative_cycle": False}


# --------------------------------------------------------------------------
# Bellman-Ford
# --------------------------------------------------------------------------
def bellman_ford(adj, source, trace=True):
    """
    Bellman-Ford algorithm.

    1. dist[source] = 0, everything else = infinity.
    2. Repeat (V - 1) times: relax EVERY road (in both directions).
       After pass k, all shortest routes that use at most k roads are correct.
    3. One extra check: if any road can STILL be relaxed, the graph has a
       negative cycle (a loop that keeps making the trip cheaper forever).

    Stops early if a whole pass changes nothing.
    trace=False skips the step recording (used by the benchmark).
    """
    if source not in adj:
        raise ValueError(f"Source intersection '{source}' does not exist in the network.")

    arcs = [(u, v, cost) for u in adj for v, cost in adj[u].items()]
    dist = {node: INF for node in adj}
    prev = {node: None for node in adj}
    dist[source] = 0
    passes = []

    for pass_no in range(1, len(adj)):
        updates, changed = [], False
        for u, v, cost in arcs:
            if dist[u] != INF and dist[u] + cost < dist[v]:
                if trace:
                    updates.append({"from": u, "to": v, "edge_cost": cost,
                                    "old_distance": dist[v],
                                    "new_distance": dist[u] + cost})
                dist[v] = dist[u] + cost
                prev[v] = u
                changed = True
        if trace:
            passes.append({"pass": pass_no, "updates": updates,
                           "dist_snapshot": dict(dist)})
        if not changed:
            break

    negative_cycle = any(dist[u] != INF and dist[u] + cost < dist[v]
                         for u, v, cost in arcs)
    return {"algorithm": "Bellman-Ford", "source": source, "dist": dist,
            "prev": prev, "passes": passes, "negative_cycle": negative_cycle}


# --------------------------------------------------------------------------
# Helpers shared by the pages
# --------------------------------------------------------------------------
def build_path(prev, source, target):
    """Follow the `prev` pointers backwards from target to source.
    Returns [source, ..., target] or [] when there is no route."""
    path, node, guard = [], target, len(prev) + 1
    while node is not None and guard > 0:
        path.append(node)
        node = prev.get(node)
        guard -= 1
    path.reverse()
    return path if path and path[0] == source else []


def path_cost(adj, path):
    """Total cost of a list of intersections, using the roads in `adj`."""
    return sum(adj[a][b] for a, b in zip(path, path[1:]))


def find_route(adj, source, target, algorithm="Dijkstra"):
    """Run the chosen algorithm and package everything the page needs."""
    if source not in adj:
        raise ValueError(f"Source intersection '{source}' does not exist in the network.")
    if target not in adj:
        raise ValueError(f"Target intersection '{target}' does not exist in the network.")

    if source == target:
        return {
            "algorithm": algorithm,
            "source": source,
            "target": target,
            "path": [source],
            "found": True,
            "cost": 0,
            "segments": [],
            "run": {
                "algorithm": algorithm,
                "source": source,
                "dist": {node: (0 if node == source else INF) for node in adj},
                "prev": {node: None for node in adj},
                "steps": [],
                "passes": [],
                "negative_cycle": False,
            },
        }

    if algorithm == "Bellman-Ford":
        run = bellman_ford(adj, source)
    else:
        run = dijkstra(adj, source, target)

    path = build_path(run["prev"], source, target)
    if run["negative_cycle"]:
        path = []
    segments, running = [], 0
    for a, b in zip(path, path[1:]):
        running += adj[a][b]
        segments.append({"from": a, "to": b, "cost": adj[a][b], "cumulative": running})

    return {
        "algorithm": run["algorithm"],
        "source": source,
        "target": target,
        "path": path,
        "found": bool(path),
        "cost": run["dist"][target] if path else None,
        "segments": segments,
        "run": run,
    }
