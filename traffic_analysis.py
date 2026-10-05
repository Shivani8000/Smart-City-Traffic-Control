"""
traffic_analysis.py
===================
Congestion simulation.

Congestion = a road becomes slower, i.e. its weight goes UP (e.g. 5 -> 15).
We never edit the real network: we make a modified COPY, then compare routes
"before" and "after" with Bellman-Ford.

Why Bellman-Ford here?
  * Traffic changes the weights, and Bellman-Ford does not assume anything about
    them. It works even if some adjustment is negative (e.g. a toll refund or a
    priority-lane bonus on a ONE-WAY road) and it REPORTS a negative cycle
    instead of silently giving a wrong answer. Dijkstra cannot do either.
  * Its pass-by-pass structure ("after pass k, all routes of <= k roads are
    correct") is easy to display and explain.
  * The price is speed: O(V*E) instead of Dijkstra's O((V+E) log V). For a
    city-sized network that price is tiny.
"""
from route_planner import bellman_ford, build_path, path_cost
from graph_model import road_key


def congestion_level(ratio):
    """Ratio = current cost / normal cost."""
    if ratio >= 2.0:
        return "Heavy"
    if ratio >= 1.25:
        return "Moderate"
    return "Free flow"


def road_table(net, changes):
    """One row per congested road: normal cost, current cost, change, level."""
    rows = []
    for (u, v), new in changes.items():
        if not net.has_edge(u, v):
            continue
        old = net.weight(u, v)
        ratio = new / old
        rows.append({"road": f"{u} — {v}", "key": road_key(u, v), "normal": old,
                     "now": new, "change": new - old, "ratio": ratio,
                     "level": congestion_level(ratio)})
    return rows


def network_impact(net, congested):
    """Compare the cost of EVERY pair of intersections before/after congestion."""
    nodes = net.nodes
    old_total = new_total = pairs = affected = 0
    worst = None
    for i, s in enumerate(nodes):
        before = bellman_ford(net.adj, s, trace=False)["dist"]
        after = bellman_ford(congested.adj, s, trace=False)["dist"]
        for t in nodes[i + 1:]:
            if before[t] == float("inf"):
                continue
            pairs += 1
            old_total += before[t]
            new_total += after[t]
            increase = after[t] - before[t]
            if increase > 0:
                affected += 1
            if worst is None or increase > worst["increase"]:
                worst = {"from": s, "to": t, "before": before[t],
                         "after": after[t], "increase": increase}
    return {"pairs": pairs, "affected": affected,
            "avg_before": old_total / pairs if pairs else 0,
            "avg_after": new_total / pairs if pairs else 0,
            "worst": worst}


CONGESTION_PRESETS = {
    "Peak Evening Rush Hour": {
        "description": "Heavy peak hour traffic around City Center, Mall, and Airport corridors.",
        "changes": {
            ("City Center", "Mall"): 16.0,
            ("Mall", "Airport"): 18.0,
            ("City Center", "Hospital"): 12.0,
        },
    },
    "Arterial Incident / Severe Bottleneck": {
        "description": "Major accident severely blocking the City Center — Mall arterial connection.",
        "changes": {
            ("City Center", "Mall"): 22.0,
        },
    },
    "Transit Hub Congestion": {
        "description": "Heavy passenger congestion around Railway Station and Bus Terminal.",
        "changes": {
            ("City Center", "Railway Station"): 12.0,
            ("Railway Station", "University"): 13.0,
            ("City Center", "Bus Terminal"): 8.0,
        },
    },
    "Industrial Freight Surge": {
        "description": "Commercial trucks slowing down Industrial Area and Hospital connector roads.",
        "changes": {
            ("Hospital", "Industrial Area"): 13.0,
            ("Bus Terminal", "Industrial Area"): 20.0,
        },
    },
}


def analyze_congestion(net, changes, source, target):
    if source not in net.adj or target not in net.adj:
        raise ValueError(f"Both source '{source}' and target '{target}' must exist in the network.")

    congested = net.with_weights(changes)
    run_before = bellman_ford(net.adj, source)
    run_after = bellman_ford(congested.adj, source)

    path_before = build_path(run_before["prev"], source, target)
    path_after = build_path(run_after["prev"], source, target)
    if not path_before or not path_after:
        return {
            "reachable": False,
            "congested": congested,
            "path_before": path_before,
            "path_after": path_after,
            "cost_before": run_before["dist"].get(target) if path_before else None,
            "cost_after": run_after["dist"].get(target) if path_after else None,
            "extra_cost": 0,
            "extra_pct": 0,
            "stay_cost": 0,
            "detour_saving": 0,
            "route_changed": False,
            "roads_hit": [],
            "run_before": run_before,
            "run_after": run_after,
            "table": road_table(net, changes),
            "impact": network_impact(net, congested),
        }

    cost_before = run_before["dist"][target]
    cost_after = run_after["dist"][target]
    stay_cost = path_cost(congested.adj, path_before)   # if we ignored the jam
    hit_roads = [road_key(a, b) for a, b in zip(path_before, path_before[1:])
                 if road_key(a, b) in changes]

    return {
        "reachable": True,
        "congested": congested,
        "path_before": path_before, "cost_before": cost_before,
        "path_after": path_after, "cost_after": cost_after,
        "extra_cost": cost_after - cost_before,
        "extra_pct": (cost_after - cost_before) / cost_before * 100 if cost_before else 0,
        "stay_cost": stay_cost,
        "detour_saving": stay_cost - cost_after,
        "route_changed": path_before != path_after,
        "roads_hit": hit_roads,
        "run_before": run_before, "run_after": run_after,
        "table": road_table(net, changes),
        "impact": network_impact(net, congested),
    }
