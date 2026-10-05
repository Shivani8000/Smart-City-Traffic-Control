"""
benchmark.py
============
REAL experiments for the "Algorithm Comparison" section. Nothing here is invented:
every number comes from running the algorithms on this computer.

For each network size (10, 25, 50, 100 intersections) we
  1. build a random connected road network (fixed seed -> repeatable graph),
  2. run every algorithm, timing it with time.perf_counter(),
  3. measure peak extra memory with tracemalloc,
  4. record what each algorithm produced.

Fairness: the algorithms are run with trace=False, i.e. WITHOUT the step-by-step
recording that the web pages use for teaching, so only the algorithm itself is timed.

Timing method: each algorithm is run repeatedly for at least `min_seconds`
and the AVERAGE time of one run is reported (a single run of a small graph is
too quick to measure reliably).
Times differ from computer to computer; the *pattern* (which is faster) is what matters.
"""
import random
import time
import tracemalloc

import pandas as pd

from connectivity_module import bfs, dfs
from graph_model import RoadNetwork
from mst_planner import kruskal, prim
from route_planner import bellman_ford, build_path, dijkstra, path_cost

SIZES = (10, 25, 50, 100)
ALGORITHMS = ["BFS", "DFS", "Dijkstra", "Bellman-Ford", "Prim", "Kruskal"]


def random_network(n, seed=42, extra_ratio=1.0, max_cost=20):
    """Random CONNECTED network: first a random spanning tree (guarantees
    connectivity), then about n*extra_ratio additional random roads."""
    rng = random.Random(seed * 1000 + n)
    names = [f"J{i}" for i in range(1, n + 1)]
    net = RoadNetwork()
    for name in names:
        net.add_intersection(name, pos=(0, 0))
    for i in range(1, n):
        net.add_road(names[i], names[rng.randrange(i)], rng.randint(1, max_cost))
    wanted, added, tries = int(n * extra_ratio), 0, 0
    while added < wanted and tries < wanted * 20:
        tries += 1
        a, b = rng.sample(names, 2)
        if not net.has_edge(a, b):
            net.add_road(a, b, rng.randint(1, max_cost))
            added += 1
    return net


def measure_time_ms(fn, min_seconds=0.03, max_runs=200000):
    fn()                                            # warm-up run (not counted)
    runs, start = 0, time.perf_counter()
    while True:
        fn()
        runs += 1
        elapsed = time.perf_counter() - start
        if elapsed >= min_seconds or runs >= max_runs:
            return elapsed / runs * 1000


def measure_peak_kb(fn):
    tracemalloc.start()
    fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024


def _make_call(name, adj, s):
    return {
        "BFS": lambda: bfs(adj, s, trace=False),
        "DFS": lambda: dfs(adj, s, trace=False),
        "Dijkstra": lambda: dijkstra(adj, s, trace=False),
        "Bellman-Ford": lambda: bellman_ford(adj, s, trace=False),
        "Prim": lambda: prim(adj, s, trace=False),
        "Kruskal": lambda: kruskal(adj, trace=False),
    }[name]


def _summarise(name, adj, s, t, result):
    """(roads in the result, cost of the result)."""
    if name in ("BFS", "DFS"):
        path = build_path(result["parent"], s, t)
    elif name in ("Dijkstra", "Bellman-Ford"):
        path = build_path(result["prev"], s, t)
    else:                                            # Prim / Kruskal: the whole tree
        return len(result["edges"]), result["total_cost"]
    return (len(path) - 1, path_cost(adj, path)) if path else (None, None)


def run_all(net, source, target, min_seconds=0.03):
    """Time + memory + result of all six algorithms on ONE network."""
    adj = net.adj
    rows = []
    for name in ALGORITHMS:
        call = _make_call(name, adj, source)
        roads_in_result, cost = _summarise(name, adj, source, target, call())
        rows.append({
            "Intersections": net.node_count,
            "Roads": net.edge_count,
            "Algorithm": name,
            "Time (ms)": measure_time_ms(call, min_seconds),
            "Peak memory (KB)": measure_peak_kb(call),
            "Roads in result": roads_in_result,
            "Cost of result": cost,
        })
    return pd.DataFrame(rows)


def run_benchmark(sizes=SIZES, seed=42, min_seconds=0.03):
    frames = []
    for n in sizes:
        net = random_network(n, seed)
        frames.append(run_all(net, "J1", f"J{n}", min_seconds))
    return pd.concat(frames, ignore_index=True)


def agreement_report(df):
    """Sanity check: Dijkstra and Bellman-Ford must find the same cost, and
    Prim and Kruskal must find the same total (different trees are possible on ties)."""
    rows = []
    for n, part in df.groupby("Intersections"):
        cost = part.set_index("Algorithm")["Cost of result"]
        rows.append({
            "Intersections": n,
            "Dijkstra = Bellman-Ford": bool(cost["Dijkstra"] == cost["Bellman-Ford"]),
            "Prim = Kruskal": bool(cost["Prim"] == cost["Kruskal"]),
        })
    return pd.DataFrame(rows)


def compare_shortest_path_algos(net, source, target, min_seconds=0.03):
    """Direct head-to-head comparison between Dijkstra and Bellman-Ford."""
    adj = net.adj
    dijkstra_fn = lambda: dijkstra(adj, source, target, trace=False)
    bellman_fn = lambda: bellman_ford(adj, source, trace=False)

    t_dijkstra = measure_time_ms(dijkstra_fn, min_seconds)
    t_bellman = measure_time_ms(bellman_fn, min_seconds)

    m_dijkstra = measure_peak_kb(dijkstra_fn)
    m_bellman = measure_peak_kb(bellman_fn)

    run_d = dijkstra(adj, source, target, trace=True)
    run_bf = bellman_ford(adj, source, trace=True)

    path_d = build_path(run_d["prev"], source, target)
    path_bf = build_path(run_bf["prev"], source, target)

    cost_d = run_d["dist"][target] if path_d else None
    cost_bf = run_bf["dist"][target] if path_bf else None

    steps_d = len(run_d["steps"])
    relaxations_d = sum(len(s["relaxations"]) for s in run_d["steps"])

    passes_bf = len(run_bf["passes"])
    updates_bf = sum(len(p["updates"]) for p in run_bf["passes"])

    return {
        "Dijkstra": {
            "path": path_d,
            "cost": cost_d,
            "time_ms": t_dijkstra,
            "memory_kb": m_dijkstra,
            "work_units": steps_d,
            "work_label": "Intersections settled",
            "relaxations": relaxations_d,
            "time_complexity": "O((V + E) log V)",
            "space_complexity": "O(V)",
            "supports_negative": "No (assumes greedy non-negative)",
            "detects_cycles": "No",
        },
        "Bellman-Ford": {
            "path": path_bf,
            "cost": cost_bf,
            "time_ms": t_bellman,
            "memory_kb": m_bellman,
            "work_units": passes_bf,
            "work_label": "Passes over all roads",
            "relaxations": updates_bf,
            "time_complexity": "O(V · E)",
            "space_complexity": "O(V)",
            "supports_negative": "Yes (can handle negative weights)",
            "detects_cycles": "Yes (reports negative cycles)",
        },
        "same_cost": cost_d == cost_bf,
        "same_path": path_d == path_bf,
        "faster": "Dijkstra" if t_dijkstra <= t_bellman else "Bellman-Ford",
        "speedup": max(t_dijkstra, t_bellman) / max(min(t_dijkstra, t_bellman), 1e-12),
    }

