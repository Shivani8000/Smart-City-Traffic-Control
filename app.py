"""
app.py - Smart City Traffic Management and Route Optimization System
=====================================================================
Run with:   streamlit run app.py

This file only builds the PAGES (what the user sees).  The algorithms live in
their own modules so they can be read - and explained in a viva - separately:

    graph_model.py          road network (adjacency list / matrix, sample city)
    route_planner.py        Dijkstra + Bellman-Ford
    traffic_analysis.py     congestion simulation (uses Bellman-Ford)
    connectivity_module.py  BFS + DFS
    mst_planner.py          Prim + Kruskal
    benchmark.py            real timing experiments
    visuals.py / ui.py      drawing and styling
"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import benchmark
from connectivity_module import bfs, check_path_exists, connected_components, dfs
from graph_model import RoadNetwork, build_sample_city, road_key
from mst_planner import kruskal, prim
from route_planner import bellman_ford, dijkstra, find_route
from traffic_analysis import CONGESTION_PRESETS, analyze_congestion, congestion_level
from ui import (ICONS, TONES, adjacency_card, callout_box, esc, fmt, inject_css,
                page_header, route_chips, stat_card, viva_card)
from visuals import COLORS, LEVEL_COLORS, draw_network

st.set_page_config(page_title="Smart City Traffic Control Center", page_icon="🚦", layout="wide")
inject_css()

PAGES = ["Dashboard", "Route Planner", "Traffic Analysis", "Connectivity",
         "Infrastructure Planning", "Algorithm Comparison", "Network Builder", "Graph Data",
         "Viva Guide & About"]


# ==========================================================================
# Shared helpers
# ==========================================================================
def init_state():
    ss = st.session_state
    if "city" not in ss:
        ss["city"] = build_sample_city()
    if "congestion" not in ss:
        ss["congestion"] = {}            # {road_key: congested cost}
    if "route_settings" not in ss:
        ss["route_settings"] = None      # remembered by the Dashboard


def reset_selectors():
    """Forget selectbox choices (they may point to intersections that no longer exist)."""
    for key in [k for k in st.session_state.keys() if str(k).startswith("sel_")]:
        del st.session_state[key]


def replace_network(net):
    st.session_state["city"] = net
    st.session_state["congestion"] = {}
    st.session_state["route_settings"] = None
    reset_selectors()


def active_congestion():
    """Congested roads that still exist and really differ from their normal cost."""
    net = st.session_state["city"]
    out = {}
    for (u, v), w in st.session_state["congestion"].items():
        if net.has_edge(u, v) and w != net.weight(u, v):
            out[road_key(u, v)] = w
    return out


def ratios_of(net, cong):
    return {k: w / net.weight(*k) for k, w in cong.items()}


def overall_congestion(net, cong):
    if not cong:
        return "Clear", "green", "no congested roads"
    worst = congestion_level(max(ratios_of(net, cong).values()))
    label = {"Heavy": "Heavy", "Moderate": "Moderate"}.get(worst, "Light")
    tone = {"Heavy": "red", "Moderate": "amber"}.get(worst, "green")
    return label, tone, f"{len(cong)} road(s) affected"


def show_map(fig):
    st.pyplot(fig)
    plt.close(fig)


def table(rows_or_df, index=False):
    df = rows_or_df if isinstance(rows_or_df, pd.DataFrame) else pd.DataFrame(rows_or_df)
    st.dataframe(df, hide_index=not index)


def require(net, nodes=0, roads=0):
    if net.node_count < nodes or net.edge_count < roads:
        st.info(f"This page needs at least {nodes} intersection(s) and {roads} road(s). "
                "Open **Network Builder** to add them, or reset to the sample city.")
        return False
    return True


def default_index(options, wanted, fallback=0):
    return options.index(wanted) if wanted in options else min(fallback, len(options) - 1)


def pick_pair(prefix, nodes):
    c1, c2 = st.columns(2)
    src = c1.selectbox("Source intersection", nodes, key=f"sel_{prefix}_src",
                       index=default_index(nodes, "City Center", 0))
    dst = c2.selectbox("Destination intersection", nodes, key=f"sel_{prefix}_dst",
                       index=default_index(nodes, "Airport", len(nodes) - 1))
    return src, dst


def road_label(net, key):
    return f"{key[0]} — {key[1]}  (cost {fmt(net.weight(*key))})"


# ==========================================================================
# Sidebar
# ==========================================================================
def sidebar():
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">' + ICONS["junction"] + '</div>'
            '<div><div class="brand-name">Smart City<br>Traffic Control</div>'
            '<div class="brand-sub">Route optimisation console</div></div></div>',
            unsafe_allow_html=True)
        page = st.radio("Navigation", PAGES, label_visibility="collapsed", key="nav")
        st.markdown("---")
        net = st.session_state["city"]
        st.markdown(f'<div class="side-note">Loaded network: {net.node_count} intersections, '
                    f'{net.edge_count} roads.<br>DAA Lab capstone, BCA (AI &amp; DS).</div>',
                    unsafe_allow_html=True)
        if st.button("Reset to sample city"):
            replace_network(build_sample_city())
            st.rerun()
    return page


# ==========================================================================
# Page: Dashboard
# ==========================================================================
def page_dashboard():
    net = st.session_state["city"]
    cong = active_congestion()
    components = connected_components(net.adj)
    connected = len(components) <= 1 and net.node_count > 0
    level, level_tone_name, level_sub = overall_congestion(net, cong)

    pills = [("Network connected" if connected else
              (f"{len(components)} separate areas" if net.node_count else "Network empty"),
              "green" if connected else "amber"),
             (f"Traffic Condition: {level}", level_tone_name),
             (f"{net.node_count} Intersections", "blue"),
             (f"{net.edge_count} Roads", "ink")]
    page_header("Smart City Traffic Control Center",
                "Operations console: real-time monitoring of intersections, road segments, "
                "live route optimization, network connectivity, and congestion impact.", pills)

    # 1. Top KPI Stat Cards
    c = st.columns(4)
    c[0].markdown(stat_card("junction", "Total Intersections", net.node_count,
                            "junctions / graph vertices", "blue"), unsafe_allow_html=True)
    c[1].markdown(stat_card("road", "Total Road Segments", net.edge_count,
                            "two-way road links / edges", "blue"), unsafe_allow_html=True)
    c[2].markdown(stat_card("link", "Network Connectivity",
                            "Connected" if connected else f"{len(components)} areas",
                            "100% reachable" if connected else f"Network split into {len(components)} components",
                            "green" if connected else "amber", small=True), unsafe_allow_html=True)
    c[3].markdown(stat_card("alert", "Traffic Status", level, level_sub,
                            level_tone_name, small=True), unsafe_allow_html=True)

    # 2. Route Optimization Quick Dispatch Bar
    st.write("")
    st.markdown("#### 🚦 Live Route Dispatch & Selected Trip")
    if net.node_count >= 2:
        nodes = net.nodes
        q1, q2, q3, q4 = st.columns([1.5, 1.5, 1.2, 0.8])
        src = q1.selectbox("Origin Junction (Source)", nodes, key="dash_src",
                           index=default_index(nodes, "City Center", 0))
        dst = q2.selectbox("Destination Junction", nodes, key="dash_dst",
                           index=default_index(nodes, "Airport", len(nodes) - 1))
        algo = q3.selectbox("Route Algorithm", ["Dijkstra", "Bellman-Ford"], key="dash_algo")
        use_live = q4.checkbox("Live traffic", value=bool(cong), disabled=not cong, key="dash_live")

        st.session_state["route_settings"] = {"source": src, "target": dst, "algorithm": algo, "live": bool(use_live and cong)}
        work = net.with_weights(cong) if (use_live and cong) else net

        if src == dst:
            has_route = True
            route = {"path": [src], "cost": 0, "algorithm": algo, "found": True}
            st.info(f"Origin and Destination are both **{src}**. Distance is 0 (already at destination).")
        else:
            route = find_route(work.adj, src, dst, algo)
            has_route = bool(route and route["found"])

        st.write("")
        r = st.columns([3, 1, 1])
        if has_route:
            r[0].markdown(route_chips(route["path"], "blue", f"Shortest Route: {src} → {dst}"), unsafe_allow_html=True)
            r[1].markdown(stat_card("cost", "Route Cost", fmt(route["cost"]), "travel time units", "blue"), unsafe_allow_html=True)
            r[2].markdown(stat_card("route", "Segments Used", max(len(route["path"]) - 1, 0), f"via {algo}", "ink", small=True), unsafe_allow_html=True)
        else:
            r[0].error(f"No route found between **{src}** and **{dst}** (isolated components).")
            r[1].markdown(stat_card("cost", "Route Cost", "–", "unreachable", "grey"), unsafe_allow_html=True)
            r[2].markdown(stat_card("route", "Algorithm", algo, "no path", "grey", small=True), unsafe_allow_html=True)
    else:
        st.info("The network needs at least two intersections to dispatch routes.")
        route = None
        has_route = False
        src = dst = None

    # 3. Live Map + Congestion Status & Network Topology Insights
    st.write("")
    left, right = st.columns([2, 1])
    with left:
        shown = net.with_weights(cong) if cong else net
        legend = [("Optimal route", COLORS["blue"])] if has_route else []
        legend += [(lvl, LEVEL_COLORS[lvl]) for lvl in ("Free flow", "Moderate", "Heavy")
                   if any(congestion_level(x) == lvl for x in ratios_of(net, cong).values())]
        show_map(draw_network(shown, route=route["path"] if has_route else None,
                              congestion=ratios_of(net, cong),
                              start=src if has_route else None,
                              end=dst if has_route else None,
                              title="Live smart city network map", legend=legend or None))
    with right:
        ratios = ratios_of(net, cong)
        heavy_cnt = sum(1 for r in ratios.values() if r >= 2.0)
        mod_cnt = sum(1 for r in ratios.values() if 1.25 <= r < 2.0)
        free_cnt = net.edge_count - len(cong)

        cong_items = "".join(
            f'<div style="font-size:0.83rem; margin-bottom:0.25rem;">• <b>{k[0]} — {k[1]}</b>: '
            f'cost {fmt(net.weight(*k))} ➔ <span style="color:#D8392B;font-weight:700;">{fmt(w)}</span> '
            f'({congestion_level(w / net.weight(*k))})</div>' for k, w in cong.items()
        ) if cong else '<div style="font-size:0.83rem; color:#1E9E6A;">All roads clear at baseline costs.</div>'

        st.markdown(
            '<div class="panel"><h4>Traffic Condition Breakdown</h4>'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:0.35rem;">'
            f'<span>🟢 Free Flow Roads:</span> <b>{free_cnt}</b></div>'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:0.35rem;">'
            f'<span>🟡 Moderate Traffic:</span> <b>{mod_cnt}</b></div>'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:0.75rem;">'
            f'<span>🔴 Heavy Congestion:</span> <b>{heavy_cnt}</b></div>'
            f'<div class="panel-label">Active Congested Roads ({len(cong)})</div>'
            f'{cong_items}</div>',
            unsafe_allow_html=True)

        st.write("")
        edges = shown.edges()
        if edges:
            busiest = max(net.nodes, key=net.degree)
            longest = max(edges, key=lambda e: e[2])
            shortest = min(edges, key=lambda e: e[2])
            avg = sum(e[2] for e in edges) / len(edges)
            density = net.edge_count / max(net.node_count * (net.node_count - 1) / 2, 1)
            st.markdown(
                '<div class="panel"><h4>Network Topology Insights</h4>'
                f'<div class="panel-label">Busiest Junction</div><b>{esc(busiest)}</b> ({net.degree(busiest)} roads connected)<br><br>'
                f'<div class="panel-label">Highest Cost Road</div><b>{esc(longest[0])} — {esc(longest[1])}</b> (cost {fmt(longest[2])})<br><br>'
                f'<div class="panel-label">Lowest Cost Road</div><b>{esc(shortest[0])} — {esc(shortest[1])}</b> (cost {fmt(shortest[2])})<br><br>'
                f'<div class="panel-label">Average Road Cost</div><b>{avg:.2f} units</b><br><br>'
                f'<div class="panel-label">Network Density</div><b>{density:.1%}</b></div>',
                unsafe_allow_html=True)


# ==========================================================================
# Page: Route Planner  (Dijkstra / Bellman-Ford)
# ==========================================================================
def distance_progress_table(run, nodes):
    """Textbook table: one row per step, one column per intersection."""
    start_row = {"Step": "Start"}
    for n in nodes:
        start_row[n] = "0" if n == run["source"] else "∞"
    rows = [start_row]
    if run["algorithm"] == "Dijkstra":
        for s in run["steps"]:
            row = {"Step": f"{s['step']}. settle {s['node']}"}
            for n in nodes:
                row[n] = fmt(s["dist_snapshot"][n]) + (" ✓" if n in s["settled"] else "")
            rows.append(row)
    else:
        for p in run["passes"]:
            row = {"Step": f"Pass {p['pass']}"}
            for n in nodes:
                row[n] = fmt(p["dist_snapshot"][n])
            rows.append(row)
    return pd.DataFrame(rows).set_index("Step")


def render_steps(run):
    if run["algorithm"] == "Dijkstra":
        st.caption("Each step: take the unfinished intersection with the smallest distance, "
                   "lock its distance, then try to improve its neighbours (relaxation).")
        for s in run["steps"]:
            with st.expander(f"Step {s['step']}: settle {s['node']} (distance {fmt(s['distance'])})"):
                st.write(f"**{s['node']}** has the smallest tentative distance among the unfinished "
                         f"intersections, so **{fmt(s['distance'])}** is final. Relaxing its roads:")
                if s["relaxations"]:
                    table([{"Neighbour": r["neighbor"], "Road cost": fmt(r["edge_cost"]),
                            "Best known": fmt(r["old_distance"]),
                            f"Via {s['node']}": fmt(r["new_distance"]),
                            "Improved?": "Yes, updated" if r["updated"] else "No"}
                           for r in s["relaxations"]])
                else:
                    st.caption("No unfinished neighbours left to update.")
    else:
        st.caption("Each pass relaxes EVERY road once. After pass k, every route that uses "
                   "k roads or fewer is correct. If a pass changes nothing, we stop early.")
        for p in run["passes"]:
            with st.expander(f"Pass {p['pass']}: {len(p['updates'])} distance(s) improved"):
                if p["updates"]:
                    table([{"Road": f"{u['from']} → {u['to']}", "Road cost": fmt(u["edge_cost"]),
                            "Old distance": fmt(u["old_distance"]),
                            "New distance": fmt(u["new_distance"])} for u in p["updates"]])
                else:
                    st.write("Nothing changed in this pass, so all distances are final.")
        st.caption("Final check: no road can still be relaxed, so there is no negative cycle."
                   if not run["negative_cycle"] else "A negative cycle exists: no shortest route.")


def page_route_planner():
    net = st.session_state["city"]
    cong = active_congestion()
    page_header("Route Planner", "Pick two intersections and let the algorithm find the cheapest route.",
                [("Dijkstra", "blue"), ("Bellman-Ford", "violet")])
    if not require(net, nodes=2):
        return
    nodes = net.nodes

    src, dst = pick_pair("rp", nodes)
    o1, o2, o3 = st.columns([1.3, 1.2, 1.2])
    algorithm = o1.radio("Algorithm", ["Dijkstra", "Bellman-Ford"], horizontal=True, key="sel_rp_algo")
    live = o2.checkbox("Use live traffic", value=False, disabled=not cong, key="sel_rp_live",
                       help="Plan with the congested road costs set in Traffic Analysis.")
    show_steps = o3.checkbox("Show step-by-step calculation", value=False, key="sel_rp_steps")

    if src == dst:
        st.info(f"Source and destination are both **{src}**. The vehicle is already at the destination, so total travel cost is **0** units.")
        st.markdown(route_chips([src], "blue", "Selected Trip"), unsafe_allow_html=True)
        st.write("")
        c = st.columns(3)
        c[0].markdown(stat_card("cost", "Total travel cost", "0", "already at destination", "green"), unsafe_allow_html=True)
        c[1].markdown(stat_card("road", "Roads used", 0, "no travel needed", "blue"), unsafe_allow_html=True)
        c[2].markdown(stat_card("chart", "Algorithm work", 0, "trivial single-node path", "ink"), unsafe_allow_html=True)
        show_map(draw_network(work, start=src, end=dst, title=f"Trip Status: Already at {src}"))
        return

    work = net.with_weights(cong) if (live and cong) else net
    result = find_route(work.adj, src, dst, algorithm)
    st.session_state["route_settings"] = {"source": src, "target": dst, "algorithm": algorithm,
                                          "live": bool(live and cong)}
    run = result["run"]

    if not result["found"]:
        st.error(f"No route exists from **{src}** to **{dst}**: they are in disconnected parts of the network. "
                 "Add a road in Network Builder to link them.")
        show_map(draw_network(work, start=src, end=dst, title="Network"))
        return

    if run["negative_cycle"]:
        st.error("Negative cycle detected, so shortest routes are undefined.")
        return

    st.success(f"Best route found with {algorithm}: {len(result['path']) - 1} road(s), "
               f"total cost {fmt(result['cost'])}.")
    st.markdown(route_chips(result["path"], "blue", "Shortest route"), unsafe_allow_html=True)
    st.write("")
    c = st.columns(3)
    c[0].markdown(stat_card("cost", "Total travel cost", fmt(result["cost"]), "units", "blue"),
                  unsafe_allow_html=True)
    c[1].markdown(stat_card("road", "Roads used", len(result["path"]) - 1, "segments", "blue"),
                  unsafe_allow_html=True)
    steps_n = len(run["steps"]) if algorithm == "Dijkstra" else len(run["passes"])
    c[2].markdown(stat_card("chart", "Algorithm work", steps_n,
                            "intersections settled" if algorithm == "Dijkstra" else "passes over all roads",
                            "ink"), unsafe_allow_html=True)
    st.write("")

    tab_names = ["Map", "Route breakdown", "Distance updates"] + (["Step-by-step"] if show_steps else [])
    tabs = st.tabs(tab_names)
    with tabs[0]:
        ratios = ratios_of(net, cong) if (live and cong) else {}
        show_map(draw_network(work, route=result["path"], start=src, end=dst, congestion=ratios,
                              title=f"{src} to {dst}",
                              legend=[("Selected route", COLORS["blue"]), ("Other roads", COLORS["road"])]))
    with tabs[1]:
        table([{"From": s["from"], "To": s["to"], "Road cost": fmt(s["cost"]),
                "Running total": fmt(s["cumulative"])} for s in result["segments"]])
    with tabs[2]:
        st.caption("Distance from the source to every intersection, after each step. "
                   "∞ = not reached yet" + (", ✓ = distance is final." if algorithm == "Dijkstra" else "."))
        st.dataframe(distance_progress_table(run, nodes))
        st.markdown("**Final distances and where each route came from**")
        table([{"Intersection": n, "Shortest distance": fmt(run["dist"][n]),
                "Arrive from": run["prev"][n] or "–"} for n in nodes])
    if show_steps:
        with tabs[3]:
            render_steps(run)

    with st.expander("How does this algorithm work? (Detailed Viva Explanation)"):
        if algorithm == "Dijkstra":
            st.markdown(
                "### Dijkstra's Algorithm (Greedy Single-Source Shortest Path)\n\n"
                "**Core Idea:** Maintains a set of settled intersections whose shortest distance from the source is finalized.\n\n"
                "1. **Initialization:** Set `dist[source] = 0` and `dist[v] = ∞` for all other vertices. Insert `(0, source)` into a min-priority queue (heap).\n"
                "2. **Greedy Selection:** Extract the vertex `u` with the smallest tentative distance `dist[u]`. Mark `u` as settled.\n"
                "3. **Edge Relaxation:** For every unsettled neighbor `v` connected by an edge of weight `w(u, v)`:\n"
                "   $$\\text{if } dist[u] + w(u, v) < dist[v] \\implies dist[v] = dist[u] + w(u, v), \\quad prev[v] = u$$\n"
                "   Push the updated candidate distance to the heap.\n"
                "4. **Termination:** Stop when the destination is settled or the priority queue is empty. Reconstruct the route by backtracking through `prev`.\n\n"
                "**Why Edge Weights Must Be Non-Negative:**\n"
                "Dijkstra assumes that once a vertex is settled, its distance can never be decreased by extending a longer path. "
                "Negative edges violate this greedy property, potentially causing Dijkstra to return incorrect routes.\n\n"
                "**Complexity:**\n"
                "- **Time Complexity:** $O((V + E) \\log V)$ using an adjacency list and binary heap.\n"
                "- **Space Complexity:** $O(V)$ for distance table, previous pointers, and heap.")
        else:
            st.markdown(
                "### Bellman-Ford Algorithm (Dynamic Programming Shortest Path)\n\n"
                "**Core Idea:** Iteratively relaxes all edges $V - 1$ times. Guaranteed to find the optimal path in graphs with any edge weights (even negative).\n\n"
                "1. **Initialization:** Set `dist[source] = 0` and `dist[v] = ∞` for all other vertices.\n"
                "2. **Repeated Passes (1 to $V - 1$):** In each pass, scan through **every edge** $(u, v)$ with weight $w$:\n"
                "   $$\\text{if } dist[u] \\neq \\infty \\text{ and } dist[u] + w < dist[v] \\implies dist[v] = dist[u] + w, \\quad prev[v] = u$$\n"
                "   *Why $V - 1$ passes?* In a graph of $V$ vertices, any simple path has at most $V - 1$ edges. Pass $k$ guarantees shortest paths of up to $k$ edges.\n"
                "3. **Early Exit Optimization:** If a pass produces zero updates, distances have converged early and the loop terminates.\n"
                "4. **Negative Cycle Detection (Pass $V$):** Scan all edges one extra time. If any edge can still be relaxed ($dist[u] + w < dist[v]$), "
                "the graph contains a **negative cycle**, meaning path cost can be reduced infinitely.\n\n"
                "**Complexity:**\n"
                "- **Time Complexity:** $O(V \\cdot E)$ — slower than Dijkstra, but significantly more flexible.\n"
                "- **Space Complexity:** $O(V)$ for distance and predecessor tables.")


# ==========================================================================
# Page: Traffic Analysis  (Bellman-Ford)
# ==========================================================================
def page_traffic():
    net = st.session_state["city"]
    page_header("Traffic Analysis", "Slow down some roads, then see how the best route and its cost change.",
                [("Bellman-Ford", "violet")])
    if not require(net, nodes=2, roads=1):
        return

    src, dst = pick_pair("tr", net.nodes)
    if src == dst:
        st.info(f"Source and destination are both **{src}**. Choose two different intersections to observe route changes and congestion detour impact.")
        show_map(draw_network(net, start=src, end=dst, title=f"Selected: {src}"))
        return

    st.markdown("#### 1. Create or simulate congestion")
    st.markdown("**Quick Urban Congestion Scenarios (1-Click Demos):**")
    p_cols = st.columns(len(CONGESTION_PRESETS) + 1)
    for i, (name, p_data) in enumerate(CONGESTION_PRESETS.items()):
        if p_cols[i].button(name, key=f"btn_tr_preset_{i}", help=p_data["description"]):
            st.session_state["congestion"] = dict(p_data["changes"])
            st.rerun()
    if p_cols[-1].button("Clear All", key="btn_tr_preset_clear", help="Reset all roads to baseline normal cost"):
        st.session_state["congestion"] = {}
        st.rerun()

    st.write("")
    keys = [road_key(u, v) for u, v, _ in net.edges()]
    demo = road_key("City Center", "Mall")
    picked = st.multiselect("Or manually select roads to congest", keys, key="sel_tr_roads",
                            default=[demo] if demo in keys else [],
                            format_func=lambda k: road_label(net, k))
    m1, m2, m3 = st.columns([1.4, 1, 1.3])
    mode = m1.radio("How to change the travel cost", ["Set new cost", "Multiply normal cost"],
                    horizontal=True, key="sel_tr_mode")
    if mode == "Set new cost":
        amount = m2.number_input("New cost", min_value=0.5, value=15.0, step=1.0, key="sel_tr_val")
    else:
        amount = m2.number_input("Multiplier", min_value=0.5, value=3.0, step=0.5, key="sel_tr_mult")
    with m3:
        st.write("")
        b1, b2 = st.columns(2)
        apply_clicked = b1.button("Apply", type="primary", key="btn_tr_apply")
        reset_clicked = b2.button("Clear all", key="btn_tr_clear")

    if apply_clicked:
        if not picked:
            st.warning("Select at least one road first.")
        else:
            for k in picked:
                new = amount if mode == "Set new cost" else net.weight(*k) * amount
                st.session_state["congestion"][k] = round(float(new), 2)
    if reset_clicked:
        st.session_state["congestion"] = {}

    cong = active_congestion()
    st.markdown("#### 2. Route & Network Impact")
    if not cong:
        st.info("No congestion yet. Select roads above and press **Apply**. "
                "The City Center — Mall road is pre-selected as a demo: try setting its cost to 15.")
        base = find_route(net.adj, src, dst, "Bellman-Ford")
        if base["found"]:
            st.markdown(route_chips(base["path"], "blue", f"Normal route (cost {fmt(base['cost'])})"),
                        unsafe_allow_html=True)
            show_map(draw_network(net, route=base["path"], start=src, end=dst, title="Normal traffic"))
        return

    res = analyze_congestion(net, cong, src, dst)
    if not res["reachable"]:
        st.error("These two intersections are not connected, so there is no route to compare.")
        return

    ratios = ratios_of(net, cong)
    if res["route_changed"]:
        hit = ", ".join(f"{a} — {b}" for a, b in res["roads_hit"]) or "the congested roads"
        st.warning(f"Congestion on **{hit}** made the old route slower, so the best route changed. "
                   f"Staying on the old route would now cost **{fmt(res['stay_cost'])}**; "
                   f"the detour costs **{fmt(res['cost_after'])}** and saves **{fmt(res['detour_saving'])}**.")
    elif res["extra_cost"] > 0:
        st.warning("The best route is the same, but it is now more expensive.")
    else:
        st.success("The congested roads are not on your best route, so this trip is not affected.")

    c = st.columns(4)
    c[0].markdown(stat_card("cost", "Original cost", fmt(res["cost_before"]), "normal traffic", "blue"),
                  unsafe_allow_html=True)
    worse = res["extra_cost"] > 0
    c[1].markdown(stat_card("cost", "Updated cost", fmt(res["cost_after"]), "with congestion",
                            "red" if worse else "green"), unsafe_allow_html=True)
    c[2].markdown(stat_card("alert", "Cost difference", f"{res['extra_cost']:+g}",
                            f"{res['extra_pct']:+.1f}% vs normal", "red" if worse else "green"),
                  unsafe_allow_html=True)
    c[3].markdown(stat_card("route", "Route", "Rerouted" if res["route_changed"] else "Unchanged",
                            "a different path is now best" if res["route_changed"] else "same roads as before",
                            "amber" if res["route_changed"] else "green", small=True), unsafe_allow_html=True)
    st.write("")

    r1, r2 = st.columns(2)
    r1.markdown(route_chips(res["path_before"], "blue", "Original route"), unsafe_allow_html=True)
    r2.markdown(route_chips(res["path_after"], "violet" if res["route_changed"] else "blue", "Updated route"),
                unsafe_allow_html=True)
    st.write("")

    m1, m2 = st.columns(2)
    with m1:
        show_map(draw_network(net, route=res["path_before"], start=src, end=dst,
                              title="Before: normal traffic", figsize=(7, 5)))
    with m2:
        present = [lvl for lvl in ("Moderate", "Heavy") if any(congestion_level(x) == lvl for x in ratios.values())]
        legend = [("Route", COLORS["violet"] if res["route_changed"] else COLORS["blue"])] + \
                 [(f"{lvl} congestion", LEVEL_COLORS[lvl]) for lvl in present]
        show_map(draw_network(res["congested"], route=res["path_after"], start=src, end=dst,
                              congestion=ratios, title="After: with congestion", legend=legend,
                              highlight_color=COLORS["violet"] if res["route_changed"] else COLORS["blue"],
                              figsize=(7, 5)))

    st.markdown("#### 3. Traffic impact statistics")
    imp = res["impact"]
    s = st.columns(4)
    s[0].markdown(stat_card("road", "Roads congested", f"{len(cong)} of {net.edge_count}", "", "amber"),
                  unsafe_allow_html=True)
    s[1].markdown(stat_card("chart", "Average trip cost", f"{imp['avg_before']:.2f} → {imp['avg_after']:.2f}",
                            "over every pair of intersections", "ink", small=True), unsafe_allow_html=True)
    s[2].markdown(stat_card("route", "Trips made slower", f"{imp['affected']} of {imp['pairs']}",
                            "all pairs of intersections", "amber"), unsafe_allow_html=True)
    w = imp["worst"]
    s[3].markdown(stat_card("alert", "Worst-hit trip", f"+{fmt(w['increase'])}" if w else "–",
                            f"{w['from']} to {w['to']}" if w else "", "red", small=True),
                  unsafe_allow_html=True)
    st.write("")
    table([{"Road": r["road"], "Normal cost": fmt(r["normal"]), "Current cost": fmt(r["now"]),
            "Change": f"{r['change']:+g}", "Level": r["level"]} for r in res["table"]])

    with st.expander("Why Bellman-Ford in this module?"):
        st.markdown(
            "Traffic changes the **weights** of the graph, so this module needs an algorithm that "
            "makes no assumptions about them.\n\n"
            "- Bellman-Ford handles **negative adjustments** too (for example a toll refund on a one-way road) "
            "and **detects negative cycles** instead of returning a wrong answer. Dijkstra cannot do either "
            "(see the demo in *Algorithm Comparison*).\n"
            "- Its pass-by-pass design is easy to show and explain.\n"
            "- The cost is speed: O(V × E) against Dijkstra's O((V + E) log V) - negligible for a city-sized map.\n\n"
            "For ordinary positive travel times both algorithms give the same routes; Route Planner uses Dijkstra by default.")
    with st.expander("Bellman-Ford passes (after congestion)"):
        render_steps(res["run_after"])


# ==========================================================================
# Page: Connectivity  (BFS / DFS)
# ==========================================================================
def page_connectivity():
    net = st.session_state["city"]
    page_header("Connectivity Analysis", "Which intersections can be reached from a starting point, and in what order?",
                [("BFS", "teal"), ("DFS", "violet")])
    if not require(net, nodes=1):
        return
    start = st.selectbox("Starting intersection", net.nodes, key="sel_cn_start",
                         index=default_index(net.nodes, "City Center", 0))

    b, d = bfs(net.adj, start), dfs(net.adj, start)
    comps = connected_components(net.adj)
    reach = set(b["order"])
    unreachable = [n for n in net.nodes if n not in reach]

    c = st.columns(3)
    c[0].markdown(stat_card("junction", "Reachable intersections", f"{len(reach)} of {net.node_count}",
                            f"from {start}", "green" if not unreachable else "amber"), unsafe_allow_html=True)
    c[1].markdown(stat_card("link", "Separate areas", len(comps),
                            "1 = fully connected", "green" if len(comps) == 1 else "amber"), unsafe_allow_html=True)
    depth = max(b["level"].values())
    c[2].markdown(stat_card("road", "Furthest junction (fewest roads)", depth, "roads away, found by BFS", "teal"),
                  unsafe_allow_html=True)
    st.write("")
    if unreachable:
        st.warning("Cannot be reached from here: " + ", ".join(unreachable))
    else:
        st.success("Every intersection can be reached from this starting point.")

    left, right = st.columns(2)
    for col, result, color, tint, label in ((left, b, COLORS["teal"], "#BFE9EC", "BFS"),
                                            (right, d, COLORS["violet"], "#DCCFF5", "DFS")):
        with col:
            st.markdown(route_chips(result["order"], "teal" if label == "BFS" else "violet",
                                    f"{label} traversal order"), unsafe_allow_html=True)
            fills = {n: tint for n in result["order"]}
            fills.update({n: "#FBE0DD" for n in unreachable})
            fills[start] = color
            show_map(draw_network(net, highlight_edges=result["tree_edges"], highlight_color=color,
                                  badges={n: str(i + 1) for i, n in enumerate(result["order"])},
                                  node_fill=fills, dim_others=True,
                                  title=f"{label}: numbers show the visiting order",
                                  legend=[("Road used to reach a new junction", color), ("Unused road", COLORS["faint"])],
                                  figsize=(7, 5)))
    t1, t2 = st.tabs(["BFS: queue trace", "DFS: stack trace"])
    for tab, result in ((t1, b), (t2, d)):
        with tab:
            st.caption({"BFS": "BFS takes junctions from the front of a queue, so it explores in rings: "
                               "all neighbours first, then their neighbours.",
                        "DFS": "DFS takes junctions from the top of a stack, so it keeps going down one road "
                               "until it is stuck, then backs up."}[result["algorithm"]])
            table([{"Step": t["step"], "Visit": t["visit"],
                    "Roads from start": result["level"][t["visit"]],
                    result["container_label"]: ", ".join(t["container_after"]) or "(empty)"}
                   for t in result["trace"]])
    if len(comps) > 1:
        with st.expander("Separate areas of the network"):
            for i, comp in enumerate(comps, 1):
                st.write(f"**Area {i}:** " + ", ".join(comp))

    st.write("")
    st.markdown("#### 🔗 Check Reachability Between Any Two Intersections")
    st.caption("Test if any two intersections in the city can reach each other and find the fewest-roads path (unweighted BFS shortest path).")
    c_a, c_b, c_btn = st.columns([1.5, 1.5, 1])
    n_a = c_a.selectbox("Origin Intersection", net.nodes, key="reach_sel_a", index=0)
    n_b = c_b.selectbox("Target Intersection", net.nodes, key="reach_sel_b", index=min(1, len(net.nodes) - 1))
    with c_btn:
        st.write("")
        btn_reach = st.button("Check Reachability", key="btn_check_reach", type="primary")

    if btn_reach or st.session_state.get("reach_active"):
        st.session_state["reach_active"] = True
        can_reach, hop_path = check_path_exists(net.adj, n_a, n_b)
        if can_reach:
            st.success(f"**Reachable!** A connected road path exists between **{n_a}** and **{n_b}** ({len(hop_path) - 1} road hop(s)).")
            st.markdown(route_chips(hop_path, "teal", "Fewest-Hops Connection Route"), unsafe_allow_html=True)
            show_map(draw_network(net, route=hop_path, start=n_a, end=n_b, title=f"Connection Path: {n_a} to {n_b}"))
        else:
            st.error(f"**Unreachable!** No road path connects **{n_a}** and **{n_b}**. They are in isolated components of the network.")



# ==========================================================================
# Page: Infrastructure Planning  (Prim / Kruskal)
# ==========================================================================
def mst_view(net, result, color, tint):
    total_all = sum(w for _, _, w in net.edges())
    if not result["spanning"]:
        if result["algorithm"] == "Prim":
            st.warning("The network is not fully connected: Prim only covers the start intersection's area "
                       f"({len(result['covered'])} of {net.node_count} intersections). Kruskal gives a forest for all areas.")
        else:
            st.warning(f"The network is not fully connected: Kruskal produced a forest of {result['trees']} trees.")
    c = st.columns(3)
    c[0].markdown(stat_card("cost", "Total construction cost", fmt(result["total_cost"]),
                            "cheapest way to connect everything", "green"), unsafe_allow_html=True)
    c[1].markdown(stat_card("road", "Roads selected", len(result["edges"]),
                            f"of {net.edge_count} existing roads", "blue"), unsafe_allow_html=True)
    c[2].markdown(stat_card("chart", "Cost avoided", fmt(total_all - result["total_cost"]),
                            f"if all {net.edge_count} roads were built: {fmt(total_all)}", "ink"),
                  unsafe_allow_html=True)
    st.write("")
    left, right = st.columns(2)
    with left:
        show_map(draw_network(net, title="Original network", figsize=(7, 5)))
    with right:
        chosen = [(u, v) for u, v, _ in result["edges"]]
        show_map(draw_network(net, highlight_edges=chosen, highlight_color=color, dim_others=True,
                              node_fill={n: tint for n in net.nodes}, title=f"{result['algorithm']} minimum spanning tree",
                              legend=[("Selected road", color), ("Not needed", COLORS["faint"])], figsize=(7, 5)))
    t1, t2 = st.tabs(["Selected roads", "Step-by-step decisions"])
    with t1:
        table([{"#": i, "Road": f"{u} — {v}", "Cost": fmt(w)} for i, (u, v, w) in enumerate(result["edges"], 1)])
        st.markdown(f"**Total infrastructure cost: {fmt(result['total_cost'])}**")
    with t2:
        st.caption("Prim: pick the cheapest road that reaches a NEW intersection." if result["algorithm"] == "Prim"
                   else "Kruskal: go through roads from cheapest to costliest; accept a road unless it closes a loop.")
        table([{"Road considered": s["road"], "Cost": fmt(s["cost"]), "Decision": s["decision"],
                "Running total": fmt(s["total"])} for s in result["steps"]])


def page_infrastructure():
    net = st.session_state["city"]
    page_header("Infrastructure Planning",
                "If we had to build the road network from scratch, which roads give the cheapest full connection?",
                [("Prim", "green"), ("Kruskal", "magenta")])
    if not require(net, nodes=2, roads=1):
        return
    tab_p, tab_k, tab_c = st.tabs(["Prim's algorithm", "Kruskal's algorithm", "Prim vs Kruskal"])
    with tab_p:
        start = st.selectbox("Start building from", net.nodes, key="sel_mst_start")
        p = prim(net.adj, start)
        mst_view(net, p, COLORS["green"], "#CDEBDD")
    k = kruskal(net.adj)
    with tab_k:
        mst_view(net, k, COLORS["magenta"], "#F3D3E6")
    with tab_c:
        p = prim(net.adj, st.session_state.get("sel_mst_start", net.nodes[0]))
        same = p["total_cost"] == k["total_cost"]
        (st.success if same else st.warning)(
            f"Prim total = {fmt(p['total_cost'])}, Kruskal total = {fmt(k['total_cost'])}. "
            + ("Both algorithms find a minimum spanning tree with the same total cost." if same else
               "Totals differ because the network is disconnected (Prim covers one area only)."))
        pe = {road_key(u, v) for u, v, _ in p["edges"]}
        ke = {road_key(u, v) for u, v, _ in k["edges"]}
        table([{"Road": f"{a} — {b}", "Cost": fmt(net.weight(a, b)),
                "In Prim's tree": "Yes" if (a, b) in pe else "–",
                "In Kruskal's tree": "Yes" if (a, b) in ke else "–"}
               for a, b in sorted(pe | ke)])
        st.caption("If two roads have equal cost the two algorithms may pick different roads, "
                   "but the total cost is always the same.")
    with st.expander("Why is an MST useful for infrastructure planning?"):
        st.markdown(
            "A minimum spanning tree connects **every** intersection using the **cheapest** set of roads, with "
            "no loops (a loop means paying for a road nobody needs for connectivity). It is a natural first "
            "plan for laying new roads, cables, water pipes or metro lines. Real projects then add extra roads "
            "on top of the MST for redundancy.")


# ==========================================================================
# Page: Algorithm Comparison
# ==========================================================================
@st.cache_data(show_spinner=False)
def cached_benchmark(seed, min_seconds):
    return benchmark.run_benchmark(seed=seed, min_seconds=min_seconds)


def describe(row):
    if row["Algorithm"] in ("Prim", "Kruskal"):
        return f"{row['Roads in result']} roads, total cost {fmt(row['Cost of result'])}"
    if row["Algorithm"] in ("BFS", "DFS"):
        return f"path of {row['Roads in result']} roads (cost {fmt(row['Cost of result'])})"
    return f"cost {fmt(row['Cost of result'])} over {row['Roads in result']} roads"


QUALITATIVE = {
    ("BFS", "DFS"): {
        "Purpose": ("Explore level by level; find the FEWEST-roads route", "Explore one branch fully; test reachability, find areas and loops"),
        "Traversal behaviour": ("Queue (first in, first out): all neighbours before going deeper", "Stack (last in, first out): goes deep, then backtracks"),
        "Time complexity": ("O(V + E)", "O(V + E)"),
        "Finds cheapest route?": ("No (ignores road costs), only fewest roads", "No guarantee at all"),
        "Suitable use case": ("Nearest hospital by number of junctions, emergency spread", "Checking if the city is connected, finding isolated areas"),
    },
    ("Dijkstra", "Bellman-Ford"): {
        "Shortest path": ("Yes, when all costs are ≥ 0", "Yes, also with negative costs"),
        "Edge-weight requirement": ("Non-negative only", "Any weight; detects negative cycles"),
        "Approach": ("Greedy: lock the closest unfinished junction (priority queue)", "Relax every road, V − 1 times"),
        "Time complexity": ("O((V + E) log V)", "O(V × E)"),
        "Suitable use case": ("Everyday route planning (GPS)", "Traffic what-if analysis, networks with adjustments/discounts"),
    },
    ("Prim", "Kruskal"): {
        "MST construction": ("Grows ONE tree outward from a start junction", "Merges many small trees by adding cheapest safe roads"),
        "Approach": ("Vertex-based greedy with a heap", "Edge-based greedy: sort roads + Union-Find"),
        "Time complexity": ("O(E log V) with heap", "O(E log E) (sorting)"),
        "Disconnected network": ("Covers only the start's area", "Gives a spanning forest"),
        "Suitable use case": ("Dense networks (many roads), growing a network from a hub", "Sparse networks, planning from a list of candidate roads"),
    },
}


def pair_tab(df, a, b):
    qual = QUALITATIVE[(a, b)]
    st.markdown("**How they differ**")
    table([{"Aspect": k, a: v[0], b: v[1]} for k, v in qual.items()])

    rows, mem_rows = [], []
    for n in sorted(df["Intersections"].unique()):
        ra = df[(df["Intersections"] == n) & (df["Algorithm"] == a)].iloc[0]
        rb = df[(df["Intersections"] == n) & (df["Algorithm"] == b)].iloc[0]
        faster, slower = (a, b) if ra["Time (ms)"] <= rb["Time (ms)"] else (b, a)
        ratio = max(ra["Time (ms)"], rb["Time (ms)"]) / max(min(ra["Time (ms)"], rb["Time (ms)"]), 1e-12)
        rows.append({"Intersections": n, "Roads": ra["Roads"],
                     f"{a} time (ms)": f"{ra['Time (ms)']:.4f}", f"{b} time (ms)": f"{rb['Time (ms)']:.4f}",
                     "Faster": f"{faster} ({ratio:.1f}× quicker)",
                     f"{a} result": describe(ra), f"{b} result": describe(rb)})
        mem_rows.append({"Intersections": n, f"{a} peak memory (KB)": f"{ra['Peak memory (KB)']:.1f}",
                         f"{b} peak memory (KB)": f"{rb['Peak memory (KB)']:.1f}"})
    st.markdown("**Measured on your computer just now**")
    table(rows)
    pivot = df.pivot(index="Intersections", columns="Algorithm", values="Time (ms)")[[a, b]]
    st.markdown("Execution time (ms) as the network grows")
    st.line_chart(pivot)
    with st.expander("Memory usage"):
        table(mem_rows)


def page_comparison():
    net = st.session_state["city"]
    page_header("Algorithm Comparison",
                "Real experiments on random networks of 10, 25, 50 and 100 intersections. "
                "Every number below was measured, none is typed in.",
                [("6 algorithms", "blue")])
    with st.expander("Experiment settings", expanded=False):
        s1, s2, s3 = st.columns([1, 1, 1])
        seed = s1.number_input("Random seed (same seed = same networks)", 0, 9999, 42, key="cmp_seed")
        min_s = s2.slider("Measuring time per algorithm (seconds)", 0.01, 0.30, 0.03, 0.01, key="cmp_time",
                          help="Longer = steadier averages.")
        s3.write("")
        if s3.button("Re-run experiments"):
            st.cache_data.clear()
    with st.spinner("Running experiments..."):
        df = cached_benchmark(int(seed), float(min_s))

    check = benchmark.agreement_report(df)
    if check[["Dijkstra = Bellman-Ford", "Prim = Kruskal"]].all().all():
        st.success("Correctness check passed: on every network Dijkstra and Bellman-Ford found the same route cost, "
                   "and Prim and Kruskal found the same total MST cost.")
    else:
        st.error("Correctness check FAILED - please review the algorithms.")
    st.caption("Timings are averages over many repeated runs and depend on your computer; the pattern matters, not the exact numbers. "
               "Dijkstra and Bellman-Ford run to every intersection (source J1); routes are measured to the last intersection.")

    t = st.tabs(["Dijkstra vs Bellman-Ford (Head-to-Head)", "Overview (Multi-Size)", "BFS vs DFS",
                 "Dijkstra vs Bellman-Ford (Scaling)", "Prim vs Kruskal", "Your Network (All 6)", "Negative-Cost Demo"])
    with t[0]:
        st.markdown("### Head-to-Head Shortest Path Comparison on Active City Network")
        if net.node_count < 2:
            st.info("Add at least two intersections to run head-to-head comparison.")
        else:
            c1, c2 = st.columns(2)
            s_node = c1.selectbox("Origin Intersection", net.nodes, key="cmp_h2h_src", index=default_index(net.nodes, "City Center", 0))
            t_node = c2.selectbox("Destination Intersection", net.nodes, key="cmp_h2h_dst", index=default_index(net.nodes, "Airport", len(net.nodes) - 1))

            if s_node == t_node:
                st.info("Select two different intersections for meaningful algorithm comparison.")
            else:
                comp = benchmark.compare_shortest_path_algos(net, s_node, t_node, min_seconds=0.02)
                dj = comp["Dijkstra"]
                bf = comp["Bellman-Ford"]

                if comp["same_cost"]:
                    st.success(f"✓ **Agreement Verified:** Both algorithms found the identical optimal route cost of **{fmt(dj['cost'])}** units.")
                else:
                    st.warning("Routes or costs differ between algorithms.")

                col_dj, col_bf = st.columns(2)
                with col_dj:
                    st.markdown("#### ⚡ Dijkstra's Algorithm")
                    st.markdown(route_chips(dj["path"], "blue", "Selected Route"), unsafe_allow_html=True)
                    st.write("")
                    d1, d2 = st.columns(2)
                    d1.markdown(stat_card("cost", "Total Cost", fmt(dj["cost"]), "optimal units", "blue"), unsafe_allow_html=True)
                    d2.markdown(stat_card("chart", "Execution Time", f"{dj['time_ms']:.4f} ms", f"{comp['speedup']:.1f}× faster" if comp['faster'] == "Dijkstra" else "", "green" if comp['faster'] == "Dijkstra" else "ink", small=True), unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f"- **Intersections Settled:** `{dj['work_units']}` of {net.node_count}")
                    st.markdown(f"- **Relaxations Evaluated:** `{dj['relaxations']}`")
                    st.markdown(f"- **Peak Memory:** `{dj['memory_kb']:.1f} KB`")
                    st.markdown(f"- **Time Complexity:** `{dj['time_complexity']}`")
                    st.markdown(f"- **Negative Edge Support:** `{dj['supports_negative']}`")
                    st.markdown(f"- **Negative Cycle Detection:** `{dj['detects_cycles']}`")

                with col_bf:
                    st.markdown("#### 🔄 Bellman-Ford Algorithm")
                    st.markdown(route_chips(bf["path"], "violet", "Selected Route"), unsafe_allow_html=True)
                    st.write("")
                    b1, b2 = st.columns(2)
                    b1.markdown(stat_card("cost", "Total Cost", fmt(bf["cost"]), "optimal units", "violet"), unsafe_allow_html=True)
                    b2.markdown(stat_card("chart", "Execution Time", f"{bf['time_ms']:.4f} ms", f"{comp['speedup']:.1f}× faster" if comp['faster'] == "Bellman-Ford" else "", "green" if comp['faster'] == "Bellman-Ford" else "ink", small=True), unsafe_allow_html=True)
                    st.write("")
                    st.markdown(f"- **Passes over all roads:** `{bf['work_units']}` (max {net.node_count - 1})")
                    st.markdown(f"- **Relaxations Evaluated:** `{bf['relaxations']}`")
                    st.markdown(f"- **Peak Memory:** `{bf['memory_kb']:.1f} KB`")
                    st.markdown(f"- **Time Complexity:** `{bf['time_complexity']}`")
                    st.markdown(f"- **Negative Edge Support:** `{bf['supports_negative']}`")
                    st.markdown(f"- **Negative Cycle Detection:** `{bf['detects_cycles']}`")

                st.write("")
                st.markdown("#### Detailed Trade-Off Comparison")
                table([
                    {"Feature": "Algorithmic Paradigm", "Dijkstra": "Greedy (locally optimal choices)", "Bellman-Ford": "Dynamic Programming (repeated relaxation)"},
                    {"Feature": "Core Data Structure", "Dijkstra": "Min-Priority Queue (Binary Heap)", "Bellman-Ford": "Edge list / Array passes"},
                    {"Feature": "Time Complexity", "Dijkstra": "O((V + E) log V)", "Bellman-Ford": "O(V · E)"},
                    {"Feature": "Space Complexity", "Dijkstra": "O(V)", "Bellman-Ford": "O(V)"},
                    {"Feature": "Edge Weight Requirement", "Dijkstra": "Non-negative only (costs ≥ 0)", "Bellman-Ford": "Any weights (handles negative edges)"},
                    {"Feature": "Negative Cycle Detection", "Dijkstra": "Cannot detect (fails or gives wrong result)", "Bellman-Ford": "Detects negative cycles in pass V"},
                    {"Feature": "Smart City Suitability", "Dijkstra": "Live GPS navigation, real-time routing", "Bellman-Ford": "Offline traffic analysis, toll discount models"}
                ])
    with t[1]:
        show = df.copy()
        show["Time (ms)"] = show["Time (ms)"].map(lambda x: f"{x:.4f}")
        show["Peak memory (KB)"] = show["Peak memory (KB)"].map(lambda x: f"{x:.1f}")
        show["Result"] = df.apply(describe, axis=1)
        table(show[["Intersections", "Roads", "Algorithm", "Time (ms)", "Peak memory (KB)", "Result"]])
        st.markdown("Execution time of all algorithms (ms)")
        st.line_chart(df.pivot(index="Intersections", columns="Algorithm", values="Time (ms)"))
        table(check.replace({True: "✓ same", False: "✗ different"}))
    with t[2]:
        pair_tab(df, "BFS", "DFS")
    with t[3]:
        pair_tab(df, "Dijkstra", "Bellman-Ford")
    with t[4]:
        pair_tab(df, "Prim", "Kruskal")
    with t[5]:
        if net.node_count < 2:
            st.info("Add at least two intersections to compare algorithms on your own network.")
        else:
            st.caption("Runs all six algorithms on the network currently loaded in the app.")
            src, dst = pick_pair("cmp", net.nodes)
            if st.button("Run on my network"):
                out = benchmark.run_all(net, src, dst, min_seconds=0.03)
                out["Result"] = [describe(r) for _, r in out.iterrows()]
                out["Time (ms)"] = out["Time (ms)"].map(lambda x: f"{x:.4f}")
                out["Peak memory (KB)"] = out["Peak memory (KB)"].map(lambda x: f"{x:.1f}")
                table(out[["Algorithm", "Time (ms)", "Peak memory (KB)", "Result"]])
                st.caption("A small network is so tiny that all times are extremely small and close together.")
    with t[6]:
        st.markdown("**Where Dijkstra fails and Bellman-Ford does not.** One-way roads, where road C → B has a "
                    "cost of −3 (think of a toll refund or a bus-lane bonus).")
        adj = {"A": {"B": 4, "C": 5}, "B": {"D": 2}, "C": {"B": -3}, "D": {}}
        dj, bf = dijkstra(adj, "A")["dist"], bellman_ford(adj, "A")["dist"]
        table([{"From A to": n, "Dijkstra says": fmt(dj[n]), "Bellman-Ford says": fmt(bf[n]),
                "Correct?": "Dijkstra wrong" if dj[n] != bf[n] else "Both right"} for n in adj])
        st.caption("Dijkstra locks B at 4 before it ever looks at C, so it never finds A → C → B = 2.")
        cyc = {"A": {"B": 1}, "B": {"C": 1}, "C": {"B": -3}}
        st.markdown("**Negative cycle** (B → C → B costs 1 + (−3) = −2 every lap):")
        st.write("Bellman-Ford reports negative cycle: **" + str(bellman_ford(cyc, "A")["negative_cycle"]) + "**")


# ==========================================================================
# Page: Network Builder
# ==========================================================================
def page_builder():
    net = st.session_state["city"]
    page_header("Network Builder", "Create your own city: add intersections and roads, edit costs, or import a CSV.",
                [(f"{net.node_count} intersections", "blue"), (f"{net.edge_count} roads", "blue")])
    t = st.tabs(["Add intersection", "Add road", "Edit or remove", "Import / export"])

    with t[0]:
        with st.form("form_add_node", clear_on_submit=True):
            name = st.text_input("Intersection name", placeholder="e.g. Stadium")
            auto = st.checkbox("Place it automatically on the map", value=True)
            x, y = st.columns(2)
            px = x.slider("Map position X (used if not automatic)", 0.0, 10.0, 5.0, 0.1)
            py = y.slider("Map position Y (used if not automatic)", 0.0, 10.0, 5.0, 0.1)
            if st.form_submit_button("Add intersection"):
                try:
                    net.add_intersection(name, None if auto else (px, py))
                    st.success(f"Added intersection '{name.strip()}'. Now connect it with a road.")
                except ValueError as err:
                    st.error(str(err))
    with t[1]:
        if net.node_count < 2:
            st.info("Add at least two intersections first.")
        else:
            with st.form("form_add_road", clear_on_submit=False):
                a, b, w = st.columns([2, 2, 1])
                u = a.selectbox("From", net.nodes, key="sel_bd_from")
                v = b.selectbox("To", net.nodes, key="sel_bd_to", index=1)
                cost = w.number_input("Travel cost", min_value=0.5, value=5.0, step=1.0)
                if st.form_submit_button("Add road"):
                    try:
                        new = net.add_road(u, v, cost)
                        st.success(f"{'Added' if new else 'Updated'} road {u} — {v} with cost {fmt(cost)}.")
                    except ValueError as err:
                        st.error(str(err))
    with t[2]:
        if net.edge_count:
            with st.form("form_edit_road"):
                keys = [road_key(u, v) for u, v, _ in net.edges()]
                road = st.selectbox("Road", keys, format_func=lambda k: road_label(net, k), key="sel_bd_edit")
                new_cost = st.number_input("New normal cost", min_value=0.5, value=5.0, step=1.0)
                c1, c2 = st.columns(2)
                update = c1.form_submit_button("Update cost")
                delete = c2.form_submit_button("Delete road")
                if update:
                    net.add_road(road[0], road[1], new_cost)
                    st.success("Cost updated.")
                if delete:
                    net.remove_road(*road)
                    reset_selectors()
                    st.rerun()
        else:
            st.info("There are no roads to edit yet.")
        if net.node_count:
            with st.form("form_del_node"):
                victim = st.selectbox("Intersection to delete (its roads are deleted too)", net.nodes, key="sel_bd_del")
                if st.form_submit_button("Delete intersection"):
                    net.remove_intersection(victim)
                    reset_selectors()
                    st.rerun()
    with t[3]:
        st.download_button("Download roads as CSV", net.to_csv(), "road_network.csv", "text/csv")
        up = st.file_uploader("Load a network from CSV (columns: source, target, weight)", type=["csv"])
        if up is not None:
            try:
                data = pd.read_csv(up)
                table(data.head(15))
                if st.button("Use this network"):
                    replace_network(RoadNetwork.from_edge_table(data))
                    st.rerun()
            except Exception as err:      # bad file -> friendly message
                st.error(f"Could not read that file: {err}")
        c1, c2 = st.columns(2)
        if c1.button("Load sample city"):
            replace_network(build_sample_city())
            st.rerun()
        if c2.button("Start with an empty network"):
            replace_network(RoadNetwork())
            st.rerun()

    st.markdown("#### Current network")
    show_map(draw_network(net, title="Road network"))


# ==========================================================================
# Page: Graph Data  (adjacency list / matrix)
# ==========================================================================
def page_graph_data():
    net = st.session_state["city"]
    cong = active_congestion()
    page_header("Graph Data", "The same road network, stored two ways. Both update automatically when you change the network.",
                [("Adjacency list", "blue"), ("Adjacency matrix", "violet")])
    if not require(net, nodes=1):
        return
    live = st.checkbox("Show live traffic costs", value=False, disabled=not cong, key="sel_gd_live")
    shown = net.with_weights(cong) if (live and cong) else net

    t1, t2, t3 = st.tabs(["Adjacency list", "Adjacency matrix", "Which one to use?"])
    with t1:
        st.caption("For every intersection: its neighbours and the cost of each road.")
        cols = st.columns(3)
        for i, (node, nbs) in enumerate(shown.adjacency_list().items()):
            cols[i % 3].markdown(adjacency_card(node, nbs), unsafe_allow_html=True)
    with t2:
        st.caption("Row = from, column = to. The number is the road cost; · means no direct road.")
        matrix = shown.adjacency_matrix()
        st.dataframe(matrix.style.background_gradient(cmap="Blues", vmin=0, vmax=max(float(matrix.values.max()), 1) * 1.6)
                     .format(lambda v: "·" if v == 0 else f"{v:g}"))
        st.download_button("Download matrix as CSV", matrix.to_csv(), "adjacency_matrix.csv", "text/csv")
    with t3:
        table([{"Aspect": "Memory", "Adjacency list": "O(V + E)", "Adjacency matrix": "O(V²)"},
               {"Aspect": "Is there a road A—B?", "Adjacency list": "O(degree of A)", "Adjacency matrix": "O(1)"},
               {"Aspect": "List all neighbours of A", "Adjacency list": "O(degree of A)", "Adjacency matrix": "O(V)"},
               {"Aspect": "Best for", "Adjacency list": "Sparse graphs (city maps: few roads per junction)",
                "Adjacency matrix": "Dense graphs, quick lookups"},
               {"Aspect": "Used in this project", "Adjacency list": "All algorithms", "Adjacency matrix": "Display and export"}])
        density = net.edge_count / max(net.node_count * (net.node_count - 1) / 2, 1)
        st.info(f"Your network has {net.edge_count} of the {int(net.node_count * (net.node_count - 1) / 2)} possible roads "
                f"({density:.0%}), which is why the list is the natural choice.")


# ==========================================================================
# Page: Viva Guide & About  (College Presentation & Examination)
# ==========================================================================
def page_viva_guide():
    page_header("Viva Preparation & Smart City Guide",
                "Complete project documentation, graph theory fundamentals, algorithm explanations, "
                "and question-answer cheat sheet designed for BCA final-year presentation and viva voce.",
                [("BCA Final Year", "blue"), ("6 Hand-Written Algorithms", "green"), ("Viva Ready", "violet")])

    t1, t2, t3 = st.tabs(["10 Core Viva Questions & Answers", "Master Algorithm Cheat Sheet", "System Architecture & Theory"])

    with t1:
        st.markdown("### Essential Viva Questions & Model Answers for College Defense")

        st.markdown(viva_card(
            "1. What real-world problem does this project solve?",
            "<p>Urban traffic congestion causes huge delays, fuel wastage, and elevated carbon emissions. "
            "This project models a smart city's road network as a mathematical weighted graph to dynamically compute lowest-cost travel routes, "
            "simulate traffic slowdowns and bottlenecks, compute optimal detours and detour savings, evaluate network connectivity, "
            "and plan cost-effective road infrastructure using Minimum Spanning Trees (MST).</p>",
            "PROBLEM CONTEXT"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "2. How is a city represented as a mathematical graph?",
            "<p>A city road network is modeled as an <b>undirected weighted graph G = (V, E, W)</b> where:</p>"
            "<ul>"
            "<li><b>Vertices / Nodes (V):</b> Major intersections, traffic junctions, and landmarks (Airport, Railway Station, Mall, City Center).</li>"
            "<li><b>Edges (E):</b> Two-way roads connecting pairs of intersections.</li>"
            "<li><b>Weights (W):</b> Travel cost (distance or travel time in minutes). Weights are strictly positive in real road networks (w > 0).</li>"
            "</ul>"
            "<p>In our implementation, the graph is stored as an <b>Adjacency List</b> using a Python dictionary of dictionaries for O(V + E) memory efficiency.</p>",
            "GRAPH THEORY"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "3. How does Dijkstra's Algorithm work and why can't it handle negative weights?",
            "<p><b>How it works:</b> Dijkstra is a <b>greedy</b> algorithm that finds the shortest path from a source to all other nodes. "
            "It maintains a min-priority queue (binary heap) of unsettled vertices ordered by tentative distance. In each step, it extracts "
            "the vertex u with the minimum tentative distance, locks/settles it, and relaxes all outgoing edges: "
            "<code>if dist[u] + cost &lt; dist[v] then dist[v] = dist[u] + cost</code>.</p>"
            "<p><b>Why non-negative only?</b> Dijkstra assumes that adding another edge to a path can never decrease its total length. "
            "Once a vertex is settled, its distance is considered final. If a negative edge existed later in the graph, it could provide a cheaper "
            "path to an already settled vertex, which Dijkstra would fail to discover, producing incorrect results.</p>"
            "<p><b>Time Complexity:</b> O((V + E) log V) with a binary heap.</p>",
            "DIJKSTRA ALGORITHM"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "4. How does Bellman-Ford work and how does it detect negative cycles?",
            "<p><b>How it works:</b> Bellman-Ford is based on <b>Dynamic Programming</b> and iterative edge relaxation. "
            "In any simple path with V vertices, there are at most V - 1 edges. Therefore, Bellman-Ford relaxes <b>all edges</b> in the graph "
            "V - 1 times. After k passes, all shortest paths using at most k edges are guaranteed to be correct.</p>"
            "<p><b>Negative Cycle Detection:</b> On the V-th pass, it scans all edges one more time. In a graph without negative cycles, "
            "no distance can improve after V - 1 passes. If any edge can still be relaxed (<code>dist[u] + cost &lt; dist[v]</code>), "
            "it mathematically proves the existence of a <b>negative cycle</b> where trip cost decreases infinitely.</p>"
            "<p><b>Time Complexity:</b> O(V · E).</p>",
            "BELLMAN-FORD"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "5. Why did you implement BOTH Dijkstra and Bellman-Ford in this project?",
            "<p>Because they represent the classic trade-off between <b>computational efficiency</b> and <b>flexibility</b>:</p>"
            "<ul>"
            "<li><b>Dijkstra is fast (O((V+E) log V)):</b> Ideal for live, real-time GPS navigation under standard positive travel times.</li>"
            "<li><b>Bellman-Ford is flexible (O(VE)):</b> Used in our <b>Traffic Analysis module</b> because it makes no assumptions about edge weights. "
            "It supports what-if adjustments (such as toll refunds or high-occupancy bonuses that reduce relative cost) and explicitly reports negative cycles rather than crashing or looping indefinitely. "
            "Its pass-by-pass structure is also ideal for step-by-step visual demonstration.</li>"
            "</ul>",
            "ALGORITHM COMPARISON"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "6. What does the Traffic & Congestion Simulation do and how is detour saving computed?",
            "<p>The simulation models real-world traffic jams by dynamically increasing road weights (e.g., multiplier or new cost) without modifying the original base network (using <code>net.with_weights()</code>). "
            "It re-evaluates the optimal route and calculates:</p>"
            "<ul>"
            "<li><b>Extra Travel Cost:</b> Δ Cost = Cost_after - Cost_before.</li>"
            "<li><b>Stay Cost:</b> The travel cost if the vehicle foolishly stayed on the original route despite the traffic jam.</li>"
            "<li><b>Detour Saving:</b> Detour Saving = Stay Cost - Cost_after. If the algorithm finds a detour, this value shows how many travel units the smart system saved the driver!</li>"
            "<li><b>Network Impact:</b> Evaluates all pairs of intersections to determine city-wide trip degradation and the worst-hit route.</li>"
            "</ul>",
            "TRAFFIC ANALYSIS"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "7. What does a Minimum Spanning Tree (MST) represent in city planning?",
            "<p>An MST is a subset of edges that connects <b>every vertex</b> in the graph with the <b>minimum total edge weight</b> and <b>no cycles</b>. "
            "In a connected graph with V vertices, an MST always has exactly V - 1 edges.</p>"
            "<p><b>Smart City Applications:</b></p>"
            "<ul>"
            "<li>Laying underground fiber optic internet backbones between all city hubs at minimum trenching cost.</li>"
            "<li>Designing municipal water pipeline or power grid distribution networks with zero redundant loops.</li>"
            "<li>Designing the foundational skeleton for new road or light-rail transit systems before adding redundancy lines.</li>"
            "</ul>"
            "<p>We implemented both <b>Prim's Algorithm</b> (vertex-based greedy with a heap, O(E log V)) and <b>Kruskal's Algorithm</b> (edge-based greedy using Union-Find, O(E log E)).</p>",
            "INFRASTRUCTURE MST"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "8. What is the difference between BFS and DFS in a city network?",
            "<p>Both visit every reachable intersection in O(V + E) time, but their search strategies differ:</p>"
            "<ul>"
            "<li><b>Breadth-First Search (BFS):</b> Uses a <b>FIFO Queue</b> to explore in concentric rings (all immediate neighbors first). "
            "In an unweighted graph, BFS guarantees finding the path with the <b>fewest road segments / hops</b>. Ideal for emergency broadcasts or nearest police dispatch by junctions.</li>"
            "<li><b>Depth-First Search (DFS):</b> Uses a <b>LIFO Stack</b> to explore as deeply as possible down a corridor before backtracking. "
            "Ideal for cycle detection, exploring dead-ends, topological sorting, and structural connectivity checks.</li>"
            "</ul>",
            "CONNECTIVITY BFS/DFS"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "9. How did you conduct the empirical benchmarking and what do the numbers prove?",
            "<p>Our benchmarking module (<code>benchmark.py</code>) conducts <b>real, automated experiments</b> on random connected networks of 10, 25, 50, and 100 intersections using fixed random seeds for reproducibility.</p>"
            "<p>To ensure high statistical precision, each algorithm is executed repeatedly for at least 0.03 seconds and timed using Python's high-resolution <code>time.perf_counter()</code>. Peak extra RAM is measured with <code>tracemalloc</code>. "
            "Crucially, teaching traces are disabled (<code>trace=False</code>) during benchmarks so pure algorithmic execution is measured.</p>"
            "<p>The empirical results perfectly confirm theoretical time complexities: Dijkstra scales far better than Bellman-Ford as V grows (O(V log V) vs O(V^2)), and Kruskal and Prim produce identical MST costs.</p>",
            "BENCHMARKING"
        ), unsafe_allow_html=True)

        st.markdown(viva_card(
            "10. What are the key conclusions and future extensions of this system?",
            "<p><b>Conclusions:</b> The project demonstrates that graph algorithms are fundamental to urban computing. "
            "Combining greedy routing (Dijkstra), dynamic programming (Bellman-Ford), graph traversals (BFS/DFS), and spanning tree optimization (Prim/Kruskal) provides a complete toolkit for smart transit management.</p>"
            "<p><b>Future Scope:</b> Real-time IoT sensor telemetry integration, one-way directed road networks, A* heuristic routing with GPS coordinates, and historical time-of-day congestion prediction using machine learning.</p>",
            "PROJECT SUMMARY"
        ), unsafe_allow_html=True)

    with t2:
        st.markdown("### Master Algorithm Reference Sheet (All 6 Hand-Written Algorithms)")
        table([
            {"Algorithm": "Dijkstra", "Type / Paradigm": "Greedy", "Data Structure": "Min-Heap (Priority Queue)", "Time Complexity": "O((V + E) log V)", "Space Complexity": "O(V)", "Key Requirement": "Non-negative edge weights (w ≥ 0)", "Smart City Application": "Live turn-by-turn navigation"},
            {"Algorithm": "Bellman-Ford", "Type / Paradigm": "Dynamic Programming", "Data Structure": "Edge list / Array", "Time Complexity": "O(V · E)", "Space Complexity": "O(V)", "Key Requirement": "No negative cycles (detects them)", "Smart City Application": "Traffic what-if simulation & toll analysis"},
            {"Algorithm": "Breadth-First Search (BFS)", "Type / Paradigm": "Graph Traversal", "Data Structure": "FIFO Queue", "Time Complexity": "O(V + E)", "Space Complexity": "O(V)", "Key Requirement": "Unweighted or unit cost", "Smart City Application": "Fewest-hop routing, flood-fill alerts"},
            {"Algorithm": "Depth-First Search (DFS)", "Type / Paradigm": "Graph Traversal", "Data Structure": "LIFO Stack (Explicit)", "Time Complexity": "O(V + E)", "Space Complexity": "O(V)", "Key Requirement": "Graph adjacency list", "Smart City Application": "Cycle detection & corridor exploration"},
            {"Algorithm": "Prim's Algorithm", "Type / Paradigm": "Greedy (Vertex-based)", "Data Structure": "Min-Heap", "Time Complexity": "O(E log V)", "Space Complexity": "O(V)", "Key Requirement": "Connected graph (or covers 1 component)", "Smart City Application": "Utility networks expanding from city hub"},
            {"Algorithm": "Kruskal's Algorithm", "Type / Paradigm": "Greedy (Edge-based)", "Data Structure": "Sorting + Union-Find", "Time Complexity": "O(E log E)", "Space Complexity": "O(V)", "Key Requirement": "Disjoint-Set (Path compression)", "Smart City Application": "Regional fiber & pipeline planning"}
        ])

    with t3:
        st.markdown("### System Architecture & Engineering Principles")
        st.markdown(
            "1. **Decoupled Architecture:** Algorithm modules (`route_planner.py`, `traffic_analysis.py`, `connectivity_module.py`, `mst_planner.py`, `benchmark.py`) "
            "contain **zero Streamlit code**. They operate on standard Python dictionaries and can be run in CLI, scripts, or unit tests independently.\n"
            "2. **Zero Third-Party Routing Dependency:** All 6 algorithms were written **from scratch by hand**. NetworkX is utilized strictly in unit tests for cross-validation and for force-directed graph spring layouts.\n"
            "3. **State Management:** Session state preserves active city road changes, live traffic weights, and planned routes across multiple pages seamlessly.\n"
            "4. **Defensive Error Handling:** The system validates input nodes, checks for self-loops, handles disconnected components, guards against negative cycles, and prevents crashes on identical origin/destination queries."
        )


# ==========================================================================
# Main
# ==========================================================================
init_state()
PAGE_FUNCTIONS = {
    "Dashboard": page_dashboard,
    "Route Planner": page_route_planner,
    "Traffic Analysis": page_traffic,
    "Connectivity": page_connectivity,
    "Infrastructure Planning": page_infrastructure,
    "Algorithm Comparison": page_comparison,
    "Network Builder": page_builder,
    "Graph Data": page_graph_data,
    "Viva Guide & About": page_viva_guide,
}
PAGE_FUNCTIONS[sidebar()]()

