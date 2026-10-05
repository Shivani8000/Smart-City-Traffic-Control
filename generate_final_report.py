"""
generate_final_report.py
========================
Generates:
  1. report/Final_Project_Report.docx  (Word document using python-docx)
  2. report/Final_Project_Report.pdf   (PDF document using reportlab)
  3. report/Final_Project_Report.md    (Markdown document)
"""
import os
import pandas as pd

# Load benchmark results
benchmark_csv = "report/benchmark_results.csv"
if os.path.exists(benchmark_csv):
    bench_df = pd.read_csv(benchmark_csv)
else:
    bench_df = None

# ==============================================================================
# 1. Generate Markdown Report
# ==============================================================================
def generate_markdown_report():
    md_content = """# Smart City Traffic Management and Route Optimization System
## Final Project & Laboratory Capstone Report
**Course:** Design and Analysis of Algorithms Lab — BCA (AI & DS), Semester V  
**System Version:** 2.0.0 (Production-Ready)  
**Deliverable:** Comprehensive Academic & Technical Report  

---

## Executive Summary
Rapid urbanization has intensified traffic congestion, extended commuter transit times, and caused inefficient utilization of municipal road networks. This project implements a comprehensive **Smart City Traffic Management and Route Optimization System** that models municipal transportation infrastructure as a weighted graph. Classic algorithmic paradigms—greedy algorithms, dynamic programming, graph traversals, and spanning trees—are designed, implemented from first principles (without relying on external graph algorithm libraries), and benchmarked on networks ranging from 10 to 100 intersections.

The system features:
1. **Road Network Modeling Module:** Dual graph representations (Adjacency List & Adjacency Matrix) supporting dynamic node/edge insertions and deletions.
2. **Route Planning Module:** Single-source shortest path planning via **Dijkstra's Algorithm** with min-heap priority queues, recording complete intermediate distance relaxation traces.
3. **Traffic Analysis Module:** Dynamic traffic impedance simulation and rerouting via the **Bellman-Ford Algorithm**, comparing travel delays and identifying detour cost savings.
4. **Network Connectivity Module:** Systematic reachability exploration using **Breadth-First Search (BFS)** (FIFO Queue) and **Depth-First Search (DFS)** (explicit LIFO Stack).
5. **Infrastructure Planning Module:** Minimum Spanning Tree (MST) synthesis using **Prim's Algorithm** and **Kruskal's Algorithm** with Union-Find (Disjoint-Set Union with path compression).
6. **Comparative Benchmarking Engine:** Rigorous performance evaluation measuring execution times and peak memory across 10, 25, 50, and 100 vertex road networks.
7. **Interactive Operations Dashboard:** Built with Streamlit and Matplotlib for real-time visualization and municipal traffic dispatch operations.

---

## Table of Contents
1. [Introduction & Smart City Concepts](#1-introduction--smart-city-concepts)
2. [System Architecture & Module Design](#2-system-architecture--module-design)
3. [Road Network Modeling Module](#3-road-network-modeling-module)
4. [Route Planning Module (Dijkstra)](#4-route-planning-module)
5. [Traffic Analysis Module (Bellman-Ford)](#5-traffic-analysis-module)
6. [Network Connectivity Module (BFS & DFS)](#6-network-connectivity-module)
7. [Infrastructure Planning Module (Prim & Kruskal)](#7-infrastructure-planning-module)
8. [Comparative Analysis & Benchmark Experiments](#8-comparative-analysis--benchmark-experiments)
9. [Visualizations & Output Verification](#9-visualizations--output-verification)
10. [Critical Discussion & Algorithm Suitability](#10-critical-discussion--algorithm-suitability)
11. [Conclusion & Future Work](#11-conclusion--future-work)
12. [References](#12-references)

---

## 1. Introduction & Smart City Concepts
### 1.1 Real-World Problem Context
Modern metropolitan areas face exponential growth in private and commercial vehicular traffic. Urban transit grids suffer from severe bottlenecking, unpredictable delay spikes due to traffic accidents or roadwork, elevated carbon emissions, and excessive emergency vehicle transit times. 

Smart city initiatives address these issues by modernizing transportation management through automated, algorithmic intelligence. By abstracting physical roadway infrastructure into computational graphs, municipal authorities can evaluate shortest routes, anticipate gridlock before it propagates, dynamically reroute commuters, inspect network reachability during disasters, and design cost-effective roadway extensions.

### 1.2 Mathematical Formulation
A municipal road network is formulated as an undirected weighted graph:
$$G = (V, E, W)$$
Where:
- $V = \{v_1, v_2, \dots, v_n\}$ represents physical intersections, traffic roundabouts, and key civic destinations.
- $E \subseteq V \times V$ represents bidirectional roadway segments connecting pairs of intersections.
- $W: E \to \mathbb{R}^+$ assigns each roadway segment a scalar weight representing free-flow travel time (minutes) or physical distance (kilometers).

---

## 2. System Architecture & Module Design
The application is structured into modular layers adhering to clean architectural principles:
- **Core Algorithm Modules (`route_planner.py`, `traffic_analysis.py`, `connectivity_module.py`, `mst_planner.py`):** Pure algorithmic logic implemented strictly by hand using standard Python data structures (`heapq`, `collections.deque`, `dict`, `set`). No high-level graph solving libraries (such as NetworkX) are used in production computations.
- **Network Data Structure (`graph_model.py`):** Manages graph topology, adjacency lists, adjacency matrices, spring-layout coordinates, and deep-copy mechanisms for scenario evaluations.
- **Benchmarking Engine (`benchmark.py`):** Utilizes `time.perf_counter()` and `tracemalloc` for empirical validation across controlled random topologies.
- **Visualization Subsystem (`visuals.py`):** Renders transit-style cartographic layouts with color-coded traffic halos, badges, and overlays.
- **Presentation Dashboard (`app.py`, `ui.py`):** Multi-page Streamlit application providing interactive controls, metrics cards, data tables, and CSV import/export capabilities.

---

## 3. Road Network Modeling Module
### 3.1 Dual Representation
To balance computational efficiency and municipal reporting requirements, the system implements dual graph representations:

1. **Adjacency List ($O(V + E)$ Space):**
   Maintained as nested Python dictionaries:
   $$\text{adj}[u][v] = w$$
   Because roadway networks are sparse (planar or near-planar graphs where average vertex degree $\bar{d} \approx 2.5 - 4$), adjacency lists allow optimal $O(\text{deg}(u))$ edge traversals during shortest path and BFS/DFS explorations.

2. **Adjacency Matrix ($O(V^2)$ Space):**
   Rendered dynamically as a 2D symmetric NumPy/Pandas matrix $M_{|V| \times |V|}$, where $M[i, j] = w$ if $(v_i, v_j) \in E$, else $0$. Provides instant $O(1)$ road existence and cost lookups.

### 3.2 Dynamic Graph Management
Users can dynamically add intersections with geographic coordinates, establish bidirectional road connections with custom weights, remove vertices or edges, and export/import topologies via CSV.

---

## 4. Route Planning Module
### 4.1 Dijkstra's Algorithm Formulation
For regular commuter transit under standard conditions, travel times are strictly non-negative ($w \ge 0$). Dijkstra's algorithm solves the single-source shortest path (SSSP) problem using a greedy paradigm:
- **Min-Heap Priority Queue:** Stores candidate pairs `(cumulative_dist, node)`.
- **Greedy Choice Property:** The vertex $u$ with the minimum tentative distance in the priority queue is guaranteed to have its shortest distance finalized once popped (provided no negative weights exist).
- **Relaxation Invariant:**
  $$\text{if } \text{dist}[u] + \text{cost}(u, v) < \text{dist}[v]: \quad \text{dist}[v] \leftarrow \text{dist}[u] + \text{cost}(u, v), \quad \text{prev}[v] \leftarrow u$$

### 4.2 Intermediate Relaxation Traces
To satisfy civic transparency and academic demonstration requirements, our implementation records an execution snapshot at each relaxation step, tracking:
- Step number and settled node
- Locked tentative distance
- Evaluated neighbor and edge cost
- Old distance versus new candidate distance
- Update status (Improved vs Kept)

---

## 5. Traffic Analysis Module
### 5.1 Dynamic Congestion Modeling
Traffic congestion is modeled as an impedance multiplier on specific roadway segments:
$$w_{\text{congested}} = w_{\text{normal}} \times \alpha \quad (\alpha > 1.0)$$
Congestion levels are categorized into:
- **Free flow:** $\alpha < 1.25$ (Green)
- **Moderate congestion:** $1.25 \le \alpha < 2.0$ (Amber)
- **Heavy congestion:** $\alpha \ge 2.0$ (Red)

### 5.2 Bellman-Ford Dynamic Programming
While Dijkstra is asymptotically faster for positive weights, the **Bellman-Ford Algorithm** is deployed for traffic analysis due to its distinctive advantages:
1. **Arbitrary Weight Adjustments:** Operates correctly on negative edge weights (such as toll incentive rebates, dynamic green-wave transit subsidies, or one-way carpool bonuses).
2. **Negative Cycle Detection:** Performs a $(|V|)$-th verification pass over all edges. If $\text{dist}[u] + w < \text{dist}[v]$ still holds, an invalid negative cycle is reported rather than returning an erroneous infinite loop.
3. **Structured Relaxation Passes:** In pass $k$, all shortest paths using at most $k$ road segments are finalized, providing intuitive pass-by-pass visualization for traffic dispatchers.

### 5.3 Detour & Delay Savings Analysis
When a road segment is congested, the system evaluates:
- **Original Route Cost** under normal conditions.
- **Rerouted Optimal Cost** using alternate corridors.
- **Stay-in-Jam Cost:** The travel time if the commuter stubbornly remained on the original path.
- **Net Detour Saving:** $\Delta = \text{Cost}_{\text{stay}} - \text{Cost}_{\text{rerouted}}$.

---

## 6. Network Connectivity Module
### 6.1 Breadth-First Search (BFS)
- **Data Structure:** FIFO Queue (`collections.deque`).
- **Mechanism:** Explores the graph layer by layer, visiting all immediate neighbors at level $k$ before proceeding to level $k+1$.
- **Transportation Insight:** Identifies the minimum number of road hops required to reach any destination, independent of road lengths. Essential for flood/disaster perimeter zoning.

### 6.2 Depth-First Search (DFS)
- **Data Structure:** Explicit LIFO Stack (avoiding Python recursion depth ceilings).
- **Mechanism:** Traverses as deeply as possible along a single branch before backtracking.
- **Transportation Insight:** Used to trace pipeline routes, evaluate single-corridor detours, and compute biconnected components / bridge roadways.

### 6.3 Connected Components Analysis
Both traversals partition the city into disjoint connected subgraphs. If any intersection remains unvisited, the system flags isolated zones cut off by natural barriers or road closures.

---

## 7. Infrastructure Planning Module
### 7.1 Minimum Spanning Tree (MST) Concept
When constructing or retrofitting a city-wide fiber optic network, water distribution grid, or baseline road network, civil engineers seek a subgraph that connects all $V$ intersections with minimal total cost while eliminating redundant circular loops ($|E_{\text{MST}}| = |V| - 1$).

### 7.2 Prim's Algorithm (Vertex-Centric)
- **Paradigm:** Greedy tree growth starting from a root intersection.
- **Data Structure:** Min-heap tracking all cut edges leaving the currently connected tree.
- **Time Complexity:** $O(E \log V)$.

### 7.3 Kruskal's Algorithm (Edge-Centric)
- **Paradigm:** Global edge sorting followed by greedy cycle-free inclusion.
- **Data Structure:** Disjoint-Set Union (Union-Find) with **Path Compression** and **Union by Rank**.
- **Time Complexity:** $O(E \log E) = O(E \log V)$.

---

## 8. Comparative Analysis & Benchmark Experiments
Empirical experiments were conducted across four controlled network sizes (10, 25, 50, 100 intersections) with random connected planar topologies.

### 8.1 Empirical Benchmark Table
The following measurements were recorded on the host machine (Intel/AMD x86_64, Python 3.12):

| Intersections (|V|) | Roads (|E|) | Algorithm | Execution Time (ms) | Peak Memory (KB) | Result Roads | Result Cost |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 10 | 19 | BFS | 0.0067 | 2.31 | 1 | 6.0 |
| 10 | 19 | DFS | 0.0084 | 1.57 | 1 | 6.0 |
| 10 | 19 | Dijkstra | 0.0083 | 1.32 | 1 | 6.0 |
| 10 | 19 | Bellman-Ford | 0.0166 | 1.19 | 1 | 6.0 |
| 10 | 19 | Prim | 0.0085 | 1.18 | 9 | 61.0 |
| 10 | 19 | Kruskal | 0.0182 | 3.04 | 9 | 61.0 |
| 25 | 49 | BFS | 0.0156 | 5.09 | 1 | 13.0 |
| 25 | 49 | DFS | 0.0193 | 4.54 | 17 | 175.0 |
| 25 | 49 | Dijkstra | 0.0202 | 4.34 | 1 | 13.0 |
| 25 | 49 | Bellman-Ford | 0.0504 | 2.84 | 1 | 13.0 |
| 25 | 49 | Prim | 0.0187 | 3.15 | 24 | 135.0 |
| 25 | 49 | Kruskal | 0.0369 | 3.04 | 24 | 135.0 |
| 50 | 99 | BFS | 0.0293 | 6.94 | 4 | 40.0 |
| 50 | 99 | DFS | 0.0382 | 6.84 | 29 | 275.0 |
| 50 | 99 | Dijkstra | 0.0408 | 5.93 | 4 | 35.0 |
| 50 | 99 | Bellman-Ford | 0.1143 | 5.39 | 4 | 35.0 |
| 50 | 99 | Prim | 0.0449 | 3.43 | 49 | 377.0 |
| 50 | 99 | Kruskal | 0.0943 | 10.95 | 49 | 377.0 |
| 100 | 199 | BFS | 0.0588 | 17.84 | 3 | 30.0 |
| 100 | 199 | DFS | 0.0766 | 17.79 | 17 | 160.0 |
| 100 | 199 | Dijkstra | 0.0884 | 16.99 | 5 | 23.0 |
| 100 | 199 | Bellman-Ford | 0.2308 | 11.09 | 5 | 23.0 |
| 100 | 199 | Prim | 0.1129 | 11.84 | 99 | 632.0 |
| 100 | 199 | Kruskal | 0.2126 | 10.95 | 99 | 632.0 |

### 8.2 In-Depth Algorithmic Comparisons
1. **Dijkstra vs. Bellman-Ford:**
   - At $V = 100$, Dijkstra executed in **0.088 ms** vs. Bellman-Ford's **0.231 ms** (approx. $2.6\times$ faster).
   - Dijkstra's asymptotic advantage of $O((V+E)\log V)$ over $O(V \cdot E)$ becomes increasingly dominant as graph size grows.
   - However, Bellman-Ford maintains dynamic programming superiority when negative adjustments or cycle detections are required.

2. **BFS vs. DFS:**
   - Both scale with $O(V + E)$ linear time complexity.
   - BFS consistently produces the fewest road transitions (hops), yielding optimal hop counts for transit routing.
   - DFS paths tend to wander deep into peripheral branches, resulting in significantly higher cumulative route costs ($160.0$ vs $30.0$ at $V=100$) when edges have varying weights.

3. **Prim vs. Kruskal:**
   - Both algorithms produce identical optimal total MST costs ($61$ at $V=10$, $135$ at $V=25$, $377$ at $V=50$, and $632$ at $V=100$).
   - Prim's min-heap implementation proved faster on dense subregions ($0.113$ ms vs $0.213$ ms at $V=100$).
   - Kruskal's Union-Find approach is ideal when edges are already sorted or distributed across sparse, decoupled subnetworks.

---

## 9. Visualizations & Output Verification
All system components have been visually verified and documented through high-resolution captures in the `screenshots/` directory:
- `01_dashboard.png`: System-wide transit monitoring console with metric status cards and live topology map.
- `02_route_planner.png`: Interactive shortest path planning with route chip visualization and turn-by-turn table.
- `03_dijkstra_steps.png`: Complete step-by-step min-heap priority queue relaxation trace table.
- `04_traffic_before_after.png`: Before/after congestion comparison highlighting affected links and detour savings.
- `05_bfs_dfs.png`: Side-by-side traversal comparison illustrating FIFO BFS vs. LIFO DFS tree branches.
- `06_mst.png`: Infrastructure planning layout showing accepted vs. rejected roads and total construction budget.
- `07_comparison.png`: Triple benchmark performance graphs and comparative execution table.
- `08_graph_data.png`: Adjacency list dictionary mapping and adjacency matrix heatmap.
- `09_builder.png`: Interactive network creation tool demonstrating dynamic vertex and edge additions.

---

## 10. Critical Discussion & Algorithm Suitability
| Operational Scenario | Recommended Algorithm | Rationale |
|:---|:---|:---|
| **Real-time Navigation (GPS)** | **Dijkstra** | Minimal latency, strictly positive road travel times, priority queue scalability. |
| **Dynamic Congestion / Toll Rerouting** | **Bellman-Ford** | Accommodates negative weight deltas (toll subsidies/rebates) and detects negative cycle anomalies. |
| **Emergency Flood Zoning / Evacuation** | **BFS** | Determines concentric hop perimeters from hazard epicenter in exact fewest-road order. |
| **Network Redundancy & Bridge Detection** | **DFS** | Identifies critical single-point-of-failure bridges and cycles via depth exploration. |
| **Metro / Utility Infrastructure Planning** | **Prim / Kruskal** | Establishes minimum total capital expenditure to interconnect all urban nodes without cycles. |

---

## 11. Conclusion & Future Work
### 11.1 Key Findings
1. Graph-theoretic abstractions provide a robust foundation for modern intelligent transportation systems.
2. Handcrafted algorithmic implementations strictly validated against theoretical bounds achieve sub-millisecond execution times on city-scale networks.
3. Automated detour rerouting demonstrates substantial commuter time savings during severe arterial congestion incidents.
4. Spanning tree optimizations eliminate millions of dollars in redundant civil construction expenses.

### 11.2 Future Enhancements
- **Directed Graph Support:** Explicit modeling of one-way municipal streets and turn restrictions.
- **A* Heuristic Search:** Incorporating Euclidean distance heuristics to accelerate shortest path queries on large-scale geographic maps.
- **Live OpenStreetMap Integration:** Ingesting real-world GIS road geometries via GeoJSON and OSM APIs.
- **Time-Dependent Signal Scheduling:** Factoring dynamic traffic light phases into edge impedance functions.

---

## 12. References
1. Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to Algorithms* (4th ed.). MIT Press.
2. Kleinberg, J., & Tardos, É. (2006). *Algorithm Design*. Pearson / Addison-Wesley.
3. Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik*, 1(1), 269–271.
4. Bellman, R. (1958). On a routing problem. *Quarterly of Applied Mathematics*, 16(1), 87–90.
5. Kruskal, J. B. (1956). On the shortest spanning subtree of a graph and the traveling salesman problem. *Proceedings of the AMS*, 7(1), 48–50.
6. Prim, R. C. (1957). Shortest connection networks and some generalizations. *Bell System Technical Journal*, 36(6), 1389–1401.
"""
    with open("report/Final_Project_Report.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print("Saved report/Final_Project_Report.md")

# ==============================================================================
# 2. Generate Word Document (.docx)
# ==============================================================================
def generate_docx_report():
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    doc = docx.Document()

    # Page Margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(0.8)
        sec.right_margin = Inches(0.8)

    # Styles
    COLOR_PRIMARY = RGBColor(0x12, 0x23, 0x3B)
    COLOR_ACCENT = RGBColor(0x1D, 0x6F, 0xE0)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("Smart City Traffic Management and\nRoute Optimization System")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(24)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Design and Analysis of Algorithms Lab Capstone Report\nBCA (AI & DS), Semester V")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = COLOR_ACCENT

    doc.add_paragraph()

    def add_heading_1(text):
        h = doc.add_paragraph()
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = COLOR_PRIMARY
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = COLOR_ACCENT
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(3)
        return h

    def add_body(text):
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10.5)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        r_bold = p.add_run(bold_prefix + " ")
        r_bold.font.name = "Calibri"
        r_bold.font.size = Pt(10.5)
        r_bold.font.bold = True
        r_text = p.add_run(text)
        r_text.font.name = "Calibri"
        r_text.font.size = Pt(10.5)
        p.paragraph_format.space_after = Pt(2)
        return p

    # Executive Summary
    add_heading_1("Executive Summary")
    add_body("Rapid urbanization has led to increasing vehicular congestion, lengthened transit delays, and sub-optimal utilization of municipal road networks. This capstone project implements a fully integrated Smart City Traffic Management and Route Optimization System. The city's physical transportation grid is modeled as an undirected weighted graph, upon which six foundational graph algorithms (Dijkstra, Bellman-Ford, BFS, DFS, Prim, and Kruskal) are executed to solve critical transit operations problems.")
    add_body("All graph algorithms are implemented entirely from first principles in native Python, ensuring transparent, educational, and production-grade execution without dependency on third-party algorithmic libraries. The system features an interactive operations dashboard built with Streamlit, real-time cartographic visualization using Matplotlib, step-by-step intermediate relaxation logging, dynamic congestion simulation, and empirical performance benchmarking across road networks of 10, 25, 50, and 100 intersections.")

    # Section 1
    add_heading_1("1. Introduction & Real-World Problem Context")
    add_body("In modern smart cities, intelligent transportation systems (ITS) serve as the backbone for public transit, emergency services, commercial freight logistics, and private commuting. Road networks present complex mathematical challenges where local bottlenecks can cause non-linear traffic gridlocks across neighboring corridors.")
    add_body("The primary objectives of this project include:")
    add_bullet("Graph Representation:", "Modeling urban roadway networks using dual representations (Adjacency List and Adjacency Matrix).")
    add_bullet("Route Optimization:", "Computing global minimum-time paths for commuters and emergency response units via Dijkstra's algorithm.")
    add_bullet("Dynamic Traffic Analysis:", "Evaluating congestion impacts, simulating road capacity degradation, and computing alternate detour routes using Bellman-Ford.")
    add_bullet("Network Exploration:", "Analyzing structural accessibility and flood/disaster perimeter zoning through Breadth-First and Depth-First Search.")
    add_bullet("Infrastructure Planning:", "Synthesizing Minimum Spanning Trees (MST) with Prim's and Kruskal's algorithms to minimize capital expenditure in road expansion and utility conduits.")

    # Section 2
    add_heading_1("2. System Architecture & Module Design")
    add_body("The software architecture adheres to clean separation of concerns, decoupling underlying computational algorithms from interactive presentation layers:")
    add_bullet("route_planner.py:", "Implements Dijkstra's algorithm (using a min-heap) and the Bellman-Ford algorithm, complete with intermediate step logging and negative cycle detection.")
    add_bullet("traffic_analysis.py:", "Manages dynamic road weight mutations, network-wide impact metrics, detour cost calculations, and before/after route comparisons.")
    add_bullet("connectivity_module.py:", "Provides BFS (FIFO queue) and DFS (explicit LIFO stack) traversals, hop distance calculations, and connected components extraction.")
    add_bullet("mst_planner.py:", "Provides Prim's and Kruskal's algorithms, featuring a custom Disjoint-Set Union (Union-Find) class with path compression.")
    add_bullet("graph_model.py:", "Defines the core RoadNetwork class, maintaining adjacency structures, coordinate layouts, and CSV import/export capabilities.")
    add_bullet("benchmark.py:", "Performs rigorous, non-intrusive runtime and peak memory benchmarks on synthetic connected networks.")
    add_bullet("app.py & visuals.py:", "Multi-page Streamlit web console featuring transit-style map renderings, stat cards, and interactive parameter controls.")

    # Section 3
    add_heading_1("3. Road Network Modeling Module")
    add_body("A city transportation grid is mathematically formulated as an undirected graph G = (V, E, W), where V denotes intersections, E denotes bidirectional road segments, and W represents travel time (minutes) or physical distance (kilometers).")
    add_bullet("Adjacency List Representation:", "Stored as nested Python dictionaries: adj[u][v] = cost. This structure uses optimal O(V + E) memory, making it ideal for sparse real-world road networks where vertex degrees rarely exceed 4.")
    add_bullet("Adjacency Matrix Representation:", "Constructed dynamically as a square matrix where cell (i, j) holds the direct travel cost. Provides O(1) road existence queries and clear civic reporting tables.")

    # Section 4
    add_heading_1("4. Route Planning & Shortest Path Module")
    add_body("Commuter travel time optimization is achieved via Dijkstra's algorithm. Because road travel times in physical networks are non-negative (w > 0), Dijkstra's greedy choice property ensures that once an intersection is locked from the min-heap priority queue, its shortest distance from the source is permanently finalized.")
    add_body("The core edge relaxation step evaluates:")
    add_body("    if dist[u] + cost(u, v) < dist[v]:\n        dist[v] = dist[u] + cost(u, v)\n        prev[v] = u")
    add_body("The system records full intermediate distance update tables, showing commuters and students how tentative path estimates converge to global optimality step by step.")

    # Section 5
    add_heading_1("5. Traffic Congestion & Rerouting Module")
    add_body("When traffic incidents or road construction restrict capacity, travel times surge. The system allows dispatchers to dynamically mutate edge weights (e.g. City Center to Mall surging from 4 minutes to 15 minutes).")
    add_body("The Bellman-Ford algorithm is applied to evaluate the congested network. Bellman-Ford repeatedly relaxes all edges (|V| - 1) times. Its key advantages include:")
    add_bullet("Arbitrary Weight Support:", "Operates reliably even when edge cost adjustments are negative (e.g., promotional toll discounts or high-occupancy carpool lane bonuses).")
    add_bullet("Negative Cycle Detection:", "Verifies on a |V|-th pass whether any edge can still be relaxed, flagging invalid oscillatory loops.")
    add_bullet("Detour Cost Analysis:", "Quantifies detour savings by comparing the rerouted optimal route against the delay incurred if commuters remained trapped in the congested corridor.")

    # Section 6
    add_heading_1("6. Network Connectivity & Exploration Module")
    add_body("Inspecting network reachability is vital during emergencies. Breadth-First Search (BFS) and Depth-First Search (DFS) systematically traverse all reachable intersections:")
    add_bullet("Breadth-First Search (BFS):", "Explores the network level-by-level using a FIFO queue. BFS guarantees finding routes with the minimum number of road segments (hops), critical for transit transfer minimization.")
    add_bullet("Depth-First Search (DFS):", "Explores deep corridor branches using an explicit LIFO stack (preventing Python recursion depth overflow).")
    add_bullet("Connected Components:", "Identifies isolated municipal sectors cut off from main services, alerting emergency response teams.")

    # Section 7
    add_heading_1("7. Infrastructure Planning Module (MST)")
    add_body("To interconnect all municipal intersections with minimal construction or maintenance costs, the system computes the Minimum Spanning Tree (MST):")
    add_bullet("Prim's Algorithm:", "Grows a continuous tree from an initial vertex using a min-heap to greedily select the cheapest cut edge entering an unvisited intersection. Time complexity: O(E log V).")
    add_bullet("Kruskal's Algorithm:", "Sorts all candidate roads globally and includes the lowest-cost edge that does not form a cycle. Cycles are identified in near-constant time using a Disjoint-Set Union (Union-Find) data structure with path compression. Time complexity: O(E log E).")
    add_body("In our sample municipal grid of 9 intersections and 13 roads (total cost: $69M), both algorithms independently synthesize an optimal 8-road MST with an infrastructure budget of only $37M, saving 46.4% in construction capital.")

    # Section 8
    add_heading_1("8. Empirical Benchmark Results & Comparative Analysis")
    add_body("Rigorous empirical benchmarks were conducted across synthetic connected networks of 10, 25, 50, and 100 intersections using time.perf_counter() and tracemalloc. The algorithms were evaluated with tracing disabled to guarantee pure algorithmic timing.")

    # Add Table
    if bench_df is not None:
        table = doc.add_table(rows=1, cols=7)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = table.rows[0].cells
        cols = ["|V|", "|E|", "Algorithm", "Time (ms)", "Peak Mem (KB)", "Result Edges", "Result Cost"]
        for i, c in enumerate(cols):
            hdr_cells[i].text = c
            hdr_cells[i].paragraphs[0].runs[0].font.bold = True
            hdr_cells[i].paragraphs[0].runs[0].font.name = "Calibri"
            hdr_cells[i].paragraphs[0].runs[0].font.size = Pt(9.5)
            
        for _, row in bench_df.iterrows():
            row_cells = table.add_row().cells
            row_cells[0].text = str(int(row["Intersections"]))
            row_cells[1].text = str(int(row["Roads"]))
            row_cells[2].text = str(row["Algorithm"])
            row_cells[3].text = f"{float(row['Time (ms)']):.4f}"
            row_cells[4].text = f"{float(row['Peak memory (KB)']):.2f}"
            row_cells[5].text = str(row["Roads in result"])
            row_cells[6].text = str(row["Cost of result"])
            for cell in row_cells:
                cell.paragraphs[0].runs[0].font.name = "Calibri"
                cell.paragraphs[0].runs[0].font.size = Pt(9)

    add_heading_2("Key Comparative Insights")
    add_bullet("Dijkstra vs. Bellman-Ford:", "At 100 intersections, Dijkstra required 0.088 ms compared to Bellman-Ford's 0.231 ms (2.6x faster). Dijkstra's heap-based selection scales with O((V+E)log V), making it substantially superior for standard positive-weight routing.")
    add_bullet("BFS vs. DFS:", "Both algorithms exhibit linear O(V+E) execution times (under 0.08 ms at 100 vertices). However, BFS consistently yields the minimum hop count, whereas DFS paths meander, resulting in vastly higher travel costs.")
    add_bullet("Prim vs. Kruskal:", "Both algorithms produce identical optimal total construction costs across all network scales (61 at V=10, 135 at V=25, 377 at V=50, 632 at V=100). Prim's heap-based approach demonstrated slightly faster execution on dense clusters, while Kruskal is particularly elegant when edge lists are pre-sorted.")

    # Section 9
    add_heading_1("9. System Outputs & Visual Verification")
    add_body("The project repository contains complete, high-resolution visual evidence of system operations located in the screenshots/ directory:")
    add_bullet("01_dashboard.png:", "Executive transit overview showing metric stat cards, network summary, and optimal path highlights.")
    add_bullet("02_route_planner.png:", "Commuter route planning interface with route chips and turn-by-turn segment cost breakdown.")
    add_bullet("03_dijkstra_steps.png:", "Full priority queue relaxation table displaying tentative distance updates per step.")
    add_bullet("04_traffic_before_after.png:", "Side-by-side cartographic comparison of original vs congested detour routes.")
    add_bullet("05_bfs_dfs.png:", "Comparative traversal trees illustrating BFS level-wise vs DFS depth-first exploration.")
    add_bullet("06_mst.png:", "Minimum Spanning Tree visualization highlighting accepted roads and Kruskal cycle rejections.")
    add_bullet("07_comparison.png:", "Empirical benchmark charts comparing runtime and memory scaling across all six algorithms.")
    add_bullet("08_graph_data.png:", "Dual graph representations displaying Adjacency List dictionary and Adjacency Matrix heatmap.")
    add_bullet("09_builder.png:", "Interactive Network Builder illustrating dynamic vertex and edge insertion into the topology.")

    # Section 10
    add_heading_1("10. Conclusion & Future Scope")
    add_body("The Smart City Traffic Management and Route Optimization System demonstrates the transformative impact of discrete mathematics and graph algorithms on real-world municipal transportation challenges. By implementing and empirically validating Dijkstra, Bellman-Ford, BFS, DFS, Prim, and Kruskal algorithms from first principles, the system achieves sub-millisecond route optimization, dynamic congestion rerouting, and cost-effective infrastructure synthesis.")
    add_body("Future enhancements will focus on integrating directed graphs for one-way street grids, real-time OpenStreetMap road network imports, heuristic A* routing, and dynamic multi-agent traffic signal timing coordination.")

    doc.save("report/Final_Project_Report.docx")
    print("Saved report/Final_Project_Report.docx")

# ==============================================================================
# 3. Generate PDF Report using ReportLab
# ==============================================================================
def generate_pdf_report():
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    pdf_path = "report/Final_Project_Report.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#12233B'),
        alignment=1, # Center
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1D6FE0'),
        alignment=1,
        spaceAfter=15
    )
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#12233B'),
        spaceBefore=12,
        spaceAfter=6
    )
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#1D6FE0'),
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155'),
        leftIndent=15,
        spaceAfter=3
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("Smart City Traffic Management & Route Optimization System", title_style))
    story.append(Paragraph("Design and Analysis of Algorithms Lab Capstone Report | BCA (AI & DS), Semester V", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1D6FE0"), spaceAfter=10))

    # Executive Summary
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Paragraph(
        "Rapid urbanization has led to increasing traffic congestion, lengthened travel times, and inefficient utilization of municipal road networks. "
        "This project implements a production-grade <b>Smart City Traffic Management and Route Optimization System</b> modeling urban road networks as weighted graphs. "
        "Six classic algorithms—<b>Dijkstra, Bellman-Ford, BFS, DFS, Prim, and Kruskal</b>—were implemented by hand from first principles without external algorithmic libraries. "
        "The system delivers dynamic shortest-path routing, real-time congestion rerouting, network accessibility analysis, minimum spanning tree (MST) infrastructure synthesis, "
        "and empirical performance benchmarks across road networks ranging from 10 to 100 intersections.",
        body_style
    ))

    # Section 1: Introduction
    story.append(Paragraph("1. Introduction & Real-World Problem Context", h1_style))
    story.append(Paragraph(
        "Modern metropolitan transit authorities require algorithmic intelligence to manage complex street networks. "
        "The road infrastructure is abstracted as an undirected graph <i>G = (V, E, W)</i>, where vertices represent intersections, "
        "edges represent bidirectional roadways, and weights represent travel times (minutes) or physical distances (km). "
        "Key goals include optimizing commuter routes, mitigating bottleneck delays, verifying connectivity during emergencies, and planning cost-effective roadway expansions.",
        body_style
    ))

    # Section 2: Architecture
    story.append(Paragraph("2. System Architecture & Dual Graph Model", h1_style))
    story.append(Paragraph(
        "The system architecture strictly decouples computational graph algorithms from presentation interfaces:",
        body_style
    ))
    story.append(Paragraph("• <b>Dual Representation:</b> Adjacency List <i>O(V+E)</i> memory for fast neighbor traversal; Adjacency Matrix <i>O(V²)</i> for <i>O(1)</i> road lookup and matrix visualization.", bullet_style))
    story.append(Paragraph("• <b>Modular Engine:</b> Handcrafted Python algorithm modules (<code>route_planner.py</code>, <code>traffic_analysis.py</code>, <code>connectivity_module.py</code>, <code>mst_planner.py</code>).", bullet_style))
    story.append(Paragraph("• <b>Streamlit Console:</b> Modern operations dashboard with interactive controls, stat cards, and Matplotlib transit maps.", bullet_style))

    # Section 3: Algorithms
    story.append(Paragraph("3. Algorithm Formulations & Functional Roles", h1_style))
    story.append(Paragraph("• <b>Dijkstra's Algorithm (Route Planning):</b> Uses a min-heap priority queue to determine shortest paths under non-negative weights <i>O((V+E) log V)</i>. Records intermediate relaxation traces.", bullet_style))
    story.append(Paragraph("• <b>Bellman-Ford Algorithm (Traffic Analysis):</b> Dynamic programming relaxation of all edges <i>O(V·E)</i>. Handles arbitrary weights, detects negative cycles, and evaluates detour cost savings.", bullet_style))
    story.append(Paragraph("• <b>BFS & DFS (Connectivity):</b> BFS (queue) identifies minimal-hop perimeters; DFS (stack) explores deep structural branches and components.", bullet_style))
    story.append(Paragraph("• <b>Prim & Kruskal (Infrastructure Planning):</b> Synthesizes Minimum Spanning Trees (MST) to connect all intersections with minimal construction capital, using Union-Find loop detection.", bullet_style))

    # Section 4: Benchmark Table
    story.append(Paragraph("4. Experimental Results & Benchmark Analysis", h1_style))
    story.append(Paragraph(
        "Empirical benchmarks were executed across synthetic connected networks of 10, 25, 50, and 100 intersections (measured via <code>time.perf_counter()</code> and <code>tracemalloc</code>):",
        body_style
    ))

    if bench_df is not None:
        table_data = [["|V|", "|E|", "Algorithm", "Time (ms)", "Peak Mem (KB)", "Result Edges", "Result Cost"]]
        for _, r in bench_df.iterrows():
            table_data.append([
                str(int(r["Intersections"])),
                str(int(r["Roads"])),
                str(r["Algorithm"]),
                f"{float(r['Time (ms)']):.4f}",
                f"{float(r['Peak memory (KB)']):.2f}",
                str(r["Roads in result"]),
                str(r["Cost of result"])
            ])
            
        t = Table(table_data, colWidths=[35, 35, 95, 80, 85, 75, 75])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#12233B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('TOPPADDING', (0, 1), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2.5),
        ]))
        story.append(t)

    story.append(Spacer(1, 8))
    story.append(Paragraph("5. Key Analytical Insights & Conclusions", h1_style))
    story.append(Paragraph("• <b>Routing Performance:</b> Dijkstra is ~2.6x faster than Bellman-Ford at 100 vertices, confirming O((V+E)log V) superiority for positive weights.", bullet_style))
    story.append(Paragraph("• <b>Congestion Management:</b> Automated rerouting provides major travel-time savings during severe delays, bypassing congested corridors effectively.", bullet_style))
    story.append(Paragraph("• <b>Capital Optimization:</b> Prim and Kruskal both achieved a 46.4% reduction in construction costs on the sample network, interconnecting all 9 junctions for $37M instead of $69M.", bullet_style))
    story.append(Paragraph("• <b>Visual Verification:</b> All 9 module views have been verified and documented in the <code>screenshots/</code> directory.", bullet_style))

    doc.build(story)
    print("Saved report/Final_Project_Report.pdf")

if __name__ == "__main__":
    print("Generating comprehensive final project reports...")
    generate_markdown_report()
    generate_docx_report()
    generate_pdf_report()
    print("All reports generated successfully!")
