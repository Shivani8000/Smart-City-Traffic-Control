"""
visuals.py
==========
Draws the road network as a "transit map": thick rounded roads, station-style
intersections, colour-coded routes and congestion.  Uses matplotlib only.

draw_network() is the one function every page uses; the keyword arguments switch
on the different overlays (route, congestion, traversal numbers, MST ...).
"""
import sys
import textwrap

import matplotlib

if "ipykernel" not in sys.modules:        # in a Jupyter notebook keep the inline backend
    matplotlib.use("Agg")                 # otherwise: no pop-up windows; Streamlit shows the image
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.lines import Line2D

from graph_model import road_key

COLORS = {
    "ink":    "#12233B",
    "paper":  "#F3F5F7",
    "road":   "#C3CCD8",
    "faint":  "#E3E8EE",
    "blue":   "#1D6FE0",
    "green":  "#1E9E6A",
    "amber":  "#E8A200",
    "red":    "#D8392B",
    "teal":   "#0E9AA7",
    "violet": "#7B4FD0",
    "magenta": "#C2358C",
}
LEVEL_COLORS = {"Free flow": COLORS["green"], "Moderate": COLORS["amber"], "Heavy": COLORS["red"]}


def fmt(x):
    return f"{x:g}"


def _level(ratio):
    return "Heavy" if ratio >= 2.0 else "Moderate" if ratio >= 1.25 else "Free flow"


def _text_on(fill):
    """White text on dark fills, ink text on light fills."""
    r, g, b = (int(fill[i:i + 2], 16) for i in (1, 3, 5))
    return "white" if (0.299 * r + 0.587 * g + 0.114 * b) < 150 else COLORS["ink"]


def draw_network(net, *, route=None, highlight_edges=None, highlight_color=None,
                 congestion=None, badges=None, node_fill=None, start=None, end=None,
                 dim_others=False, title=None, legend=None, figsize=(8.4, 5.6)):
    """
    route            list of intersections -> drawn as a thick coloured line
    highlight_edges  list of (u, v) roads to emphasise (traversal tree, MST ...)
    congestion       {road_key: ratio}  -> roads coloured green / amber / red
    badges           {node: text} written inside the intersection (visit order ...)
    node_fill        {node: colour} background colour of intersections
    start, end       intersections marked in green (S) / ink (E)
    dim_others       fade every road that is not highlighted
    """
    highlight_color = highlight_color or COLORS["blue"]
    congestion = congestion or {}
    badges = dict(badges or {})
    node_fill = dict(node_fill or {})

    route_edges = {road_key(a, b) for a, b in zip(route or [], (route or [])[1:])}
    marked = route_edges | {road_key(u, v) for u, v in (highlight_edges or [])}

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("white")
    bottom = 0.09 if legend else 0.01
    ax.set_position([0.01, bottom, 0.98, 0.93 - bottom])
    ax.axis("off")

    if not net.nodes:
        ax.text(0.5, 0.5, "The network is empty - add intersections first",
                ha="center", va="center", color=COLORS["ink"], transform=ax.transAxes)
        return fig

    pos = net.pos
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 1.3, max(xs) + 1.3)
    ax.set_ylim(min(ys) - 1.1, max(ys) + 1.0)

    # ---- roads --------------------------------------------------------------
    for u, v, w in net.edges():
        key = road_key(u, v)
        (x1, y1), (x2, y2) = pos[u], pos[v]
        is_marked = key in marked
        is_congested = key in congestion
        faded = dim_others and marked and not is_marked

        if faded:
            colour, width, label_edge = COLORS["faint"], 2.4, None
        elif is_marked:
            colour, width, label_edge = highlight_color, 6.5, highlight_color
        elif is_congested:
            colour = LEVEL_COLORS[_level(congestion[key])]
            width, label_edge = 6.5, colour
        else:
            colour, width, label_edge = COLORS["road"], 4.6, COLORS["road"]

        if is_marked and is_congested and not faded:      # congestion shown as a halo
            halo = LEVEL_COLORS[_level(congestion[key])]
            ax.plot([x1, x2], [y1, y2], color=halo, lw=width + 11, zorder=1,
                    solid_capstyle="round")
        ax.plot([x1, x2], [y1, y2], color="white", lw=width + 3, zorder=1.5,
                solid_capstyle="round")
        ax.plot([x1, x2], [y1, y2], color=colour, lw=width, zorder=2,
                solid_capstyle="round")

        if label_edge:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, fmt(w), ha="center", va="center",
                    fontsize=8, fontweight="bold", color=COLORS["ink"], zorder=4,
                    bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=label_edge, lw=1.3))

    # ---- intersections ------------------------------------------------------
    if start is not None:
        node_fill.setdefault(start, COLORS["green"])
        badges.setdefault(start, "S")
    if end is not None:
        node_fill.setdefault(end, COLORS["ink"])
        badges.setdefault(end, "E")

    for node, (x, y) in pos.items():
        fill = node_fill.get(node, "#FFFFFF")
        ax.scatter([x], [y], s=640, facecolor=fill, edgecolor=COLORS["ink"],
                   linewidths=2.6, zorder=5)
        if node in badges:
            ax.text(x, y, badges[node], ha="center", va="center", fontsize=9.5,
                    fontweight="bold", color=_text_on(fill), zorder=6)
        ax.annotate(textwrap.fill(node, 12), (x, y), xytext=(0, -19),
                    textcoords="offset points", ha="center", va="top", fontsize=8.5,
                    fontweight="semibold", color=COLORS["ink"], zorder=7,
                    path_effects=[patheffects.withStroke(linewidth=3, foreground="white")])

    if title:
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold",
                     color=COLORS["ink"], pad=6)
    if legend:
        handles = [Line2D([0], [0], color=c, lw=5, solid_capstyle="round", label=l)
                   for l, c in legend]
        fig.legend(handles=handles, loc="lower center", ncol=len(handles), fontsize=8.5,
                   frameon=False)
    return fig
