"""
ui.py
=====
Look-and-feel for the dashboard: CSS, stat cards, route chips, page headers.

Design idea: an operations console styled like a transit authority.
  * navy sidebar, pale-grey workspace, white cards
  * signal colours (green / amber / red) are used ONLY to mean traffic status
  * each stat card has a coloured left edge that tells you its status at a glance
  * type: Overpass (inspired by highway signage) for headings, IBM Plex Sans for text
    (loaded from Google Fonts; falls back to system fonts when offline)
"""
import html

import streamlit as st

TONES = {
    "blue": "#1D6FE0", "green": "#1E9E6A", "amber": "#E8A200", "red": "#D8392B",
    "teal": "#0E9AA7", "violet": "#7B4FD0", "ink": "#12233B", "grey": "#8A97A8",
    "magenta": "#C2358C",
}

_SVG = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{}</svg>'
ICONS = {
    "junction": _SVG.format('<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8 7l3 9M16 7l-3 9M8.5 6h7"/>'),
    "road": _SVG.format('<path d="M8 3L5 21M16 3l3 18M12 4v3M12 10v4M12 17v3"/>'),
    "route": _SVG.format('<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h7a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7"/>'),
    "cost": _SVG.format('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    "alert": _SVG.format('<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/>'),
    "link": _SVG.format('<path d="M10 14a4 4 0 0 0 5.6 0l3-3a4 4 0 0 0-5.6-5.6l-1 1M14 10a4 4 0 0 0-5.6 0l-3 3a4 4 0 0 0 5.6 5.6l1-1"/>'),
    "check": _SVG.format('<path d="M4 12l5 5L20 6"/>'),
    "chart": _SVG.format('<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>'),
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Overpass:wght@600;700;800&display=swap');

:root{ --ink:#12233B; --muted:#5B6B80; --line:#DCE2EA; --paper:#F3F5F7; }

html, body, .stApp, [data-testid="stAppViewContainer"]{ font-family:'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif; color:var(--ink); }
h1,h2,h3,h4{ font-family:'Overpass','Segoe UI',sans-serif !important; letter-spacing:-0.01em; color:var(--ink); }
#MainMenu, footer{ visibility:hidden; }
header[data-testid="stHeader"]{ background:transparent; }
.block-container{ padding-top:1.4rem; padding-bottom:3rem; max-width:1280px; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"]{ background:#12233B; border-right:0; }
section[data-testid="stSidebar"] *{ color:#E6ECF4; }
section[data-testid="stSidebar"] hr{ border-color:rgba(255,255,255,.14); }
.brand{ display:flex; align-items:center; gap:.7rem; padding:.2rem 0 .9rem; }
.brand-mark{ width:38px; height:38px; border-radius:10px; background:#1D6FE0; display:flex; align-items:center; justify-content:center; color:#fff; }
.brand-name{ font-family:'Overpass',sans-serif; font-weight:800; font-size:1.05rem; line-height:1.1; }
.brand-sub{ font-size:.74rem; color:#9FB0C6 !important; }
section[data-testid="stSidebar"] div[role="radiogroup"]{ gap:.15rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] label{ padding:.55rem .8rem; border-radius:8px; width:100%; border-left:4px solid transparent; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{ background:rgba(255,255,255,.07); }
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child{ display:none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){ background:rgba(29,111,224,.28); border-left-color:#5AA2FF; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{ font-weight:600; color:#fff; }
section[data-testid="stSidebar"] .stButton button{ background:transparent; border:1px solid rgba(255,255,255,.35); color:#fff; }
section[data-testid="stSidebar"] .stButton button:hover{ border-color:#fff; background:rgba(255,255,255,.08); }
.side-note{ font-size:.78rem; color:#9FB0C6 !important; line-height:1.45; }

/* ---------- page header ---------- */
.hero{ background:#12233B; border-radius:12px; padding:1.25rem 1.5rem 1.2rem; margin-bottom:1.1rem; position:relative; overflow:hidden; }
.hero:before{ content:""; position:absolute; left:0; right:0; top:0; height:5px; background:linear-gradient(90deg,#1D6FE0 0 25%,#1E9E6A 25% 50%,#E8A200 50% 75%,#D8392B 75% 100%); }
.hero h1{ color:#fff !important; font-size:1.75rem; margin:.35rem 0 .2rem; padding:0; }
.hero p{ color:#B9C6D8; margin:0; max-width:70ch; font-size:.95rem; }
.hero-pills{ margin-top:.8rem; display:flex; gap:.5rem; flex-wrap:wrap; }
.pill{ display:inline-flex; align-items:center; gap:.4rem; padding:.22rem .7rem; border-radius:999px; font-size:.8rem; font-weight:600; background:rgba(255,255,255,.12); color:#fff; }
.pill:before{ content:""; width:8px; height:8px; border-radius:50%; background:var(--tone,#8A97A8); }

/* ---------- cards ---------- */
.stat{ background:#fff; border:1px solid var(--line); border-left:6px solid var(--tone,#1D6FE0); border-radius:10px; padding:.85rem 1rem .8rem; height:100%; }
.stat-top{ display:flex; justify-content:space-between; align-items:center; color:var(--muted); }
.stat-label{ font-size:.85rem; font-weight:500; }
.stat-icon{ color:var(--tone,#1D6FE0); display:flex; }
.stat-value{ font-family:'Overpass',sans-serif; font-weight:800; font-size:1.85rem; line-height:1.15; margin-top:.15rem; }
.stat-value.small{ font-size:1.25rem; }
.stat-sub{ font-size:.8rem; color:var(--muted); margin-top:.1rem; }

.panel{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:1rem 1.1rem; }
.panel h4{ margin:0 0 .5rem; font-size:1.02rem; }
.panel-label{ font-size:.85rem; color:var(--muted); margin-bottom:.35rem; font-weight:500; }

.chips{ display:flex; flex-wrap:wrap; align-items:center; gap:.35rem .4rem; }
.chip{ background:var(--tone,#1D6FE0); color:#fff; padding:.28rem .8rem; border-radius:999px; font-weight:600; font-size:.88rem; }
.chip.end{ box-shadow:0 0 0 3px rgba(18,35,59,.18); }
.arrow{ color:#8A97A8; font-weight:600; }

.adj-card{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:.7rem .9rem; margin-bottom:.8rem; }
.adj-card b{ font-family:'Overpass',sans-serif; font-size:1rem; }
.adj-card ul{ margin:.35rem 0 0; padding-left:1.1rem; color:var(--muted); font-size:.9rem; }
.adj-card li span{ color:var(--ink); font-weight:600; }

/* ---------- streamlit widgets ---------- */
.stTabs [data-baseweb="tab"]{ font-weight:600; }
[data-testid="stExpander"]{ border:1px solid var(--line); border-radius:10px; background:#fff; }
[data-testid="stForm"]{ border:1px solid var(--line); border-radius:10px; background:#fff; }
div[data-testid="stAlert"]{ border-radius:10px; }
.stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button{ border-radius:8px; font-weight:600; }

.callout{ background:#fff; border:1px solid var(--line); border-left:5px solid var(--tone,#1D6FE0); border-radius:10px; padding:.9rem 1.1rem; margin-bottom:.8rem; }
.callout h4{ margin:0 0 .3rem; font-size:1.05rem; color:var(--ink); }
.callout p{ margin:0; color:var(--muted); font-size:.9rem; line-height:1.5; }

.viva-card{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:1.1rem 1.25rem; margin-bottom:1rem; box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.viva-q{ font-family:'Overpass',sans-serif; font-weight:700; font-size:1.05rem; color:#12233B; margin-bottom:.45rem; display:flex; align-items:center; gap:.5rem; }
.viva-badge{ display:inline-block; font-size:.72rem; font-weight:700; text-transform:uppercase; padding:.15rem .5rem; border-radius:4px; background:rgba(29,111,224,0.12); color:#1D6FE0; letter-spacing:0.04em; }
.viva-a{ color:#3D4D60; font-size:.92rem; line-height:1.55; }

@media (max-width: 768px){
  .hero h1{ font-size:1.35rem; }
  .stat-value{ font-size:1.5rem; }
}
"""


def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def flat(markup):
    """Streamlit treats indented lines as code blocks - so we remove all indentation."""
    return "".join(line.strip() for line in markup.strip().splitlines())


def esc(text):
    return html.escape(str(text))


def fmt(x):
    if x is None:
        return "–"
    if x == float("inf"):
        return "∞"
    return f"{x:g}"


def page_header(title, subtitle, pills=None):
    pill_html = "".join(f'<span class="pill" style="--tone:{TONES.get(t, t)}">{esc(text)}</span>'
                        for text, t in (pills or []))
    st.markdown(flat(f'<div class="hero"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p>'
                     f'<div class="hero-pills">{pill_html}</div></div>'), unsafe_allow_html=True)


def stat_card(icon, label, value, sub="", tone="blue", small=False):
    size = " small" if small else ""
    return flat(f'<div class="stat" style="--tone:{TONES.get(tone, tone)}">'
                f'<div class="stat-top"><span class="stat-label">{esc(label)}</span>'
                f'<span class="stat-icon">{ICONS.get(icon, "")}</span></div>'
                f'<div class="stat-value{size}">{esc(value)}</div>'
                f'<div class="stat-sub">{esc(sub)}</div></div>')


def route_chips(path, tone="blue", label=None):
    if not path:
        body = '<span class="stat-sub">No route</span>'
    else:
        parts = []
        for i, node in enumerate(path):
            cls = "chip end" if i in (0, len(path) - 1) else "chip"
            parts.append(f'<span class="{cls}" style="--tone:{TONES.get(tone, tone)}">{esc(node)}</span>')
        body = '<span class="arrow">→</span>'.join(parts)
    head = f'<div class="panel-label">{esc(label)}</div>' if label else ""
    return flat(f'<div class="panel">{head}<div class="chips">{body}</div></div>')


def adjacency_card(node, neighbours):
    items = "".join(f"<li>{esc(n)}: <span>{fmt(w)}</span></li>" for n, w in neighbours) \
        or '<li>no roads yet</li>'
    return flat(f'<div class="adj-card"><b>{esc(node)}</b><ul>{items}</ul></div>')


def level_tone(level):
    return {"Clear": "green", "Free flow": "green", "Moderate": "amber", "Heavy": "red"}.get(level, "grey")


def callout_box(title, text, tone="blue"):
    return flat(f'<div class="callout" style="--tone:{TONES.get(tone, tone)}">'
                f'<h4>{esc(title)}</h4><p>{esc(text)}</p></div>')


def viva_card(question, answer_html, category="VIVA CONCEPT"):
    return flat(f'<div class="viva-card">'
                f'<div class="viva-q"><span class="viva-badge">{esc(category)}</span>{esc(question)}</div>'
                f'<div class="viva-a">{answer_html}</div></div>')
