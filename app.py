"""
UAV Search & Rescue - Geospatial Command Center
Real-world interactive mapping with folium + dark glass-morphic UI
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import math
import time

from uav_environment import UAVEnvironment, Node
from two_phase_cfqs import TwoPhaseApproach
from q_learning_ndts import QLearningNDTS
from improved_q_learning import ImprovedQLearningNDTS
from greedy_baseline import GreedySolver

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="UAV SAR Command Center",
    page_icon="\U0001F6F0",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CONSTANTS
# =============================================================================
THEATERS = {
    "Sierra Nevada, CA": (36.5785, -118.2923),
    "Rocky Mountains, CO": (39.7392, -105.9903),
    "Appalachian Trail, VA": (37.7833, -79.4310),
    "Grand Canyon, AZ": (36.1069, -112.1129),
    "Olympic Peninsula, WA": (47.8021, -123.7088),
}

KM_PER_UNIT = 0.1  # 1 abstract map unit = 100 m

ROUTE_COLORS = [
    "#00d4ff",  # Cyan
    "#ff3366",  # Pink-Red
    "#00ff88",  # Neon Green
    "#ffaa00",  # Amber
    "#aa55ff",  # Purple
    "#ff6633",  # Orange
    "#33ffcc",  # Teal
    "#ff33cc",  # Magenta
]

# =============================================================================
# CSS INJECTION - Dark Glass-Morphic Theme
# =============================================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* --- Global --- */
.stApp {
    background: linear-gradient(135deg,#0a0a1a 0%,#0d1117 50%,#0a0a1a 100%);
    color: #e0e0e0;
    font-family: 'Inter',sans-serif;
}
.stApp header {
    background: rgba(10,10,26,.85)!important;
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(0,212,255,.12);
}

/* --- Sidebar --- */
section[data-testid="stSidebar"] {
    background: rgba(13,17,23,.95)!important;
    border-right: 1px solid rgba(0,212,255,.10);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #00d4ff!important;
}

/* --- Glass metric cards --- */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(0,212,255,.12);
    border-radius: 12px;
    padding: 16px;
    backdrop-filter: blur(10px);
}
div[data-testid="stMetric"] label {
    color: #8899aa!important;
    font-weight: 500;
    letter-spacing: .5px;
    text-transform: uppercase;
    font-size: .72rem!important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #00d4ff!important;
    font-family: 'JetBrains Mono',monospace;
    font-weight: 600;
}
div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono',monospace;
}

/* --- Tabs --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,.02);
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #8899aa;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,212,255,.1)!important;
    color: #00d4ff!important;
    border-bottom-color: #00d4ff!important;
}

/* --- Expanders --- */
.streamlit-expanderHeader {
    background: rgba(255,255,255,.03)!important;
    border: 1px solid rgba(0,212,255,.08)!important;
    border-radius: 8px!important;
    color: #c0c8d0!important;
}

/* --- Buttons --- */
.stButton > button {
    background: linear-gradient(135deg,rgba(0,212,255,.15),rgba(0,212,255,.08));
    color: #00d4ff;
    border: 1px solid rgba(0,212,255,.3);
    border-radius: 8px;
    font-weight: 600;
    transition: all .3s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg,rgba(0,212,255,.3),rgba(0,212,255,.15));
    border-color: #00d4ff;
    box-shadow: 0 0 20px rgba(0,212,255,.2);
}

/* --- Headings --- */
h1 { color: #00d4ff!important; font-weight: 700; letter-spacing: -.5px; }
h2,h3 { color: #c0d0e0!important; font-weight: 600; }

/* --- Misc --- */
hr { border-color: rgba(0,212,255,.1)!important; }
.stSelectbox label,.stSlider label,.stNumberInput label {
    color: #8899aa!important; font-weight: 500;
}
.stDataFrame { border: 1px solid rgba(0,212,255,.08); border-radius: 8px; }

/* --- Custom legend bar --- */
.legend-bar {
    display: flex; justify-content: center; flex-wrap: wrap;
    gap: 20px; padding: 10px 16px;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(0,212,255,.08);
    border-radius: 10px;
    margin: 4px 0 12px;
}
.legend-item {
    display: flex; align-items: center; gap: 8px;
    font-size: .8rem; color: #8899aa; font-weight: 500;
}
.legend-dot {
    width: 10px; height: 10px;
    border-radius: 50%; display: inline-block;
}

/* --- Node Editor --- */
.stNumberInput input { font-family: 'JetBrains Mono', monospace !important; }
</style>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in **km** between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def xy_to_latlon(x: float, y: float, map_size: float, center: tuple) -> tuple:
    """Convert abstract X/Y grid coordinates to real-world (lat, lon)."""
    dx_km = (x - map_size / 2) * KM_PER_UNIT
    dy_km = (y - map_size / 2) * KM_PER_UNIT
    lat = center[0] + dy_km / 111.0
    lon = center[1] + dx_km / (111.0 * math.cos(math.radians(center[0])))
    return (lat, lon)


def latlon_to_xy(lat: float, lon: float, map_size: float, center: tuple) -> tuple:
    """Convert real-world (lat, lon) back to abstract X/Y grid coordinates."""
    dy_km = (lat - center[0]) * 111.0
    dx_km = (lon - center[1]) * 111.0 * math.cos(math.radians(center[0]))
    x = dx_km / KM_PER_UNIT + map_size / 2
    y = dy_km / KM_PER_UNIT + map_size / 2
    return (x, y)


def init_coords_from_env(env, map_size, center):
    """Populate session state with lat/lon for every node after environment generation."""
    for node in env.nodes:
        ll = xy_to_latlon(node.x, node.y, map_size, center)
        st.session_state[f"node_{node.id}_lat"] = round(ll[0], 6)
        st.session_state[f"node_{node.id}_lon"] = round(ll[1], 6)
    st.session_state["_coords_center"] = center
    st.session_state["_coords_map_size"] = map_size


def sync_env_from_coords(env, map_size, center):
    """Update environment node positions from session state lat/lon coordinates."""
    for node in env.nodes:
        lat_key = f"node_{node.id}_lat"
        lon_key = f"node_{node.id}_lon"
        if lat_key in st.session_state and lon_key in st.session_state:
            x, y = latlon_to_xy(
                st.session_state[lat_key], st.session_state[lon_key], map_size, center
            )
            node.x = x
            node.y = y
    env.distance_matrix = env._compute_distance_matrix()
    env.time_cost_matrix = env.distance_matrix.copy()
    env.battery_cost_matrix = env.distance_matrix.copy()


def get_survivor_meta(node, max_reward: float) -> dict:
    """Simulated survivor metadata from node properties."""
    rng = np.random.RandomState(seed=node.id * 137 + 7)
    pod = round(rng.uniform(0.30, 0.95), 2)
    if node.reward >= max_reward * 0.8:
        health, hcol = "CRITICAL", "#ff4444"
    elif node.reward >= max_reward * 0.5:
        health, hcol = "SERIOUS", "#ffaa00"
    else:
        health, hcol = "STABLE", "#00ff88"
    return {"pod": pod, "health": health, "color": hcol}


def route_distance_km(env, route, map_size, center) -> float:
    """Total route distance in km using Haversine formula."""
    total = 0.0
    for i in range(len(route) - 1):
        a, b = env.nodes[route[i]], env.nodes[route[i + 1]]
        la, lo = xy_to_latlon(a.x, a.y, map_size, center)
        lb, lob = xy_to_latlon(b.x, b.y, map_size, center)
        total += haversine(la, lo, lb, lob)
    return total


# =============================================================================
# FOLIUM MAP BUILDER
# =============================================================================

def build_command_map(env, routes, map_size, center):
    """Build the interactive geospatial command-center map."""
    depot_ll = xy_to_latlon(env.depot.x, env.depot.y, map_size, center)

    m = folium.Map(
        location=list(depot_ll),
        zoom_start=14,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # --- Inject pulsing animation CSS into the map ---
    m.get_root().html.add_child(
        folium.Element(
            """
    <style>
    @keyframes sar-pulse{
        0%{transform:scale(1);opacity:.85}
        70%{transform:scale(2.4);opacity:0}
        100%{transform:scale(2.4);opacity:0}
    }
    .sar-wrap{position:relative;width:30px;height:30px}
    .sar-ping{
        position:absolute;width:14px;height:14px;border-radius:50%;
        background:rgba(255,50,50,.4);
        top:50%;left:50%;transform:translate(-50%,-50%);
        animation:sar-pulse 2s ease-out infinite;pointer-events:none;
    }
    .sar-core{
        position:absolute;width:12px;height:12px;border-radius:50%;
        background:#ff3333;border:2px solid #fff;
        top:50%;left:50%;transform:translate(-50%,-50%);z-index:2;
    }
    </style>
    """
        )
    )

    # ---- Feature groups (toggleable layers) ----
    fg_depot = folium.FeatureGroup(name="Command Base", show=True)
    fg_extract = folium.FeatureGroup(name="Extraction Zone", show=True)
    fg_survivors = folium.FeatureGroup(name="Survivors", show=True)
    fg_charging = folium.FeatureGroup(name="Charging Stations", show=True)

    # ---- DEPOT ----
    depot_popup = f"""
    <div style="font-family:Inter,sans-serif;min-width:220px;background:#111827;
                color:#e0e0e0;padding:14px;border-radius:10px;
                border:1px solid rgba(0,212,255,.2);">
        <div style="font-size:1.1rem;font-weight:700;color:#00ff88;margin-bottom:6px;">
            &#9673; COMMAND BASE</div>
        <hr style="border-color:#1e293b;margin:6px 0;">
        <table style="width:100%;font-size:.85rem;color:#94a3b8;">
            <tr><td>Role</td>
                <td style="text-align:right;color:#e0e0e0;">UAV Launch &amp; Recovery</td></tr>
            <tr><td>Coords</td>
                <td style="text-align:right;font-family:monospace;color:#00d4ff;">
                {depot_ll[0]:.5f}, {depot_ll[1]:.5f}</td></tr>
        </table>
    </div>"""
    folium.Marker(
        location=list(depot_ll),
        icon=folium.Icon(color="green", icon="home", prefix="fa"),
        popup=folium.Popup(depot_popup, max_width=280),
        tooltip="COMMAND BASE (DEPOT)",
    ).add_to(fg_depot)

    # ---- EXTRACTION ZONE ----
    dest = env.destination
    ext_ll = list(xy_to_latlon(dest.x, dest.y, map_size, center))
    # Slight offset when co-located with depot so both markers are visible
    ext_ll[0] -= 0.0012
    ext_ll[1] += 0.0012

    folium.Circle(
        location=ext_ll,
        radius=120,
        color="#aa55ff",
        fill=True,
        fill_color="#aa55ff",
        fill_opacity=0.18,
        weight=2,
        dash_array="6",
        tooltip="EXTRACTION ZONE",
    ).add_to(fg_extract)

    ext_popup = f"""
    <div style="font-family:Inter,sans-serif;min-width:200px;background:#111827;
                color:#e0e0e0;padding:14px;border-radius:10px;
                border:1px solid rgba(170,85,255,.25);">
        <div style="font-size:1.1rem;font-weight:700;color:#aa55ff;margin-bottom:6px;">
            &#9733; EXTRACTION ZONE</div>
        <hr style="border-color:#1e293b;margin:6px 0;">
        <p style="font-size:.85rem;color:#94a3b8;margin:0;">
            Medevac &amp; Survivor Handoff<br>
            <span style="font-family:monospace;color:#aa55ff;">
            {ext_ll[0]:.5f}, {ext_ll[1]:.5f}</span></p>
    </div>"""
    folium.Marker(
        location=ext_ll,
        icon=folium.Icon(color="purple", icon="medkit", prefix="fa"),
        popup=folium.Popup(ext_popup, max_width=260),
        tooltip="EXTRACTION ZONE",
    ).add_to(fg_extract)

    # ---- SURVIVORS ----
    max_reward = max((n.reward for n in env.service_nodes), default=1)

    for node in env.service_nodes:
        ll = xy_to_latlon(node.x, node.y, map_size, center)
        meta = get_survivor_meta(node, max_reward)
        popup_html = f"""
        <div style="font-family:Inter,sans-serif;min-width:240px;background:#111827;
                    color:#e0e0e0;padding:14px;border-radius:10px;
                    border:1px solid rgba(255,51,51,.2);">
            <div style="font-size:1rem;font-weight:700;color:#ff4444;margin-bottom:4px;">
                &#9888; Survivor SRV-{node.id:03d}</div>
            <hr style="border-color:#1e293b;margin:6px 0;">
            <table style="width:100%;font-size:.82rem;color:#94a3b8;line-height:1.8;">
                <tr><td>Priority Score</td>
                    <td style="text-align:right;font-weight:700;color:#e0e0e0;">
                    {node.reward}</td></tr>
                <tr><td>Prob. of Detection</td>
                    <td style="text-align:right;font-weight:700;color:#00d4ff;">
                    {meta['pod']*100:.0f}%</td></tr>
                <tr><td>Health Status</td>
                    <td style="text-align:right;font-weight:700;color:{meta['color']};">
                    {meta['health']}</td></tr>
                <tr><td>Coordinates</td>
                    <td style="text-align:right;font-family:monospace;font-size:.78rem;
                        color:#64748b;">{ll[0]:.5f}, {ll[1]:.5f}</td></tr>
            </table>
        </div>"""
        icon_html = (
            '<div class="sar-wrap">'
            '<div class="sar-ping"></div>'
            '<div class="sar-core"></div>'
            "</div>"
        )
        folium.Marker(
            location=list(ll),
            icon=folium.DivIcon(html=icon_html, icon_size=(30, 30), icon_anchor=(15, 15)),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"SRV-{node.id:03d} | Prio: {node.reward} | {meta['health']}",
        ).add_to(fg_survivors)

    # ---- CHARGING STATIONS ----
    for station in env.charging_stations:
        ll = xy_to_latlon(station.x, station.y, map_size, center)
        cs_popup = f"""
        <div style="font-family:Inter,sans-serif;min-width:200px;background:#111827;
                    color:#e0e0e0;padding:14px;border-radius:10px;
                    border:1px solid rgba(255,170,0,.2);">
            <div style="font-size:1rem;font-weight:700;color:#ffaa00;margin-bottom:4px;">
                &#9889; Charging Station CS-{station.id:03d}</div>
            <hr style="border-color:#1e293b;margin:6px 0;">
            <table style="width:100%;font-size:.82rem;color:#94a3b8;">
                <tr><td>Type</td>
                    <td style="text-align:right;color:#e0e0e0;">Battery Recharge</td></tr>
                <tr><td>Capacity</td>
                    <td style="text-align:right;color:#ffaa00;">Full Charge</td></tr>
                <tr><td>Coords</td>
                    <td style="text-align:right;font-family:monospace;color:#64748b;">
                    {ll[0]:.5f}, {ll[1]:.5f}</td></tr>
            </table>
        </div>"""
        folium.Marker(
            location=list(ll),
            icon=folium.Icon(color="orange", icon="bolt", prefix="fa"),
            popup=folium.Popup(cs_popup, max_width=260),
            tooltip=f"Charging Station CS-{station.id:03d}",
        ).add_to(fg_charging)

    # ---- ROUTES ----
    if routes:
        for idx, route in enumerate(routes):
            if len(route) < 2:
                continue
            fg_route = folium.FeatureGroup(name=f"UAV-{idx + 1} Route", show=True)
            coords = [
                list(xy_to_latlon(env.nodes[nid].x, env.nodes[nid].y, map_size, center))
                for nid in route
            ]
            color = ROUTE_COLORS[idx % len(ROUTE_COLORS)]

            # Animated ant-path for the route
            AntPath(
                locations=coords,
                color=color,
                weight=4,
                opacity=0.85,
                dash_array=[12, 24],
                delay=800,
                tooltip=f"UAV-{idx + 1} Route ({len(route)} waypoints)",
            ).add_to(fg_route)

            # Small waypoint dots
            for step, nid in enumerate(route):
                wll = list(
                    xy_to_latlon(env.nodes[nid].x, env.nodes[nid].y, map_size, center)
                )
                folium.CircleMarker(
                    location=wll,
                    radius=4,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9,
                    weight=1,
                    tooltip=f"UAV-{idx + 1} Step {step}: Node {nid}",
                ).add_to(fg_route)

            fg_route.add_to(m)

    # Add all feature groups
    fg_depot.add_to(m)
    fg_extract.add_to(m)
    fg_survivors.add_to(m)
    fg_charging.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Fit map bounds to encompass all nodes
    all_lls = [
        list(xy_to_latlon(n.x, n.y, map_size, center)) for n in env.nodes
    ]
    all_lls.append(ext_ll)
    m.fit_bounds(all_lls, padding=[30, 30])

    return m


# =============================================================================
# EDITOR MAP BUILDER (interactive node placement)
# =============================================================================

def build_editor_map(env, map_size, center, selected_node_id=None):
    """Build interactive map for the Node Editor tab with highlighted selection."""
    depot_ll = xy_to_latlon(env.depot.x, env.depot.y, map_size, center)

    m = folium.Map(
        location=list(depot_ll),
        zoom_start=14,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Inject editor-specific CSS
    cursor_css = "cursor:crosshair!important;" if selected_node_id is not None else ""
    m.get_root().html.add_child(
        folium.Element(
            f"""
    <style>
    .leaflet-container {{ {cursor_css} }}
    @keyframes editor-pulse {{
        0% {{ box-shadow: 0 0 4px 2px rgba(255,255,0,.8); }}
        50% {{ box-shadow: 0 0 16px 8px rgba(255,255,0,.4); }}
        100% {{ box-shadow: 0 0 4px 2px rgba(255,255,0,.8); }}
    }}
    .editor-selected {{
        animation: editor-pulse 1.2s ease-in-out infinite;
        border-radius: 50%;
    }}
    </style>
    """
        )
    )

    for node in env.nodes:
        ll = list(xy_to_latlon(node.x, node.y, map_size, center))
        is_selected = node.id == selected_node_id
        sel_prefix = "\u25ba " if is_selected else ""

        if node.id == 0:  # depot
            icon = folium.Icon(
                color="red" if is_selected else "green", icon="home", prefix="fa"
            )
            label = "Command Base (Depot)"
        elif node.id == 1:  # extraction / destination
            icon = folium.Icon(
                color="red" if is_selected else "purple", icon="medkit", prefix="fa"
            )
            label = "Extraction Zone"
            if abs(node.x - env.depot.x) < 1 and abs(node.y - env.depot.y) < 1:
                ll[0] -= 0.0012
                ll[1] += 0.0012
        elif node.node_type == "charging":
            icon = folium.Icon(
                color="red" if is_selected else "orange", icon="bolt", prefix="fa"
            )
            label = f"Charging CS-{node.id:03d}"
        else:  # survivor / service
            if is_selected:
                dot = (
                    '<div class="editor-selected" style="width:14px;height:14px;'
                    "background:#ffe600;border-radius:50%;border:2px solid #fff;"
                    '"></div>'
                )
            else:
                dot = (
                    '<div style="width:10px;height:10px;background:#ff3333;'
                    'border-radius:50%;border:2px solid #fff;"></div>'
                )
            icon = folium.DivIcon(html=dot, icon_size=(14, 14), icon_anchor=(7, 7))
            label = f"SRV-{node.id:03d} (Prio: {node.reward})"

        coord_str = f"{ll[0]:.5f}, {ll[1]:.5f}"
        tooltip_text = f"{sel_prefix}{label} [{coord_str}]"

        folium.Marker(location=ll, icon=icon, tooltip=tooltip_text).add_to(m)

    # Fit bounds
    all_lls = [list(xy_to_latlon(n.x, n.y, map_size, center)) for n in env.nodes]
    if all_lls:
        m.fit_bounds(all_lls, padding=[30, 30])

    return m


# =============================================================================
# PLOTLY ANALYTICS (dark-themed)
# =============================================================================
_PLOTLY_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(17,24,39,.8)",
    font=dict(color="#94a3b8", family="Inter, sans-serif"),
    xaxis=dict(gridcolor="rgba(0,212,255,.06)", zerolinecolor="rgba(0,212,255,.1)"),
    yaxis=dict(gridcolor="rgba(0,212,255,.06)", zerolinecolor="rgba(0,212,255,.1)"),
    margin=dict(l=40, r=40, t=50, b=40),
)


def create_reward_chart(env, routes):
    rewards, colors = [], []
    for idx, route in enumerate(routes):
        r = sum(
            env.nodes[nid].reward
            for nid in route
            if env.nodes[nid].node_type == "service"
        )
        rewards.append({"UAV": f"UAV {idx + 1}", "Reward": r})
        colors.append(ROUTE_COLORS[idx % len(ROUTE_COLORS)])
    df = pd.DataFrame(rewards)
    fig = go.Figure(
        go.Bar(
            x=df["UAV"],
            y=df["Reward"],
            marker_color=colors,
            marker_line_color="rgba(255,255,255,.1)",
            marker_line_width=1,
            text=df["Reward"],
            textposition="auto",
            textfont=dict(color="#e0e0e0"),
        )
    )
    fig.update_layout(title="Reward per UAV", height=380, **_PLOTLY_DARK)
    return fig


def create_coverage_chart(env, routes):
    visited = {
        nid for route in routes for nid in route if env.nodes[nid].node_type == "service"
    }
    data = [
        {
            "Node": n.id,
            "Reward": n.reward,
            "Status": "Visited" if n.id in visited else "Unvisited",
        }
        for n in env.service_nodes
    ]
    df = pd.DataFrame(data)
    fig = go.Figure()
    for status, clr in [("Visited", "#00d4ff"), ("Unvisited", "#ff4444")]:
        sub = df[df["Status"] == status]
        fig.add_trace(
            go.Scatter(
                x=sub["Node"],
                y=sub["Reward"],
                mode="markers",
                name=status,
                marker=dict(
                    size=sub["Reward"] / 3 + 6,
                    color=clr,
                    opacity=0.8,
                    line=dict(color="rgba(255,255,255,.15)", width=1),
                ),
            )
        )
    fig.update_layout(title="Node Coverage", height=380, **_PLOTLY_DARK)
    return fig


def create_battery_chart(env, routes):
    fig = go.Figure()
    for idx, route in enumerate(routes):
        levels, steps = [env.battery_limit], [0]
        bat = env.battery_limit
        for i in range(len(route) - 1):
            fn, tn = env.nodes[route[i]], env.nodes[route[i + 1]]
            d = np.sqrt((tn.x - fn.x) ** 2 + (tn.y - fn.y) ** 2)
            bat = env.battery_limit if tn.node_type == "charging" else max(0, bat - d)
            levels.append(bat)
            steps.append(i + 1)
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=levels,
                mode="lines+markers",
                name=f"UAV {idx + 1}",
                line=dict(color=ROUTE_COLORS[idx % len(ROUTE_COLORS)], width=3),
                marker=dict(size=6, color=ROUTE_COLORS[idx % len(ROUTE_COLORS)]),
            )
        )
    fig.add_hline(
        y=env.battery_limit,
        line_dash="dot",
        line_color="#ff4444",
        annotation_text="Max",
        annotation_font_color="#ff4444",
    )
    fig.update_layout(
        title="Battery Level Throughout Mission",
        height=420,
        hovermode="x unified",
        **_PLOTLY_DARK,
    )
    return fig


def battery_stats_df(env, routes):
    rows = []
    for idx, route in enumerate(routes):
        bat, min_b, recharges, td = env.battery_limit, env.battery_limit, 0, 0.0
        for i in range(len(route) - 1):
            fn, tn = env.nodes[route[i]], env.nodes[route[i + 1]]
            d = np.sqrt((tn.x - fn.x) ** 2 + (tn.y - fn.y) ** 2)
            td += d
            if tn.node_type == "charging":
                recharges += 1
                bat = env.battery_limit
            else:
                bat -= d
                min_b = min(min_b, bat)
        rows.append(
            {
                "UAV": f"UAV {idx + 1}",
                "Dist (units)": f"{td:.1f}",
                "Min Battery": f"{min_b:.1f}",
                "Recharges": recharges,
                "Final Battery": f"{bat:.1f}",
            }
        )
    return pd.DataFrame(rows)


def create_cluster_plot(cfqs):
    env = cfqs.env
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[env.depot.x],
            y=[env.depot.y],
            mode="markers",
            name="Depot",
            marker=dict(
                size=22, color="#00ff88", symbol="square", line=dict(color="#fff", width=2)
            ),
        )
    )
    ch = env.charging_stations
    if ch:
        fig.add_trace(
            go.Scatter(
                x=[n.x for n in ch],
                y=[n.y for n in ch],
                mode="markers",
                name="Charging",
                marker=dict(
                    size=16,
                    color="#ffaa00",
                    symbol="triangle-up",
                    line=dict(color="#fff", width=1),
                ),
            )
        )
    for cid, nodes in enumerate(cfqs.clusters):
        if nodes:
            fig.add_trace(
                go.Scatter(
                    x=[n.x for n in nodes],
                    y=[n.y for n in nodes],
                    mode="markers",
                    name=f"Cluster {cid + 1}",
                    marker=dict(
                        size=12,
                        color=ROUTE_COLORS[cid % len(ROUTE_COLORS)],
                        opacity=0.7,
                        line=dict(color="rgba(255,255,255,.2)", width=1),
                    ),
                    text=[f"Node {n.id}<br>Reward: {n.reward}" for n in nodes],
                    hovertemplate="<b>%{text}</b><extra></extra>",
                )
            )
    fig.update_layout(
        title="K-Means Clustering",
        height=550,
        **_PLOTLY_DARK,
    )
    fig.update_layout(
        xaxis=dict(range=[0, env.map_size]),
        yaxis=dict(range=[0, env.map_size], scaleanchor="x"),
    )
    return fig


def route_detail_df(env, route, map_size, center):
    rows = []
    cum_km = 0.0
    for step, nid in enumerate(route):
        node = env.nodes[nid]
        ll = xy_to_latlon(node.x, node.y, map_size, center)
        if step > 0:
            prev = env.nodes[route[step - 1]]
            pll = xy_to_latlon(prev.x, prev.y, map_size, center)
            cum_km += haversine(pll[0], pll[1], ll[0], ll[1])
        rows.append(
            {
                "Step": step,
                "Node": nid,
                "Type": node.node_type.upper(),
                "Lat": f"{ll[0]:.5f}",
                "Lon": f"{ll[1]:.5f}",
                "Reward": node.reward if node.node_type == "service" else 0,
                "Cum. Dist (km)": f"{cum_km:.3f}",
            }
        )
    return pd.DataFrame(rows)


def missed_opportunities(env, routes):
    visited = {
        nid for route in routes for nid in route if env.nodes[nid].node_type == "service"
    }
    missed = [
        {"Node": n.id, "Reward": n.reward, "Pos": f"({n.x:.1f}, {n.y:.1f})"}
        for n in env.service_nodes
        if n.id not in visited
    ]
    missed.sort(key=lambda x: x["Reward"], reverse=True)
    return pd.DataFrame(missed) if missed else None


# =============================================================================
# SESSION STATE
# =============================================================================
_DEFAULTS = {
    "environment": None,
    "routes": [],
    "solution_summary": None,
    "training_history": None,
    "theater": "Sierra Nevada, CA",
    "placing_node": None,
    "last_click_processed": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("### Mission Configuration")

    with st.expander("Theater of Operations", expanded=True):
        theater_name = st.selectbox(
            "Location",
            list(THEATERS.keys()),
            index=list(THEATERS.keys()).index(st.session_state.theater),
        )
        st.session_state.theater = theater_name
        center = THEATERS[theater_name]
        st.caption(f"Center: `{center[0]:.4f}, {center[1]:.4f}`")

    with st.expander("Environment", expanded=True):
        n_service_nodes = st.selectbox("Survivor Count", [10, 20, 30, 50, 100], index=1)
        n_uavs = st.selectbox("UAV Fleet Size", [1, 2, 3, 4, 5], index=1)
        n_charging = st.selectbox("Charging Stations", [2, 3, 5, 10], index=0)
        map_size = st.slider("Search Area (units)", 50, 200, 100, 10)
        time_limit = st.slider("Time Limit", 50, 300, 100, 10)
        battery_limit = st.slider("Battery Capacity", 25, 150, 50, 5)
        seed = st.number_input("Random Seed", 0, 9999, 42)

    with st.expander("Algorithm", expanded=True):
        algorithm = st.selectbox(
            "Solver",
            [
                "Improved Q-Learning (Reward-Biased)",
                "Original Q-Learning (NDTS)",
                "Greedy Baseline",
            ],
        )
        n_episodes = st.selectbox(
            "Training Episodes", [5000, 10000, 20000, 50000, 100000], index=2
        )

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        btn_gen = st.button("Generate", type="primary", use_container_width=True)
    with c2:
        btn_solve = st.button("Solve", use_container_width=True)

    # ---- Generate ----
    if btn_gen:
        with st.spinner("Generating environment\u2026"):
            st.session_state.environment = UAVEnvironment(
                n_service_nodes=n_service_nodes,
                n_charging_stations=n_charging,
                map_size=map_size,
                time_limit=time_limit,
                battery_limit=battery_limit,
                seed=seed,
            )
            st.session_state.routes = []
            st.session_state.solution_summary = None
            st.session_state.training_history = None
            st.session_state.placing_node = None
            st.session_state.last_click_processed = None
            for attr in ("cfqs", "algorithm_used"):
                if hasattr(st.session_state, attr):
                    delattr(st.session_state, attr)
            # Clean up old node coordinate keys
            for k in list(st.session_state.keys()):
                if k.startswith("node_") and k.endswith(("_lat", "_lon")):
                    del st.session_state[k]
            # Populate coordinates from new environment
            init_coords_from_env(st.session_state.environment, map_size, center)
            st.success("Environment ready")
            st.rerun()

    # ---- Solve ----
    if btn_solve:
        if st.session_state.environment is None:
            st.error("Generate an environment first")
        else:
            if algorithm == "Greedy Baseline":
                with st.spinner(f"Running Greedy solver ({n_uavs} UAVs)\u2026"):
                    solver = GreedySolver(st.session_state.environment)
                    routes, total_reward = solver.solve_multi_uav(n_uavs=n_uavs)
                    st.session_state.routes = routes
                    st.session_state.solution_summary = {
                        "n_uavs": n_uavs,
                        "total_reward": total_reward,
                        "total_service_nodes_visited": sum(
                            1
                            for route in routes
                            for nid in route
                            if st.session_state.environment.nodes[nid].node_type == "service"
                        ),
                        "routes": routes,
                        "route_lengths": [len(r) for r in routes],
                    }
                    st.session_state.algorithm_used = "Greedy"
                    st.success("Solution found")
                    st.rerun()
            else:
                with st.spinner(f"Training {n_uavs} UAV(s) with {algorithm}\u2026"):
                    cfqs = TwoPhaseApproach(st.session_state.environment, n_uavs=n_uavs)
                    cfqs.phase1_clustering()
                    if algorithm == "Improved Q-Learning (Reward-Biased)":
                        cfqs.phase2_solve_clusters_improved(
                            n_episodes=n_episodes, verbose=False
                        )
                    else:
                        cfqs.phase2_solve_clusters(n_episodes=n_episodes, verbose=False)
                    cfqs.validate_cluster_assignment()

                    st.session_state.routes = cfqs.routes
                    st.session_state.solution_summary = cfqs.get_solution_summary()
                    st.session_state.cfqs = cfqs
                    st.session_state.algorithm_used = algorithm
                    st.success("Solution found")
                    st.rerun()

# =============================================================================
# MAIN CONTENT
# =============================================================================
st.title("UAV Search & Rescue Command Center")
st.caption("Geospatial Mission Planning & Route Optimization")

if st.session_state.environment is None:
    # ---- Landing page ----
    st.markdown(
        """
    <div style="text-align:center;padding:50px 20px 30px;">
        <div style="font-size:3.5rem;margin-bottom:16px;">\U0001F6F0\uFE0F</div>
        <h2 style="color:#00d4ff;margin-bottom:8px;">Mission Planning Console</h2>
        <p style="color:#64748b;font-size:1.05rem;max-width:560px;margin:0 auto 24px;">
            Configure search parameters in the sidebar and click <b>Generate</b>
            to initialize the theater of operations.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Default Survivors", "20")
    with col2:
        st.metric("Default UAVs", "2")
    with col3:
        st.metric("Default Charging", "2")

    st.markdown(
        """
    ### Workflow
    1. **Generate** - Create a randomized theater with survivor locations
    2. **Solve** - Run RL or greedy routing to optimize rescue paths
    3. **Analyze** - Inspect routes on a real-world map with full analytics
    """
    )

else:
    env = st.session_state.environment
    center = THEATERS[st.session_state.theater]
    ms = env.map_size

    # ---- Sync node positions from user-edited coordinates ----
    if f"node_0_lat" in st.session_state:
        # Re-init if the theater (projection center) changed
        if st.session_state.get("_coords_center") != center:
            init_coords_from_env(env, ms, center)
        else:
            sync_env_from_coords(env, ms, center)

    # ---- Metrics ----
    if st.session_state.solution_summary:
        summary = st.session_state.solution_summary
        total_km = sum(
            route_distance_km(env, r, ms, center) for r in st.session_state.routes
        )
        algo_label = getattr(st.session_state, "algorithm_used", "N/A")

        # Status bar
        st.markdown(
            f"""<div class="legend-bar">
            <div class="legend-item"><span class="legend-dot" style="background:#00ff88;"></span> {theater_name}</div>
            <div class="legend-item"><span class="legend-dot" style="background:#00d4ff;"></span> {algo_label}</div>
            <div class="legend-item"><span class="legend-dot" style="background:#ffaa00;"></span> {summary['n_uavs']} UAV(s)</div>
        </div>""",
            unsafe_allow_html=True,
        )

        mc = st.columns(5)
        with mc[0]:
            st.metric("Total Reward", f"{summary['total_reward']:.0f}")
        with mc[1]:
            st.metric(
                "Rescued",
                f"{summary['total_service_nodes_visited']}/{len(env.service_nodes)}",
            )
        with mc[2]:
            cov = summary["total_service_nodes_visited"] / max(len(env.service_nodes), 1) * 100
            st.metric("Coverage", f"{cov:.1f}%")
        with mc[3]:
            st.metric("Route Distance", f"{total_km:.2f} km")
        with mc[4]:
            eff = summary["total_reward"] / max(summary["n_uavs"], 1)
            st.metric("Efficiency", f"{eff:.1f}")
    else:
        mc = st.columns(4)
        with mc[0]:
            st.metric("Survivors", len(env.service_nodes))
        with mc[1]:
            st.metric("Charging Stations", len(env.charging_stations))
        with mc[2]:
            st.metric("Time Limit", env.time_limit)
        with mc[3]:
            st.metric("Battery Cap.", env.battery_limit)

    st.divider()

    # ---- Legend ----
    st.markdown(
        """<div class="legend-bar">
        <div class="legend-item"><span class="legend-dot" style="background:#00ff88;"></span> Command Base</div>
        <div class="legend-item"><span class="legend-dot" style="background:#ff3333;"></span> Survivors</div>
        <div class="legend-item"><span class="legend-dot" style="background:#ffaa00;"></span> Charging Stations</div>
        <div class="legend-item"><span class="legend-dot" style="background:#aa55ff;"></span> Extraction Zone</div>
    </div>""",
        unsafe_allow_html=True,
    )

    # ---- Tabs ----
    tab_map, tab_editor, tab_analytics, tab_battery, tab_clusters = st.tabs(
        ["Mission Map", "Node Editor", "Analytics", "Battery", "Clusters"]
    )

    with tab_map:
        fmap = build_command_map(
            env,
            st.session_state.routes if st.session_state.routes else None,
            ms,
            center,
        )
        st_folium(fmap, height=660, use_container_width=True, returned_objects=[])

        # Per-route distance table below the map
        if st.session_state.routes:
            st.markdown("##### Route Distance Summary (Haversine)")
            dist_rows = []
            for idx, route in enumerate(st.session_state.routes):
                km = route_distance_km(env, route, ms, center)
                svc = sum(
                    1 for nid in route if env.nodes[nid].node_type == "service"
                )
                dist_rows.append(
                    {
                        "UAV": f"UAV {idx + 1}",
                        "Waypoints": len(route),
                        "Survivors": svc,
                        "Distance (km)": f"{km:.3f}",
                    }
                )
            st.dataframe(pd.DataFrame(dist_rows), width='stretch')

    # ------------------------------------------------------------------
    # NODE EDITOR TAB
    # ------------------------------------------------------------------
    with tab_editor:
        st.markdown(
            """<div style="background:rgba(0,212,255,.06);border:1px solid rgba(0,212,255,.15);
            border-radius:10px;padding:12px 16px;margin-bottom:12px;">
            <span style="color:#00d4ff;font-weight:600;">Node Editor</span>
            <span style="color:#64748b;font-size:.88rem;"> &mdash;
            Select a node below, then <b>click the map</b> to reposition it
            or type exact coordinates. Changes apply in real time.</span>
            </div>""",
            unsafe_allow_html=True,
        )

        # --- Node selector ---
        node_options = {"-- Select a node to edit --": None}
        node_options["Command Base (Depot)"] = 0
        node_options["Extraction Zone"] = 1
        for cs in sorted(env.charging_stations, key=lambda n: n.id):
            node_options[f"Charging Station CS-{cs.id:03d}"] = cs.id
        for srv in sorted(env.service_nodes, key=lambda n: n.id):
            node_options[f"Survivor SRV-{srv.id:03d} (Prio: {srv.reward})"] = srv.id

        sel_label = st.selectbox(
            "Select Node to Edit / Place",
            list(node_options.keys()),
            key="node_editor_selector",
        )
        selected_id = node_options[sel_label]
        st.session_state.placing_node = selected_id

        # Status indicator
        if selected_id is not None:
            st.info(
                f"Click on the map to reposition **{sel_label}**. "
                "The coordinates below will update automatically."
            )
        else:
            st.caption("Select a node above to begin editing.")

        # --- Interactive editor map ---
        editor_map = build_editor_map(env, ms, center, selected_id)
        map_data = st_folium(
            editor_map,
            height=520,
            use_container_width=True,
            returned_objects=["last_clicked"],
        )

        # --- Handle map click for placement ---
        if (
            map_data
            and map_data.get("last_clicked")
            and selected_id is not None
        ):
            click_lat = map_data["last_clicked"]["lat"]
            click_lng = map_data["last_clicked"]["lng"]
            click_key = f"{click_lat:.10f},{click_lng:.10f},{selected_id}"
            if click_key != st.session_state.get("last_click_processed"):
                st.session_state.last_click_processed = click_key
                st.session_state[f"node_{selected_id}_lat"] = round(click_lat, 6)
                st.session_state[f"node_{selected_id}_lon"] = round(click_lng, 6)
                st.rerun()

        # --- Coordinate entry for selected node ---
        if selected_id is not None:
            st.markdown(f"##### Coordinates for {sel_label}")
            ce1, ce2, ce3 = st.columns([2, 2, 1])
            with ce1:
                st.number_input(
                    "Latitude",
                    key=f"node_{selected_id}_lat",
                    format="%.6f",
                    step=0.0001,
                )
            with ce2:
                st.number_input(
                    "Longitude",
                    key=f"node_{selected_id}_lon",
                    format="%.6f",
                    step=0.0001,
                )
            with ce3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Deselect", key="deselect_node", use_container_width=True):
                    st.session_state.placing_node = None
                    st.rerun()

        st.divider()

        # --- Quick-edit panels for key points (skip if already selected above) ---
        st.markdown("##### Key Points")
        kp1, kp2 = st.columns(2)
        with kp1:
            if selected_id == 0:
                st.caption("Command Base (Depot) \u2014 editing above")
            else:
                with st.expander("Command Base (Depot)", expanded=False):
                    st.number_input(
                        "Lat", key="node_0_lat", format="%.6f", step=0.0001,
                        label_visibility="collapsed",
                    )
                    st.number_input(
                        "Lon", key="node_0_lon", format="%.6f", step=0.0001,
                        label_visibility="collapsed",
                    )
        with kp2:
            if selected_id == 1:
                st.caption("Extraction Zone \u2014 editing above")
            else:
                with st.expander("Extraction Zone", expanded=False):
                    st.number_input(
                        "Lat", key="node_1_lat", format="%.6f", step=0.0001,
                        label_visibility="collapsed",
                    )
                    st.number_input(
                        "Lon", key="node_1_lon", format="%.6f", step=0.0001,
                        label_visibility="collapsed",
                    )

        if env.charging_stations:
            st.markdown("##### Charging Stations")
            cs_cols = st.columns(min(len(env.charging_stations), 4))
            for idx, cs_node in enumerate(
                sorted(env.charging_stations, key=lambda n: n.id)
            ):
                with cs_cols[idx % len(cs_cols)]:
                    if selected_id == cs_node.id:
                        st.caption(f"CS-{cs_node.id:03d} \u2014 editing above")
                    else:
                        with st.expander(f"CS-{cs_node.id:03d}", expanded=False):
                            st.number_input(
                                "Lat",
                                key=f"node_{cs_node.id}_lat",
                                format="%.6f",
                                step=0.0001,
                                label_visibility="collapsed",
                            )
                            st.number_input(
                                "Lon",
                                key=f"node_{cs_node.id}_lon",
                                format="%.6f",
                                step=0.0001,
                                label_visibility="collapsed",
                            )

        # --- All-coordinates reference table ---
        with st.expander("All Node Coordinates", expanded=False):
            coord_rows = []
            for node in sorted(env.nodes, key=lambda n: n.id):
                lat_val = st.session_state.get(
                    f"node_{node.id}_lat",
                    xy_to_latlon(node.x, node.y, ms, center)[0],
                )
                lon_val = st.session_state.get(
                    f"node_{node.id}_lon",
                    xy_to_latlon(node.x, node.y, ms, center)[1],
                )
                if node.id == 0:
                    label = "Command Base"
                elif node.id == 1:
                    label = "Extraction Zone"
                elif node.node_type == "charging":
                    label = f"Charging CS-{node.id:03d}"
                else:
                    label = f"Survivor SRV-{node.id:03d}"
                coord_rows.append(
                    {
                        "Node": label,
                        "Type": node.node_type.title(),
                        "Latitude": f"{lat_val:.6f}",
                        "Longitude": f"{lon_val:.6f}",
                        "Reward": node.reward,
                    }
                )
            st.dataframe(
                pd.DataFrame(coord_rows), width='stretch', hide_index=True
            )

    with tab_analytics:
        if st.session_state.routes:
            a1, a2 = st.columns(2)
            with a1:
                st.plotly_chart(
                    create_reward_chart(env, st.session_state.routes),
                    width='stretch',
                )
            with a2:
                st.plotly_chart(
                    create_coverage_chart(env, st.session_state.routes),
                    width='stretch',
                )
        else:
            st.info("Solve the mission to see analytics")

    with tab_battery:
        if st.session_state.routes:
            st.plotly_chart(
                create_battery_chart(env, st.session_state.routes),
                width='stretch',
            )
            st.markdown("##### Battery Statistics")
            st.dataframe(
                battery_stats_df(env, st.session_state.routes), width='stretch'
            )
        else:
            st.info("Solve the mission to see battery analysis")

    with tab_clusters:
        if hasattr(st.session_state, "cfqs"):
            st.plotly_chart(
                create_cluster_plot(st.session_state.cfqs), width='stretch'
            )
        else:
            st.info("Solve with Q-Learning to see cluster analysis")

    # ---- Route Details & Missed Opportunities ----
    if st.session_state.routes:
        st.divider()
        d1, d2 = st.columns(2)

        with d1:
            st.subheader("Route Details")
            for i, route in enumerate(st.session_state.routes):
                with st.expander(f"UAV {i + 1} \u2014 {len(route)} waypoints"):
                    st.dataframe(
                        route_detail_df(env, route, ms, center),
                        width='stretch',
                    )

        with d2:
            st.subheader("Missed Opportunities")
            missed = missed_opportunities(env, st.session_state.routes)
            if missed is not None and len(missed) > 0:
                st.warning(f"**{len(missed)} survivors not reached**")
                st.dataframe(missed.head(10), width='stretch')
                if len(missed) > 10:
                    with st.expander(f"All {len(missed)} missed"):
                        st.dataframe(missed, width='stretch')
                pot = missed["Reward"].sum()
                cur = st.session_state.solution_summary["total_reward"]
                st.metric(
                    "Potential Additional Reward",
                    f"{pot:.0f}",
                    delta=f"+{pot / max(cur, 1) * 100:.1f}%",
                )
            else:
                st.success("All survivors reached!")
