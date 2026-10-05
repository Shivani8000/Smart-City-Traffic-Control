# Smart City Traffic Management and Route Optimization System

Design and Analysis of Algorithms Lab capstone - BCA (AI & DS), Semester V.

A Streamlit dashboard that models a city's road network as a graph and uses six classic algorithms
(Dijkstra, Bellman-Ford, BFS, DFS, Prim, Kruskal) - all **written by hand**, not taken from a library - to plan routes,
simulate congestion, analyse connectivity and plan infrastructure.

| Graph idea | In the city |
|---|---|
| Vertex | Intersection / junction |
| Edge | Road (two-way) |
| Edge weight | Travel cost (time or distance, always > 0) |

---

## 1. Run it

```bash
# 1. (recommended) create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# 2. install the packages
pip install -r requirements.txt

# 3. start the dashboard
streamlit run app.py
```

The browser opens automatically. A sample city (9 named places, 13 roads) is loaded, so every page works immediately.

Other commands:

```bash
python tests/test_algorithms.py     # checks all algorithms against networkx
jupyter notebook project_notebook.ipynb
```

---

## 2. Project structure

```
smart-city-traffic-system/
├── app.py                    Streamlit pages (what you see)
├── route_planner.py          Dijkstra + Bellman-Ford
├── traffic_analysis.py       congestion simulation (Bellman-Ford)
├── connectivity_module.py    BFS + DFS
├── mst_planner.py            Prim + Kruskal (+ Union-Find)
├── graph_model.py            helper: the road network, adjacency list/matrix, sample city
├── benchmark.py              helper: real timing/memory experiments
├── visuals.py                helper: draws the network (matplotlib)
├── ui.py                     helper: CSS, cards, route chips
├── tests/test_algorithms.py  automatic correctness checks
├── project_notebook.ipynb    step-by-step notebook with executed outputs
├── requirements.txt  README.md  .gitignore  .streamlit/config.toml
├── screenshots/              put your UI screenshots here (see its README)
└── report/                   benchmark_results.csv, viva notes, report outline
```

The five helper files beyond your suggested structure exist for one reason: keeping the algorithm files clean.
Each algorithm module has **no Streamlit code** in it, so you can read and explain it on its own.

---

## 3. The dashboard

| Page | What you can do |
|---|---|
| **Dashboard** | Cards for intersections, roads, connectivity, congestion; current route and cost; live map; network insights |
| **Route Planner** | Pick source/destination and algorithm (Dijkstra or Bellman-Ford); route chips, cost, highlighted map, table of distance updates, optional step-by-step calculation |
| **Traffic Analysis** | Congest roads (set a new cost or multiply it); original vs updated route and cost, before/after maps, impact statistics, "Why Bellman-Ford?" |
| **Connectivity** | Choose a start; BFS and DFS orders drawn on the map with visit numbers; reachable/unreachable intersections; queue and stack traces |
| **Infrastructure Planning** | Prim and Kruskal MSTs, selected roads, total construction cost, original vs MST maps, accept/reject decisions |
| **Algorithm Comparison** | Real experiments on 10/25/50/100 intersections: BFS vs DFS, Dijkstra vs Bellman-Ford, Prim vs Kruskal; charts; negative-cost demo |
| **Network Builder** | Add intersections and roads, edit or delete them, import/export CSV |
| **Graph Data** | Adjacency list and adjacency matrix, updated automatically |

Design idea: a transit-authority operations console. Signal colours (green/amber/red) are used *only* for traffic status,
and each card's coloured left edge tells you its status at a glance.

---

## 4. How the code works (read in this order)

**`graph_model.py`** - the graph is a dictionary of dictionaries: `adj["City Center"]["Mall"] == 4`.
Each road is stored in both directions. The adjacency matrix is *built from* this dictionary, so both views always agree.

**`route_planner.py`** - both algorithms revolve around *relaxation*:

```python
if dist[u] + cost < dist[v]:      # cheaper way to reach v through u?
    dist[v] = dist[u] + cost
    prev[v] = u                   # remember where we came from
```

* *Dijkstra*: repeatedly take the unfinished intersection with the smallest distance (a heap gives it to us), lock it, relax its roads.
* *Bellman-Ford*: relax **every** road, V-1 times; a last extra pass detects negative cycles.
* `build_path()` follows the `prev` pointers backwards to rebuild the route.

**`traffic_analysis.py`** - congestion = a road's weight goes up. We build a *modified copy* of the network
(`with_weights`), run Bellman-Ford on both, and compare routes and costs.
It also reports what the trip would cost if you ignored the jam and stayed on the old route.

**`connectivity_module.py`** - BFS uses a queue (`deque`), DFS an explicit stack.
Neighbours are visited alphabetically so results are repeatable.

**`mst_planner.py`** - Prim keeps a heap of roads leaving the growing tree. Kruskal sorts all roads and uses
**Union-Find** to reject roads that would form a loop.

**`benchmark.py`** - builds random connected networks with a fixed seed, times each algorithm by repeating it for
≥ 0.03 s and averaging (`time.perf_counter`), measures peak memory with `tracemalloc`.
The teaching "trace" recording is switched off so only the algorithm is timed.

### Complexity summary

| Algorithm | Time | Notes |
|---|---|---|
| BFS / DFS | O(V + E) | queue / stack |
| Dijkstra | O((V + E) log V) | heap; non-negative costs only |
| Bellman-Ford | O(V · E) | any costs; detects negative cycles |
| Prim | O(E log V) | heap |
| Kruskal | O(E log E) | sorting + Union-Find |

---

## 5. Honest notes (good to know for your viva)

* **Experiment numbers are measured, never typed in.** They change from computer to computer; the *pattern* matters.
  The comparison page also checks that Dijkstra = Bellman-Ford and Prim = Kruskal on every experiment.
* **Bellman-Ford and traffic.** With ordinary positive travel times, Dijkstra gives the same answer faster. Bellman-Ford is
  used in the traffic module because it makes no assumption about the weights (negative adjustments, negative-cycle detection)
  and its pass-by-pass structure is easy to display. The *Negative-cost demo* in Algorithm Comparison shows a case where
  Dijkstra gives a wrong answer.
* **Roads are two-way** (undirected graph). Negative costs only make sense for one-way roads, so the demo uses a small directed example.
* **networkx is used only for** the automatic layout of imported networks and for cross-checking the algorithms in the tests -
  never to compute a route, traversal or MST inside the app.
* **The map is drawn with matplotlib** (as suggested by the assignment). It is a clear static picture; the interactive parts are the
  selectors, sliders, tables and charts. If you want zoom/hover on the map itself, Plotly is the natural upgrade.
* **Screenshots:** the `screenshots/` folder is empty on purpose - capture your own from the running app (see the table in its README).

---

## 6. Ideas for extension

Directed (one-way) roads, A* search, loading real map data (OpenStreetMap), time-of-day congestion profiles, saving scenarios.
