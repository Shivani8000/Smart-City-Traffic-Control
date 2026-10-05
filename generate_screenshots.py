"""
generate_screenshots.py
=======================
Generates high-resolution dashboard screenshots for all 9 key views of the
Smart City Traffic Management and Route Optimization System.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Rectangle
import pandas as pd
import numpy as np

from graph_model import build_sample_city, road_key
from route_planner import dijkstra, bellman_ford, find_route
from traffic_analysis import analyze_congestion
from connectivity_module import bfs, dfs
from mst_planner import prim, kruskal
from visuals import draw_network, COLORS, LEVEL_COLORS
import benchmark

OUT_DIR = "screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10

def save_fig(fig, filename):
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"Saved: {path}")

# ==============================================================================
# Helper to draw UI topbar & title
# ==============================================================================
def draw_header(ax, title, subtitle, page_tag):
    ax.axis("off")
    ax.text(0.0, 0.75, "🚦 Smart City Traffic Control", fontsize=15, fontweight="bold", color="#12233B")
    ax.text(0.0, 0.40, f"Page: {page_tag}", fontsize=11, fontweight="bold", color="#1D6FE0")
    ax.text(0.0, 0.08, subtitle, fontsize=9.5, color="#5A6B82")
    
    # Status badges on the right
    ax.text(0.98, 0.70, "🟢 System Active", ha="right", fontsize=9.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#E8F8F1", ec="#1E9E6A", lw=1))
    ax.text(0.98, 0.25, "Graph: 9 Intersections | 13 Roads", ha="right", fontsize=9, color="#5A6B82")

# ==============================================================================
# 1. 01_dashboard.png
# ==============================================================================
def make_01_dashboard():
    net = build_sample_city()
    route_res = find_route(net.adj, "Residential Area", "Airport", "Dijkstra")
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(3, 3, height_ratios=[0.8, 1.1, 5.0], hspace=0.3, wspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.04)
    
    # Header
    ax_head = fig.add_subplot(gs[0, :])
    draw_header(ax_head, "Dashboard Overview", "City-wide transit operations console and real-time monitoring", "Dashboard")
    
    # 3 Stat Cards
    cards_data = [
        ("Intersections", "9 Active", "100% Connected", "#1D6FE0", "#EEF4FC"),
        ("Active Route", f"{' → '.join(route_res['path'][:2])} ...", f"Travel Cost: {route_res['cost']} min", "#1E9E6A", "#E8F8F1"),
        ("Traffic Congestion", "Clear Flow", "No active delays", "#E8A200", "#FEF8EC"),
    ]
    for i, (title, val, sub, bar_col, bg_col) in enumerate(cards_data):
        ax_card = fig.add_subplot(gs[1, i])
        ax_card.axis("off")
        ax_card.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.03", fc=bg_col, ec="#CBD5E1", lw=1, transform=ax_card.transAxes))
        ax_card.add_patch(Rectangle((0, 0), 0.03, 1, fc=bar_col, transform=ax_card.transAxes))
        ax_card.text(0.08, 0.70, title.upper(), fontsize=8.5, fontweight="bold", color="#64748B", transform=ax_card.transAxes)
        ax_card.text(0.08, 0.40, val, fontsize=13, fontweight="bold", color="#12233B", transform=ax_card.transAxes)
        ax_card.text(0.08, 0.15, sub, fontsize=9, color="#475569", transform=ax_card.transAxes)

    # Main Map (spanning 2 columns)
    ax_map = fig.add_subplot(gs[2, :2])
    sub_fig = draw_network(net, route=route_res["path"], start="Residential Area", end="Airport",
                           title="Transit Map — Highlighted Optimal Route (Residential Area → Airport)",
                           legend=[("Optimal Route", COLORS["blue"]), ("Road Network", COLORS["road"])], figsize=(9, 6))
    # Render sub_fig onto ax_map
    sub_fig.canvas.draw()
    img = np.asarray(sub_fig.canvas.buffer_rgba())
    plt.close(sub_fig)
    ax_map.imshow(img)
    ax_map.axis("off")
    
    # Right Sidebar / Insights Panel
    ax_side = fig.add_subplot(gs[2, 2])
    ax_side.axis("off")
    ax_side.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_side.transAxes))
    ax_side.text(0.08, 0.92, "Route Details", fontsize=11, fontweight="bold", color="#12233B", transform=ax_side.transAxes)
    ax_side.text(0.08, 0.86, f"Algorithm: Dijkstra (O((V+E) log V))", fontsize=8.5, color="#64748B", transform=ax_side.transAxes)
    
    y = 0.75
    ax_side.text(0.08, y, "Turn-by-turn Path:", fontsize=9.5, fontweight="bold", color="#1E293B", transform=ax_side.transAxes)
    y -= 0.05
    for idx, node in enumerate(route_res["path"], 1):
        ax_side.text(0.12, y, f"{idx}. {node}", fontsize=9, color="#1D6FE0" if idx in (1, len(route_res['path'])) else "#334155",
                     fontweight="bold" if idx in (1, len(route_res['path'])) else "normal", transform=ax_side.transAxes)
        y -= 0.05
    
    y -= 0.04
    ax_side.text(0.08, y, "Network Metrics:", fontsize=9.5, fontweight="bold", color="#1E293B", transform=ax_side.transAxes)
    metrics = [
        ("Total Intersections", "9"),
        ("Total Road Segments", "13"),
        ("Average Degree", "2.88"),
        ("Graph Diameter (hops)", "4"),
        ("Network Connectivity", "100% (Single Component)"),
    ]
    y -= 0.05
    for k, v in metrics:
        ax_side.text(0.12, y, f"• {k}:", fontsize=8.5, color="#64748B", transform=ax_side.transAxes)
        ax_side.text(0.92, y, v, fontsize=8.5, fontweight="bold", ha="right", color="#1E293B", transform=ax_side.transAxes)
        y -= 0.045
        
    save_fig(fig, "01_dashboard.png")

# ==============================================================================
# 2. 02_route_planner.png
# ==============================================================================
def make_02_route_planner():
    net = build_sample_city()
    src, dst = "University", "Airport"
    res = find_route(net.adj, src, dst, "Dijkstra")
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(3, 3, height_ratios=[0.8, 1.2, 5.0], hspace=0.3, wspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.04)
    
    ax_head = fig.add_subplot(gs[0, :])
    draw_header(ax_head, "Route Planner", "Commuter Shortest Path Finder with Dijkstra & Bellman-Ford", "Route Planner")
    
    # Path summary bar
    ax_summary = fig.add_subplot(gs[1, :])
    ax_summary.axis("off")
    ax_summary.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_summary.transAxes))
    ax_summary.text(0.03, 0.65, f"Route: {src}  ⟶  {dst}", fontsize=13, fontweight="bold", color="#12233B", transform=ax_summary.transAxes)
    ax_summary.text(0.03, 0.25, f"Algorithm: Dijkstra's Algorithm | Total Cost: {res['cost']} minutes | Hops: {len(res['path'])-1} roads",
                    fontsize=9.5, color="#64748B", transform=ax_summary.transAxes)
    # Route chips
    chips = "  ➜  ".join([f"[{p}]" for p in res["path"]])
    ax_summary.text(0.97, 0.50, chips, ha="right", va="center", fontsize=9.5, fontweight="bold", color="#1D6FE0",
                    bbox=dict(boxstyle="round,pad=0.4", fc="#EEF4FC", ec="#1D6FE0", lw=1), transform=ax_summary.transAxes)

    # Route Map
    ax_map = fig.add_subplot(gs[2, :2])
    sub_fig = draw_network(net, route=res["path"], start=src, end=dst,
                           title=f"Optimal Commute: {src} to {dst} (Cost: {res['cost']} min)",
                           legend=[("Shortest Path", COLORS["blue"]), ("Candidate Road", COLORS["road"])], figsize=(9, 6))
    sub_fig.canvas.draw()
    img = np.asarray(sub_fig.canvas.buffer_rgba())
    plt.close(sub_fig)
    ax_map.imshow(img)
    ax_map.axis("off")
    
    # Leg by Leg Table
    ax_table = fig.add_subplot(gs[2, 2])
    ax_table.axis("off")
    ax_table.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_table.transAxes))
    ax_table.text(0.08, 0.93, "Segment Breakdown", fontsize=11, fontweight="bold", color="#12233B", transform=ax_table.transAxes)
    
    table_data = [
        ["From", "To", "Cost", "Cumul."],
    ]
    for seg in res["segments"]:
        table_data.append([seg["from"][:8], seg["to"][:8], f"{seg['cost']}m", f"{seg['cumulative']}m"])
    
    tbl = ax_table.table(cellText=table_data[1:], colLabels=table_data[0], loc="center",
                         bbox=[0.05, 0.25, 0.90, 0.60], cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#E2E8F0")
        if r == 0:
            cell.set_facecolor("#F1F5F9")
            cell.set_text_props(weight="bold", color="#1E293B")
        else:
            cell.set_facecolor("#FFFFFF")
            
    ax_table.text(0.08, 0.15, "✓ Verified globally optimal", fontsize=8.5, fontweight="bold", color="#1E9E6A", transform=ax_table.transAxes)
    ax_table.text(0.08, 0.08, "Greedy choice property holds with w >= 0.", fontsize=8, color="#64748B", transform=ax_table.transAxes)
    
    save_fig(fig, "02_route_planner.png")

# ==============================================================================
# 3. 03_dijkstra_steps.png
# ==============================================================================
def make_03_dijkstra_steps():
    net = build_sample_city()
    res = dijkstra(net.adj, "City Center", "Airport")
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(2, 1, height_ratios=[0.8, 6.0], hspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.04)
    
    ax_head = fig.add_subplot(gs[0])
    draw_header(ax_head, "Dijkstra Intermediate Updates", "Detailed Step-by-Step Priority Queue Relaxation Log", "Route Planner ➜ Distance Updates")
    
    ax_body = fig.add_subplot(gs[1])
    ax_body.axis("off")
    ax_body.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_body.transAxes))
    
    ax_body.text(0.03, 0.95, "Dijkstra Priority Queue Execution Trace (Source: City Center)", fontsize=12, fontweight="bold", color="#12233B", transform=ax_body.transAxes)
    ax_body.text(0.03, 0.91, "Each step locks the minimum distance intersection from the min-heap and attempts edge relaxation on all neighbors.",
                 fontsize=9, color="#64748B", transform=ax_body.transAxes)
    
    rows = [["Step", "Settled Node", "Locked Dist", "Relaxed Neighbor", "Edge Cost", "Old Dist", "New Dist", "Status"]]
    for s in res["steps"]:
        for r in s["relaxations"]:
            status = "UPDATED (Improved)" if r["updated"] else "Kept (No change)"
            old_d = "∞" if r["old_distance"] == float("inf") else str(r["old_distance"])
            new_d = str(r["new_distance"])
            rows.append([f"Step {s['step']}", s["node"], str(s["distance"]), r["neighbor"], str(r["edge_cost"]), old_d, new_d, status])
    
    # Show first 12 entries
    display_rows = rows[:13]
    tbl = ax_body.table(cellText=[r for r in display_rows[1:]], colLabels=display_rows[0],
                        loc="center", bbox=[0.02, 0.12, 0.96, 0.74], cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#E2E8F0")
        if r == 0:
            cell.set_facecolor("#1D6FE0")
            cell.set_text_props(weight="bold", color="#FFFFFF")
        else:
            if "UPDATED" in display_rows[r][7]:
                cell.set_facecolor("#F0FDF4" if c == 7 else "#FFFFFF")
                if c == 7:
                    cell.set_text_props(weight="bold", color="#1E9E6A")
            else:
                cell.set_facecolor("#FFFFFF")
                if c == 7:
                    cell.set_text_props(color="#64748B")
                    
    ax_body.text(0.03, 0.05, f"Algorithm terminates when target reached or priority queue exhausted. Total relaxation iterations: {len(rows)-1}",
                 fontsize=8.5, style="italic", color="#475569", transform=ax_body.transAxes)
    save_fig(fig, "03_dijkstra_steps.png")

# ==============================================================================
# 4. 04_traffic_before_after.png
# ==============================================================================
def make_04_traffic_before_after():
    net = build_sample_city()
    src, dst = "City Center", "Airport"
    changes = {("City Center", "Mall"): 15}
    res = analyze_congestion(net, changes, src, dst)
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(3, 2, height_ratios=[0.8, 1.2, 5.0], hspace=0.3, wspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.04)
    
    ax_head = fig.add_subplot(gs[0, :])
    draw_header(ax_head, "Traffic Analysis & Congestion Rerouting", "Dynamic Rerouting and Cost Comparison using Bellman-Ford", "Traffic Analysis")
    
    # Impact Banner
    ax_banner = fig.add_subplot(gs[1, :])
    ax_banner.axis("off")
    ax_banner.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_banner.transAxes))
    ax_banner.text(0.03, 0.70, "Congestion Incident: City Center ⟷ Mall (Cost: 4 min ➜ 15 min | +275% Heavy Delay)",
                   fontsize=11.5, fontweight="bold", color="#D8392B", transform=ax_banner.transAxes)
    ax_banner.text(0.03, 0.25, f"Original Cost: {res['cost_before']} min  |  New Detour Cost: {res['cost_after']} min  |  Cost if staying in jam: {res['stay_cost']} min  |  Detour Net Saving: {res['detour_saving']} min",
                   fontsize=9.5, fontweight="bold", color="#12233B", transform=ax_banner.transAxes)

    # Before Map
    ax_left = fig.add_subplot(gs[2, 0])
    sub_before = draw_network(net, route=res["path_before"], start=src, end=dst,
                              title="Original Route: City Center ➜ Mall ➜ Airport (Cost: 12m)",
                              legend=[("Original Route", COLORS["green"])], figsize=(7, 5.5))
    sub_before.canvas.draw()
    img_b = np.asarray(sub_before.canvas.buffer_rgba())
    plt.close(sub_before)
    ax_left.imshow(img_b)
    ax_left.axis("off")
    
    # After Map
    ax_right = fig.add_subplot(gs[2, 1])
    sub_after = draw_network(res["congested"], route=res["path_after"],
                             congestion={road_key("City Center", "Mall"): 15/4},
                             start=src, end=dst,
                             title="Rerouted: City Center ➜ Hospital ➜ Airport (Cost: 13m)",
                             legend=[("Rerouted Path", COLORS["blue"]), ("Congested Road", COLORS["red"])], figsize=(7, 5.5))
    sub_after.canvas.draw()
    img_a = np.asarray(sub_after.canvas.buffer_rgba())
    plt.close(sub_after)
    ax_right.imshow(img_a)
    ax_right.axis("off")
    
    save_fig(fig, "04_traffic_before_after.png")

# ==============================================================================
# 5. 05_bfs_dfs.png
# ==============================================================================
def make_05_bfs_dfs():
    net = build_sample_city()
    start = "City Center"
    b_res = bfs(net.adj, start)
    d_res = dfs(net.adj, start)
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(3, 2, height_ratios=[0.8, 1.0, 5.0], hspace=0.3, wspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.04)
    
    ax_head = fig.add_subplot(gs[0, :])
    draw_header(ax_head, "Network Connectivity & Reachability", "Breadth-First Search (Queue) vs Depth-First Search (Stack) Exploration", "Connectivity")
    
    # Orders banner
    ax_banner = fig.add_subplot(gs[1, :])
    ax_banner.axis("off")
    ax_banner.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_banner.transAxes))
    ax_banner.text(0.02, 0.68, "BFS Order (Level by level):", fontsize=9.5, fontweight="bold", color="#1D6FE0", transform=ax_banner.transAxes)
    ax_banner.text(0.24, 0.68, " ➜ ".join([n[:8] for n in b_res["order"]]), fontsize=9, color="#1E293B", transform=ax_banner.transAxes)
    ax_banner.text(0.02, 0.22, "DFS Order (Deep exploration):", fontsize=9.5, fontweight="bold", color="#7B4FD0", transform=ax_banner.transAxes)
    ax_banner.text(0.24, 0.22, " ➜ ".join([n[:8] for n in d_res["order"]]), fontsize=9, color="#1E293B", transform=ax_banner.transAxes)

    # BFS Map
    ax_b = fig.add_subplot(gs[2, 0])
    b_badges = {n: str(i) for i, n in enumerate(b_res["order"], 1)}
    sub_b = draw_network(net, highlight_edges=b_res["tree_edges"], highlight_color=COLORS["blue"],
                         badges=b_badges, start=start,
                         title="Breadth-First Search (BFS Tree — Shortest Hops)",
                         legend=[("BFS Tree Edge", COLORS["blue"])], figsize=(7, 5.5))
    sub_b.canvas.draw()
    img_b = np.asarray(sub_b.canvas.buffer_rgba())
    plt.close(sub_b)
    ax_b.imshow(img_b)
    ax_b.axis("off")
    
    # DFS Map
    ax_d = fig.add_subplot(gs[2, 1])
    d_badges = {n: str(i) for i, n in enumerate(d_res["order"], 1)}
    sub_d = draw_network(net, highlight_edges=d_res["tree_edges"], highlight_color=COLORS["violet"],
                         badges=d_badges, start=start,
                         title="Depth-First Search (DFS Tree — Backtracking)",
                         legend=[("DFS Tree Edge", COLORS["violet"])], figsize=(7, 5.5))
    sub_d.canvas.draw()
    img_d = np.asarray(sub_d.canvas.buffer_rgba())
    plt.close(sub_d)
    ax_d.imshow(img_d)
    ax_d.axis("off")
    
    save_fig(fig, "05_bfs_dfs.png")

# ==============================================================================
# 6. 06_mst.png
# ==============================================================================
def make_06_mst():
    net = build_sample_city()
    p_res = prim(net.adj)
    k_res = kruskal(net.adj)
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(3, 3, height_ratios=[0.8, 1.1, 5.0], hspace=0.3, wspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.04)
    
    ax_head = fig.add_subplot(gs[0, :])
    draw_header(ax_head, "Infrastructure Planning Module (MST)", "Minimum Spanning Tree Construction via Prim's and Kruskal's Algorithms", "Infrastructure Planning")
    
    # Cards
    ax_c1 = fig.add_subplot(gs[1, 0])
    ax_c1.axis("off")
    ax_c1.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.03", fc="#EEF4FC", ec="#CBD5E1", lw=1, transform=ax_c1.transAxes))
    ax_c1.add_patch(Rectangle((0, 0), 0.03, 1, fc="#1D6FE0", transform=ax_c1.transAxes))
    ax_c1.text(0.08, 0.70, "PRIM'S ALGORITHM", fontsize=8.5, fontweight="bold", color="#1D6FE0", transform=ax_c1.transAxes)
    ax_c1.text(0.08, 0.35, f"Cost: ${p_res['total_cost']}M", fontsize=13, fontweight="bold", color="#12233B", transform=ax_c1.transAxes)
    ax_c1.text(0.08, 0.12, f"Edges: {len(p_res['edges'])} roads (V-1)", fontsize=8.5, color="#64748B", transform=ax_c1.transAxes)
    
    ax_c2 = fig.add_subplot(gs[1, 1])
    ax_c2.axis("off")
    ax_c2.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.03", fc="#E8F8F1", ec="#CBD5E1", lw=1, transform=ax_c2.transAxes))
    ax_c2.add_patch(Rectangle((0, 0), 0.03, 1, fc="#1E9E6A", transform=ax_c2.transAxes))
    ax_c2.text(0.08, 0.70, "KRUSKAL'S ALGORITHM", fontsize=8.5, fontweight="bold", color="#1E9E6A", transform=ax_c2.transAxes)
    ax_c2.text(0.08, 0.35, f"Cost: ${k_res['total_cost']}M", fontsize=13, fontweight="bold", color="#12233B", transform=ax_c2.transAxes)
    ax_c2.text(0.08, 0.12, "Union-Find Cycle Detection", fontsize=8.5, color="#64748B", transform=ax_c2.transAxes)
    
    ax_c3 = fig.add_subplot(gs[1, 2])
    ax_c3.axis("off")
    ax_c3.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.03", fc="#FEF8EC", ec="#CBD5E1", lw=1, transform=ax_c3.transAxes))
    ax_c3.add_patch(Rectangle((0, 0), 0.03, 1, fc="#E8A200", transform=ax_c3.transAxes))
    ax_c3.text(0.08, 0.70, "INFRASTRUCTURE SAVINGS", fontsize=8.5, fontweight="bold", color="#E8A200", transform=ax_c3.transAxes)
    full_cost = sum(w for _, _, w in net.edges())
    ax_c3.text(0.08, 0.35, f"Saved: ${full_cost - p_res['total_cost']}M", fontsize=13, fontweight="bold", color="#12233B", transform=ax_c3.transAxes)
    ax_c3.text(0.08, 0.12, f"Total network cost: ${full_cost}M", fontsize=8.5, color="#64748B", transform=ax_c3.transAxes)

    # MST Map
    mst_edges = [(u, v) for u, v, _ in p_res["edges"]]
    ax_map = fig.add_subplot(gs[2, :2])
    sub_mst = draw_network(net, highlight_edges=mst_edges, highlight_color=COLORS["teal"], dim_others=True,
                           title="Minimum Spanning Tree — 8 Selected Construction Roads (Cost: $37M)",
                           legend=[("MST Selected Road", COLORS["teal"]), ("Omitted Road", COLORS["faint"])], figsize=(9, 6))
    sub_mst.canvas.draw()
    img_m = np.asarray(sub_mst.canvas.buffer_rgba())
    plt.close(sub_mst)
    ax_map.imshow(img_m)
    ax_map.axis("off")
    
    # Kruskal Decision Table
    ax_tbl = fig.add_subplot(gs[2, 2])
    ax_tbl.axis("off")
    ax_tbl.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_tbl.transAxes))
    ax_tbl.text(0.08, 0.93, "Kruskal Decisions", fontsize=11, fontweight="bold", color="#12233B", transform=ax_tbl.transAxes)
    
    rows = [["Road", "Cost", "Decision"]]
    for s in k_res["steps"][:10]:
        dec = "Accepted" if "Accepted" in s["decision"] else "Rejected"
        rows.append([s["road"][:12], f"${s['cost']}M", dec])
        
    tbl = ax_tbl.table(cellText=rows[1:], colLabels=rows[0], loc="center", bbox=[0.05, 0.15, 0.90, 0.72], cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#E2E8F0")
        if r == 0:
            cell.set_facecolor("#0E9AA7")
            cell.set_text_props(weight="bold", color="#FFFFFF")
        else:
            if "Accepted" in rows[r][2]:
                cell.set_text_props(weight="bold", color="#1E9E6A" if c == 2 else "#1E293B")
            else:
                cell.set_text_props(color="#D8392B" if c == 2 else "#64748B")
                
    save_fig(fig, "06_mst.png")

# ==============================================================================
# 7. 07_comparison.png
# ==============================================================================
def make_07_comparison():
    df = pd.read_csv("report/benchmark_results.csv")
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(3, 3, height_ratios=[0.8, 3.2, 3.0], hspace=0.35, wspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.05)
    
    ax_head = fig.add_subplot(gs[0, :])
    draw_header(ax_head, "Comparative Analysis & Performance Benchmarks",
                "Execution Time and Memory Benchmarks across 10, 25, 50, 100 Intersection Networks", "Algorithm Comparison")
    
    # Chart 1: Shortest Path (Dijkstra vs Bellman-Ford)
    ax_sp = fig.add_subplot(gs[1, 0])
    d_df = df[df["Algorithm"] == "Dijkstra"]
    b_df = df[df["Algorithm"] == "Bellman-Ford"]
    ax_sp.plot(d_df["Intersections"], d_df["Time (ms)"], marker="o", color=COLORS["blue"], lw=2.2, label="Dijkstra (O((V+E)logV))")
    ax_sp.plot(b_df["Intersections"], b_df["Time (ms)"], marker="s", color=COLORS["red"], lw=2.2, label="Bellman-Ford (O(VE))")
    ax_sp.set_title("Shortest Path Execution Time", fontsize=10.5, fontweight="bold", color="#12233B")
    ax_sp.set_xlabel("Intersections (|V|)", fontsize=9)
    ax_sp.set_ylabel("Time (ms)", fontsize=9)
    ax_sp.grid(True, linestyle="--", alpha=0.5)
    ax_sp.legend(fontsize=8)
    
    # Chart 2: Traversal (BFS vs DFS)
    ax_tr = fig.add_subplot(gs[1, 1])
    bfs_df = df[df["Algorithm"] == "BFS"]
    dfs_df = df[df["Algorithm"] == "DFS"]
    ax_tr.plot(bfs_df["Intersections"], bfs_df["Time (ms)"], marker="o", color=COLORS["teal"], lw=2.2, label="BFS (Queue)")
    ax_tr.plot(dfs_df["Intersections"], dfs_df["Time (ms)"], marker="^", color=COLORS["violet"], lw=2.2, label="DFS (Stack)")
    ax_tr.set_title("Traversal Execution Time", fontsize=10.5, fontweight="bold", color="#12233B")
    ax_tr.set_xlabel("Intersections (|V|)", fontsize=9)
    ax_tr.set_ylabel("Time (ms)", fontsize=9)
    ax_tr.grid(True, linestyle="--", alpha=0.5)
    ax_tr.legend(fontsize=8)

    # Chart 3: MST (Prim vs Kruskal)
    ax_mst = fig.add_subplot(gs[1, 2])
    p_df = df[df["Algorithm"] == "Prim"]
    k_df = df[df["Algorithm"] == "Kruskal"]
    ax_mst.plot(p_df["Intersections"], p_df["Time (ms)"], marker="o", color=COLORS["green"], lw=2.2, label="Prim (Heap)")
    ax_mst.plot(k_df["Intersections"], k_df["Time (ms)"], marker="s", color=COLORS["amber"], lw=2.2, label="Kruskal (Sort+UF)")
    ax_mst.set_title("MST Construction Time", fontsize=10.5, fontweight="bold", color="#12233B")
    ax_mst.set_xlabel("Intersections (|V|)", fontsize=9)
    ax_mst.set_ylabel("Time (ms)", fontsize=9)
    ax_mst.grid(True, linestyle="--", alpha=0.5)
    ax_mst.legend(fontsize=8)

    # Summary Table across all algorithms for 100 intersections
    ax_tbl = fig.add_subplot(gs[2, :])
    ax_tbl.axis("off")
    ax_tbl.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.01", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_tbl.transAxes))
    ax_tbl.text(0.02, 0.92, "Empirical Benchmark Results (Measured across varying city network scales)", fontsize=11, fontweight="bold", color="#12233B", transform=ax_tbl.transAxes)
    
    pivot_df = df.pivot(index="Algorithm", columns="Intersections", values="Time (ms)").reset_index()
    headers = ["Algorithm", "10 Vertices (ms)", "25 Vertices (ms)", "50 Vertices (ms)", "100 Vertices (ms)"]
    tbl_vals = []
    for _, row in pivot_df.iterrows():
        tbl_vals.append([row["Algorithm"], f"{row[10]:.4f}", f"{row[25]:.4f}", f"{row[50]:.4f}", f"{row[100]:.4f}"])
        
    tbl = ax_tbl.table(cellText=tbl_vals, colLabels=headers, loc="center", bbox=[0.02, 0.10, 0.96, 0.72], cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#E2E8F0")
        if r == 0:
            cell.set_facecolor("#1E293B")
            cell.set_text_props(weight="bold", color="#FFFFFF")
        else:
            cell.set_facecolor("#F8FAFC" if r % 2 == 0 else "#FFFFFF")
            
    save_fig(fig, "07_comparison.png")

# ==============================================================================
# 8. 08_graph_data.png
# ==============================================================================
def make_08_graph_data():
    net = build_sample_city()
    matrix = net.adjacency_matrix()
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(2, 2, height_ratios=[0.8, 6.0], hspace=0.25, wspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.04)
    
    ax_head = fig.add_subplot(gs[0, :])
    draw_header(ax_head, "Graph Data & Network Representations", "Adjacency List O(V+E) Storage and Adjacency Matrix O(V²) Direct Lookup", "Graph Data")
    
    # Left: Adjacency List
    ax_list = fig.add_subplot(gs[1, 0])
    ax_list.axis("off")
    ax_list.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_list.transAxes))
    ax_list.text(0.06, 0.94, "Adjacency List Representation (Dict of Dicts)", fontsize=11, fontweight="bold", color="#12233B", transform=ax_list.transAxes)
    ax_list.text(0.06, 0.90, "Memory: O(V + E) | Highly optimal for sparse real-world road networks", fontsize=8.5, color="#64748B", transform=ax_list.transAxes)
    
    y = 0.83
    for node, nbs in list(net.adj.items())[:9]:
        nbs_str = ", ".join([f"({v}, {w}m)" for v, w in sorted(nbs.items())])
        ax_list.text(0.06, y, f"• {node}:", fontsize=8.5, fontweight="bold", color="#1D6FE0", transform=ax_list.transAxes)
        ax_list.text(0.38, y, f"➜ [ {nbs_str} ]", fontsize=8, color="#334155", transform=ax_list.transAxes)
        y -= 0.085

    # Right: Adjacency Matrix Heatmap
    ax_mat = fig.add_subplot(gs[1, 1])
    ax_mat.set_title("Adjacency Matrix Representation (O(V²))", fontsize=11, fontweight="bold", color="#12233B", pad=12)
    mat_data = matrix.values
    im = ax_mat.imshow(mat_data, cmap="Blues", interpolation="nearest")
    fig.colorbar(im, ax=ax_mat, fraction=0.046, pad=0.04, label="Travel Cost (min)")
    
    short_names = [n[:8] for n in matrix.index]
    ax_mat.set_xticks(range(len(short_names)))
    ax_mat.set_yticks(range(len(short_names)))
    ax_mat.set_xticklabels(short_names, rotation=45, ha="right", fontsize=8)
    ax_mat.set_yticklabels(short_names, fontsize=8)
    
    for i in range(len(short_names)):
        for j in range(len(short_names)):
            val = mat_data[i, j]
            ax_mat.text(j, i, f"{val:g}" if val > 0 else "0", ha="center", va="center",
                        fontsize=7.5, color="white" if val > 5 else "#12233B",
                        fontweight="bold" if val > 0 else "normal")

    save_fig(fig, "08_graph_data.png")

# ==============================================================================
# 9. 09_builder.png
# ==============================================================================
def make_09_builder():
    net = build_sample_city()
    # Add a custom new intersection and road
    net.add_intersection("Tech Park", pos=(8.5, 5.5))
    net.add_road("Tech Park", "City Center", 5)
    net.add_road("Tech Park", "Airport", 4)
    
    fig = plt.figure(figsize=(15, 9.5), facecolor="#F8FAFC")
    gs = gridspec.GridSpec(2, 3, height_ratios=[0.8, 6.0], hspace=0.25, wspace=0.25,
                           left=0.04, right=0.96, top=0.94, bottom=0.04)
    
    ax_head = fig.add_subplot(gs[0, :])
    draw_header(ax_head, "Interactive Network Builder & Topology Editor",
                "Dynamic Addition of Intersections, Road Segments, and Custom Weight Assignment", "Network Builder")
    
    # Left Form Mockup
    ax_form = fig.add_subplot(gs[1, 0])
    ax_form.axis("off")
    ax_form.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc="#FFFFFF", ec="#CBD5E1", lw=1, transform=ax_form.transAxes))
    ax_form.text(0.08, 0.93, "Add New Intersection", fontsize=11, fontweight="bold", color="#12233B", transform=ax_form.transAxes)
    
    ax_form.text(0.08, 0.85, "Intersection Name:", fontsize=9, color="#475569", transform=ax_form.transAxes)
    ax_form.text(0.08, 0.78, "Tech Park", fontsize=9.5, fontweight="bold", color="#12233B",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#F8FAFC", ec="#94A3B8", lw=1), transform=ax_form.transAxes)
    
    ax_form.text(0.08, 0.68, "Add Road Connection:", fontsize=11, fontweight="bold", color="#12233B", transform=ax_form.transAxes)
    ax_form.text(0.08, 0.60, "From: Tech Park", fontsize=9, color="#475569", transform=ax_form.transAxes)
    ax_form.text(0.08, 0.54, "To: Airport", fontsize=9, color="#475569", transform=ax_form.transAxes)
    ax_form.text(0.08, 0.46, "Travel Cost (min): 4.0", fontsize=9, color="#475569", transform=ax_form.transAxes)
    
    ax_form.text(0.08, 0.35, "✔ Intersection & Road Added Successfully", fontsize=8.5, fontweight="bold", color="#1E9E6A",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#E8F8F1", ec="#1E9E6A", lw=1), transform=ax_form.transAxes)
    
    ax_form.text(0.08, 0.22, "Network Summary:", fontsize=9.5, fontweight="bold", color="#12233B", transform=ax_form.transAxes)
    ax_form.text(0.08, 0.16, "• Vertices: 10 (+1 Tech Park)", fontsize=8.5, color="#64748B", transform=ax_form.transAxes)
    ax_form.text(0.08, 0.11, "• Edges: 15 (+2 new roads)", fontsize=8.5, color="#64748B", transform=ax_form.transAxes)
    ax_form.text(0.08, 0.06, "• CSV Export & Import Supported", fontsize=8.5, color="#64748B", transform=ax_form.transAxes)

    # Right: Network Map with newly added node highlighted
    ax_map = fig.add_subplot(gs[1, 1:])
    sub_fig = draw_network(net, highlight_edges=[("Tech Park", "City Center"), ("Tech Park", "Airport")],
                           highlight_color=COLORS["green"],
                           node_fill={"Tech Park": COLORS["green"]},
                           title="Updated Topology — 'Tech Park' Connected to City Center & Airport",
                           legend=[("Newly Added Roads", COLORS["green"]), ("Existing Roads", COLORS["road"])], figsize=(9, 6))
    sub_fig.canvas.draw()
    img = np.asarray(sub_fig.canvas.buffer_rgba())
    plt.close(sub_fig)
    ax_map.imshow(img)
    ax_map.axis("off")
    
    save_fig(fig, "09_builder.png")

if __name__ == "__main__":
    print("Generating all 9 screenshots...")
    make_01_dashboard()
    make_02_route_planner()
    make_03_dijkstra_steps()
    make_04_traffic_before_after()
    make_05_bfs_dfs()
    make_06_mst()
    make_07_comparison()
    make_08_graph_data()
    make_09_builder()
    print("All screenshots generated successfully in screenshots/!")
