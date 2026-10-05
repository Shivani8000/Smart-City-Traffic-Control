"""
graph_model.py
==============
The road-network data structure used by the whole project.

Vertices  = intersections (junctions)
Edges     = roads (undirected: a road can be driven both ways)
Weights   = travel cost of a road (distance or travel time, must be > 0)

The graph is stored as an ADJACENCY LIST, a dictionary of dictionaries:

    adj = {
        "City Center": {"Mall": 4, "Hospital": 6},
        "Mall":        {"City Center": 4},
        ...
    }

adj["City Center"]["Mall"] reads as: "the road from City Center to Mall costs 4".
Because roads are two-way, every road is stored twice (A->B and B->A).

All the algorithm modules work on this plain `adj` dictionary, so you can read
each algorithm without knowing anything about Streamlit.
"""
from __future__ import annotations

import math
import random

import pandas as pd

INF = float("inf")


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def road_key(u, v):
    """Order-independent name of a road: road_key('A','B') == road_key('B','A')."""
    return (u, v) if u <= v else (v, u)


def unique_edges(adj):
    """Return every road once as (u, v, weight). (adj stores each road twice.)"""
    seen, edges = set(), []
    for u in adj:
        for v, w in adj[u].items():
            key = road_key(u, v)
            if key not in seen:
                seen.add(key)
                edges.append((u, v, w))
    return edges


def _clean_number(value):
    """15.0 -> 15 (nicer to display), 2.5 stays 2.5."""
    value = float(value)
    return int(value) if value == int(value) else round(value, 2)


# --------------------------------------------------------------------------
# The road network
# --------------------------------------------------------------------------
class RoadNetwork:
    def __init__(self):
        self.adj = {}   # adjacency list: {node: {neighbour: weight}}
        self.pos = {}   # drawing coordinates: {node: (x, y)}  (only used for pictures)

    # ---- basic information ------------------------------------------------
    @property
    def nodes(self):
        return list(self.adj)

    @property
    def node_count(self):
        return len(self.adj)

    @property
    def edge_count(self):
        return len(unique_edges(self.adj))

    def edges(self):
        return unique_edges(self.adj)

    def has_edge(self, u, v):
        return u in self.adj and v in self.adj[u]

    def weight(self, u, v):
        return self.adj[u][v]

    def degree(self, node):
        return len(self.adj[node])

    # ---- building the graph ----------------------------------------------
    def add_intersection(self, name, pos=None):
        name = str(name).strip()
        if not name:
            raise ValueError("Intersection name cannot be empty.")
        if name in self.adj:
            raise ValueError(f"Intersection '{name}' already exists.")
        self.adj[name] = {}
        self.pos[name] = tuple(pos) if pos is not None else self._free_position()

    def _free_position(self):
        """Pick a drawing spot that is far away from the existing intersections."""
        if not self.pos:
            return (5.0, 5.0)
        rng = random.Random(len(self.pos) * 7919)
        best, best_gap = (5.0, 5.0), -1.0
        for _ in range(200):
            cand = (rng.uniform(0.6, 9.4), rng.uniform(0.6, 9.4))
            gap = min(math.dist(cand, p) for p in self.pos.values())
            if gap > best_gap:
                best, best_gap = cand, gap
        return best

    def add_road(self, u, v, weight):
        """Add a road (or update its cost if it already exists).
        Returns True if a NEW road was created, False if an old one was updated."""
        if u not in self.adj or v not in self.adj:
            raise ValueError("Both intersections must exist before adding a road.")
        if u == v:
            raise ValueError("A road must connect two different intersections.")
        weight = float(weight)
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("Travel cost must be a positive number.")
        weight = _clean_number(weight)
        is_new = v not in self.adj[u]
        self.adj[u][v] = weight
        self.adj[v][u] = weight
        return is_new

    def remove_road(self, u, v):
        if not self.has_edge(u, v):
            raise ValueError(f"There is no road between '{u}' and '{v}'.")
        del self.adj[u][v]
        del self.adj[v][u]

    def remove_intersection(self, name):
        if name not in self.adj:
            raise ValueError(f"Intersection '{name}' does not exist.")
        for neighbour in list(self.adj[name]):
            del self.adj[neighbour][name]
        del self.adj[name]
        self.pos.pop(name, None)

    # ---- copies (used for "what if" traffic simulation) -------------------
    def copy(self):
        clone = RoadNetwork()
        clone.adj = {u: dict(nb) for u, nb in self.adj.items()}
        clone.pos = dict(self.pos)
        return clone

    def with_weights(self, overrides):
        """Return a COPY where some roads have different costs.
        overrides = {('A','B'): 15, ...}. The original graph is never changed."""
        clone = self.copy()
        for (u, v), w in overrides.items():
            if clone.has_edge(u, v):
                clone.adj[u][v] = w
                clone.adj[v][u] = w
        return clone

    # ---- the two classic representations ----------------------------------
    def adjacency_list(self):
        """{'City Center': [('Mall', 4), ('Hospital', 6)], ...}"""
        return {u: list(nb.items()) for u, nb in self.adj.items()}

    def adjacency_matrix(self):
        """Square table; cell (row, column) = road cost, 0 = no direct road."""
        nodes = self.nodes
        data = [[self.adj[u].get(v, 0) for v in nodes] for u in nodes]
        return pd.DataFrame(data, index=nodes, columns=nodes)

    # ---- import / export --------------------------------------------------
    def edge_table(self):
        return pd.DataFrame(self.edges(), columns=["source", "target", "weight"])

    def to_csv(self):
        return self.edge_table().to_csv(index=False)

    @classmethod
    def from_edge_table(cls, table):
        """Build a network from a DataFrame with columns source, target, weight."""
        table = table.rename(columns=lambda c: str(c).strip().lower())
        missing = {"source", "target", "weight"} - set(table.columns)
        if missing:
            raise ValueError(f"CSV is missing column(s): {', '.join(sorted(missing))}. "
                             "Expected: source, target, weight")
        net = cls()
        for row_no, row in enumerate(table.itertuples(index=False), start=2):
            u, v, w = (str(row.source).strip(), str(row.target).strip(), row.weight)
            for name in (u, v):
                if name not in net.adj:
                    net.add_intersection(name, pos=(0, 0))
            try:
                net.add_road(u, v, w)
            except ValueError as err:
                raise ValueError(f"Row {row_no}: {err}") from None
        net.apply_spring_layout()
        return net

    def apply_spring_layout(self):
        """Automatic drawing positions (uses networkx' force-directed layout)."""
        import networkx as nx
        if not self.adj:
            return
        g = nx.Graph()
        g.add_nodes_from(self.adj)
        for u, v, w in self.edges():
            g.add_edge(u, v, weight=1.0 / w)   # bigger cost -> pulled less strongly -> drawn longer
        raw = nx.spring_layout(g, seed=7, weight="weight")
        xs = [p[0] for p in raw.values()]
        ys = [p[1] for p in raw.values()]
        span_x = (max(xs) - min(xs)) or 1.0
        span_y = (max(ys) - min(ys)) or 1.0
        for name, (x, y) in raw.items():
            self.pos[name] = (0.8 + 8.4 * (x - min(xs)) / span_x,
                              0.8 + 8.4 * (y - min(ys)) / span_y)


# --------------------------------------------------------------------------
# The sample city that is loaded when the app starts
# --------------------------------------------------------------------------
def build_sample_city():
    net = RoadNetwork()
    places = {
        "City Center":      (5.0, 5.0),
        "Airport":          (9.0, 8.6),
        "Railway Station":  (2.0, 7.2),
        "University":       (1.5, 2.6),
        "Hospital":         (7.6, 3.6),
        "Mall":             (6.6, 7.3),
        "Bus Terminal":     (4.2, 1.8),
        "Industrial Area":  (9.0, 1.2),
        "Residential Area": (0.6, 5.0),
    }
    for name, xy in places.items():
        net.add_intersection(name, pos=xy)

    roads = [
        ("City Center", "Mall", 4),
        ("City Center", "Hospital", 6),
        ("City Center", "Railway Station", 5),
        ("City Center", "Bus Terminal", 3),
        ("Mall", "Airport", 8),
        ("Mall", "Hospital", 5),
        ("Hospital", "Airport", 7),
        ("Hospital", "Industrial Area", 4),
        ("Railway Station", "University", 6),
        ("Railway Station", "Residential Area", 4),
        ("University", "Residential Area", 3),
        ("University", "Bus Terminal", 5),
        ("Bus Terminal", "Industrial Area", 9),
    ]
    for u, v, w in roads:
        net.add_road(u, v, w)
    return net
