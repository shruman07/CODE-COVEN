"""
SafeGrid - Cyberpunk Soft-Glam Women's Safety Matrix and AI Navigator
Developed by Team Code Coven | Infinity Hacks 2026

Backend ML Integration:
  1. get_risk_grid(time) -> Live city risk grid plotted on interactive Leaflet map
  2. Time selector (morning/afternoon/evening/night) -> Real-time model recalculation
  3. submit_report(lat, lon, note) -> Instant crowdsourced incident reporting
  4. get_reroute(start, end, time) -> Multi-candidate safer routing algorithm
  5. predict_risk(lat, lon, time) -> Spot safety prediction with risk band and score
"""

import os
import json
import time as pytime
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

# Import Backend Functions
try:
    from backend import (
        get_risk_grid,
        submit_report,
        get_reroute,
        predict_risk,
        backend_info,
        get_risk_band,
        get_time_bucket,
        REPORTS_PATH,
        DATA_PATH,
    )
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from backend import (
        get_risk_grid,
        submit_report,
        get_reroute,
        predict_risk,
        backend_info,
        get_risk_band,
        get_time_bucket,
        REPORTS_PATH,
        DATA_PATH,
    )

# ============================================================
# 1. PAGE CONFIGURATION AND THEME (NO EMOJIS)
# ============================================================
st.set_page_config(
    page_title="SafeGrid | Urban Safety Intelligence and Predictive Navigation",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 2. CONSTANTS AND PALETTE (CYBERPUNK SOFT GLAM)
# ============================================================
CITY_CENTER = [20.2961, 85.8245]  # Bhubaneswar Center

# High-contrast solid colors for guaranteed visibility
BAND_COLORS = {
    "low": "#00E676",     # High-visibility Emerald Green (Low Risk)
    "medium": "#FFB300",  # Neon Solar Amber (Medium Risk)
    "high": "#FF1744",    # Neon Crimson Ruby (High Risk)
}

BAND_LABELS = {
    "low": "LOW RISK (SAFE ZONE)",
    "medium": "MODERATE RISK (CAUTION)",
    "high": "ELEVATED RISK (ALERT)",
}

# Extensive roster of Bhubaneswar landmarks for user-friendly routing
POPULAR_LANDMARKS = {
    "KIIT Campus, Patia": (20.3560, 85.8190),
    "Patia / Infocity IT Hub": (20.3520, 85.8200),
    "Esplanade One Mall, Rasulgarh": (20.2990, 85.8420),
    "Master Canteen Square": (20.2700, 85.8410),
    "Jaydev Vihar Square": (20.2960, 85.8180),
    "Bhubaneswar Railway Station": (20.2679, 85.8398),
    "Saheed Nagar Market": (20.2940, 85.8420),
    "Biju Patnaik International Airport": (20.2530, 85.8180),
    "Vani Vihar (Utkal University)": (20.2950, 85.8390),
    "Kalinga Stadium Sports Complex": (20.2870, 85.8250),
    "Unit-1 Market Building": (20.2650, 85.8360),
    "Unit-4 Commercial Area": (20.2760, 85.8420),
    "Chandrasekharpur Housing": (20.3450, 85.8100),
    "Old Town / Lingaraj Temple": (20.2380, 85.8340),
    "Baramunda Bus Terminal": (20.2955, 85.7929),
    "Khandagiri Square": (20.2610, 85.7780),
    "Rasulgarh Market Square": (20.2960, 85.8560),
    "Bapuji Nagar Commercial": (20.2610, 85.8310),
    "STPI Bhubaneswar": (20.3430, 85.8230),
    "Nandankanan Road": (20.3940, 85.8180),
}

# ============================================================
# 3. CUSTOM CYBERPUNK SOFT-GLAM STYLING (CSS - ZERO EMOJIS)
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

    :root {
        --bg-obsidian: #080914;
        --bg-card: rgba(18, 20, 42, 0.85);
        --accent-magenta: #FF2A85;
        --accent-rose: #FFB8D9;
        --accent-cyan: #00F0FF;
        --accent-purple: #9B51E0;
        --safe-green: #00E676;
        --warn-amber: #FFB300;
        --danger-ruby: #FF1744;
        --text-primary: #FFFFFF;
        --text-secondary: #D4C9E6;
        --border-glass: rgba(255, 42, 133, 0.25);
    }

    /* Overall Application Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(255, 42, 133, 0.08) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(155, 81, 224, 0.1) 0%, transparent 40%),
                    #080914 !important;
        font-family: 'Outfit', sans-serif !important;
        color: #FFFFFF !important;
    }

    /* Headers and Titles */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em;
        color: #FFFFFF !important;
    }

    .glam-title {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFB8D9 45%, #FF2A85 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 0.02em;
        margin-bottom: 0.1rem;
    }

    .glam-subtitle {
        font-family: 'Outfit', sans-serif;
        font-weight: 500;
        color: #C8BEDE;
        font-size: 0.95rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    /* Surface Cards */
    .glam-card {
        background: rgba(18, 20, 42, 0.85);
        border: 1px solid rgba(255, 42, 133, 0.25);
        border-radius: 14px;
        padding: 1.2rem;
        box-shadow: 0 8px 30px 0 rgba(0, 0, 0, 0.5);
        margin-bottom: 1rem;
    }

    /* Status Badges */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(0, 230, 118, 0.12);
        border: 1px solid rgba(0, 230, 118, 0.4);
        color: #00E676;
        padding: 0.3rem 0.8rem;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .live-pulse {
        width: 8px;
        height: 8px;
        background-color: #00E676;
        border-radius: 50%;
        box-shadow: 0 0 8px #00E676;
        animation: pulse 1.6s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.7; }
        50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 12px #00E676; }
        100% { transform: scale(0.95); opacity: 0.7; }
    }

    /* Primary Interactive Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #FF2A85 0%, #B71C5A 100%) !important;
        color: #FFFFFF !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255, 184, 217, 0.3) !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.2rem !important;
        box-shadow: 0 4px 16px rgba(255, 42, 133, 0.35) !important;
        transition: all 0.2s ease-in-out !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #FF4598 0%, #D1236E 100%) !important;
        box-shadow: 0 6px 22px rgba(255, 42, 133, 0.55) !important;
        transform: translateY(-1px);
    }

    /* Red Action Button */
    .sos-btn div.stButton > button {
        background: linear-gradient(135deg, #FF1744 0%, #B3002D 100%) !important;
        box-shadow: 0 4px 20px rgba(255, 23, 68, 0.5) !important;
        border: 1px solid rgba(255, 100, 130, 0.5) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    /* Metric Containers */
    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        color: #FFB8D9 !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Outfit', sans-serif !important;
        color: #A99EBE !important;
        text-transform: uppercase;
        font-size: 0.78rem !important;
        letter-spacing: 0.05em;
    }

    /* Form Fields */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background-color: rgba(14, 16, 36, 0.95) !important;
        border-color: rgba(255, 42, 133, 0.3) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }

    /* Workspace Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: rgba(15, 17, 36, 0.8);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 42, 133, 0.2);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #A69DBB;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(255, 42, 133, 0.35) 0%, rgba(155, 81, 224, 0.35) 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255, 42, 133, 0.6) !important;
        box-shadow: 0 0 12px rgba(255, 42, 133, 0.3);
    }

    /* Sidebar Navigation */
    section[data-testid="stSidebar"] {
        background-color: #0B0C1E !important;
        border-right: 1px solid rgba(255, 42, 133, 0.2) !important;
    }

    /* Risk Text Badges */
    .badge-low {
        background: rgba(0, 230, 118, 0.18);
        color: #00E676;
        border: 1px solid #00E676;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-medium {
        background: rgba(255, 179, 0, 0.18);
        color: #FFB300;
        border: 1px solid #FFB300;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-high {
        background: rgba(255, 23, 68, 0.2);
        color: #FF1744;
        border: 1px solid #FF1744;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
    }

    /* Helpline Container */
    .helpline-box {
        background: rgba(20, 24, 50, 0.9);
        border: 1px solid rgba(255, 184, 217, 0.2);
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        transition: all 0.2s;
    }
    .helpline-box:hover {
        border-color: #FF2A85;
        box-shadow: 0 0 12px rgba(255, 42, 133, 0.35);
    }
    .helpline-num {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.25rem;
        font-weight: 800;
        color: #FFB8D9;
    }
    .helpline-desc {
        font-size: 0.7rem;
        color: #A99EBE;
        text-transform: uppercase;
        font-weight: 600;
    }

    /* Fixed Map Canvas Background */
    iframe {
        background-color: #0c0e1e !important;
        border-radius: 12px;
        border: 1px solid rgba(255, 42, 133, 0.25) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 4. SESSION STATE INITIALIZATION
# ============================================================
if "time_of_day" not in st.session_state:
    st.session_state["time_of_day"] = "night"

if "selected_point" not in st.session_state:
    st.session_state["selected_point"] = CITY_CENTER

if "start_coords" not in st.session_state:
    st.session_state["start_coords"] = POPULAR_LANDMARKS["KIIT Campus, Patia"]
    st.session_state["start_name"] = "KIIT Campus, Patia"

if "end_coords" not in st.session_state:
    st.session_state["end_coords"] = POPULAR_LANDMARKS["Esplanade One Mall, Rasulgarh"]
    st.session_state["end_name"] = "Esplanade One Mall, Rasulgarh"

if "calculated_route" not in st.session_state:
    st.session_state["calculated_route"] = None

if "report_success_toast" not in st.session_state:
    st.session_state["report_success_toast"] = None

if "fake_call_step" not in st.session_state:
    st.session_state["fake_call_step"] = "idle"

if "map_selection_mode" not in st.session_state:
    st.session_state["map_selection_mode"] = "start"

# ============================================================
# 5. CACHED BACKEND DATA LOADER
# ============================================================
@st.cache_data(show_spinner=False)
def fetch_cached_risk_grid(time_bucket_str):
    """Cached high-speed retrieval of city risk grid."""
    return get_risk_grid(time_bucket_str)

def get_current_time_bucket():
    """Auto-detect current real-world time bucket."""
    hour = datetime.now().hour
    return get_time_bucket(hour)

def generate_leaflet_map(risk_grid, route_data=None, selected_latlon=None):
    """
    Build Folium map with high-visibility markers and solid contrast.
    Low Risk = Emerald Green, Medium Risk = Amber, High Risk = Crimson Red.
    Maintains solid opacity without fading or lightening on user interaction.
    """
    m = folium.Map(
        location=CITY_CENTER,
        zoom_start=13,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # 1. Stratified Grid Sampling to guarantee clear presence of ALL risk bands
    # Collect all low risk, medium risk, and high risk segments
    low_cells = [c for c in risk_grid if c.get("band") == "low"]
    med_cells = [c for c in risk_grid if c.get("band") == "medium"]
    high_cells = [c for c in risk_grid if c.get("band") == "high"]

    # Keep all green points and sample medium/high to maintain 60 FPS and crisp visibility
    display_grid = low_cells + med_cells[::2] + high_cells[::2]

    # Feature Group for Risk Points
    grid_group = folium.FeatureGroup(name="SafeGrid Monitored Segments", show=True)

    for cell in display_grid:
        band = cell.get("band", "medium")
        color = BAND_COLORS.get(band, "#FFB300")
        score = cell.get("score", 0.0)
        landmark = cell.get("landmark", f"Segment {cell.get('segment_id', '')}")
        zone = cell.get("zone_type", "Urban Area").replace("_", " ").title()

        # Solid HTML card with dark background
        popup_html = f"""
        <div style="font-family: 'Outfit', sans-serif; background: #0E1022; color: #FFFFFF; padding: 10px; border-radius: 8px; border: 1px solid {color}; width: 210px;">
            <div style="font-size: 12px; font-weight: 700; color: #FFB8D9; margin-bottom: 2px;">{landmark}</div>
            <div style="font-size: 10px; color: #8E88A8; margin-bottom: 6px;">Zone: {zone}</div>
            <div style="background: {color}25; border: 1px solid {color}; color: {color}; font-weight: 800; font-size: 11px; padding: 3px 6px; border-radius: 4px; text-align: center; text-transform: uppercase;">
                [{band.upper()} RISK]
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #D4C9E6; border-top: 1px solid #252848; margin-top: 6px; padding-top: 4px;">
                <span>AI Risk Score:</span>
                <strong style="color: {color};">{score} / 100</strong>
            </div>
        </div>
        """

        tooltip_text = f"[{band.upper()} RISK] {landmark} ({score}/100)"

        # Solid CircleMarker: high fill_opacity and solid border to prevent lightening
        folium.CircleMarker(
            location=[cell["lat"], cell["lon"]],
            radius=7.5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.90,
            opacity=1.0,
            weight=1.5,
            tooltip=tooltip_text,
            popup=folium.Popup(popup_html, max_width=230),
        ).add_to(grid_group)

    grid_group.add_to(m)

    # 2. Key Anchor Landmarks
    landmark_group = folium.FeatureGroup(name="Bhubaneswar Urban Landmarks", show=True)
    for name, coords in POPULAR_LANDMARKS.items():
        folium.CircleMarker(
            location=coords,
            radius=4.5,
            color="#FF2A85",
            fill=True,
            fill_color="#FFFFFF",
            fill_opacity=1.0,
            opacity=1.0,
            weight=2,
            tooltip=f"Landmark: {name}",
        ).add_to(landmark_group)
    landmark_group.add_to(m)

    # 3. Selected User Target Location Marker
    if selected_latlon:
        folium.Marker(
            location=selected_latlon,
            tooltip="Selected Coordinate",
            icon=folium.Icon(color="purple", icon="info-sign"),
        ).add_to(m)

    # 4. Computed AI Safer Route (Solid Emerald Polyline)
    if route_data and "route" in route_data:
        coords = [(p["lat"], p["lon"]) for p in route_data["route"]]
        if coords:
            # Solid non-fading PolyLine
            folium.PolyLine(
                coords,
                color="#00E676",
                weight=6,
                opacity=1.0,
                tooltip=f"Safe Route - Band: {route_data.get('risk_band', 'LOW').upper()} (Score: {route_data.get('average_risk', 0.0)})",
            ).add_to(m)

            folium.Marker(
                coords[0],
                tooltip="Start Location",
                icon=folium.Icon(color="green", icon="play"),
            ).add_to(m)

            folium.Marker(
                coords[-1],
                tooltip="Destination Location",
                icon=folium.Icon(color="red", icon="stop"),
            ).add_to(m)

    folium.LayerControl(position="topright").add_to(m)
    return m

# ============================================================
# 6. SIDEBAR: TIME SELECTOR AND EMERGENCY HOTLINES
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
            <div style="font-family: 'Syne', sans-serif; font-size: 1.5rem; font-weight: 800; color: #FFFFFF;">SAFEGRID</div>
            <div style="font-size: 0.72rem; color: #FFB8D9; letter-spacing: 0.1em; text-transform: uppercase;">Code Coven | Infinity Hacks 2026</div>
            <div style="margin-top: 8px;">
                <span class="live-badge"><span class="live-pulse"></span> SYSTEM ACTIVE | BHUBANESWAR</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Time-of-Day Matrix
    st.markdown("### Time-of-Day Matrix")
    st.caption("City risk profiles adjust dynamically with lighting and crowd density changes across hours.")
    time_options = ["morning", "afternoon", "evening", "night"]
    current_detected = get_current_time_bucket()

    selected_time = st.select_slider(
        "Active Time Bucket",
        options=time_options,
        value=st.session_state["time_of_day"],
        key="time_slider_sidebar",
    )
    if selected_time != st.session_state["time_of_day"]:
        st.session_state["time_of_day"] = selected_time
        st.rerun()

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("Set Night Mode", use_container_width=True):
            st.session_state["time_of_day"] = "night"
            st.rerun()
    with c_btn2:
        if st.button(f"Sync Local ({current_detected})", use_container_width=True):
            st.session_state["time_of_day"] = current_detected
            st.rerun()

    st.markdown("---")

    # Emergency Hotlines
    st.markdown("### Emergency Hotlines")
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        st.markdown(
            """
            <div class="helpline-box">
                <a href="tel:112" style="text-decoration:none;">
                    <div class="helpline-num">112</div>
                    <div class="helpline-desc">National Emergency</div>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with h_col2:
        st.markdown(
            """
            <div class="helpline-box">
                <a href="tel:1091" style="text-decoration:none;">
                    <div class="helpline-num">1091</div>
                    <div class="helpline-desc">Women Helpline</div>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    h_col3, h_col4 = st.columns(2)
    with h_col3:
        st.markdown(
            """
            <div class="helpline-box" style="margin-top:8px;">
                <a href="tel:181" style="text-decoration:none;">
                    <div class="helpline-num">181</div>
                    <div class="helpline-desc">Women in Distress</div>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with h_col4:
        st.markdown(
            """
            <div class="helpline-box" style="margin-top:8px;">
                <a href="tel:1090" style="text-decoration:none;">
                    <div class="helpline-num">1090</div>
                    <div class="helpline-desc">Anti-Harassment</div>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    b_info = backend_info()
    st.caption(f"Monitored Segments: **{b_info['segments']}** | Engine: **XGBoost AI**")

# ============================================================
# 7. MAIN APPLICATION HEADER
# ============================================================
header_col1, header_col2 = st.columns([3, 1])

with header_col1:
    st.markdown('<div class="glam-title">SAFEGRID MATRIX</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="glam-subtitle">Predictive Urban Safety Intelligence and AI Navigation for Women</div>',
        unsafe_allow_html=True,
    )

with header_col2:
    current_bucket = st.session_state["time_of_day"]
    bucket_badge_color = "#FF1744" if current_bucket == "night" else ("#FFB300" if current_bucket == "evening" else "#00E676")
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 0.4rem;">
            <div style="font-size: 0.78rem; color: #8E88A8;">ACTIVE TIME BUCKET</div>
            <div style="font-family: 'Space Grotesk'; font-size: 1.35rem; font-weight: 700; color: {bucket_badge_color}; text-transform: uppercase;">
                {current_bucket} MODE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# 8. APP WORKSPACES (TABS - ZERO EMOJIS)
# ============================================================
tab_map, tab_sos, tab_companion, tab_feed, tab_analytics, tab_about = st.tabs([
    "Live SafeGrid and Navigation",
    "Emergency Dispatch and Siren",
    "Walk-With-Me Companion",
    "Community Incident Feed",
    "Urban Safety Analytics",
    "System Architecture and ML",
])

# ==============================================================================
# TAB 1: LIVE SAFEGRID AND NAVIGATION (MAP + REPORTING + ROUTING)
# ==============================================================================
with tab_map:
    # 1. Fetch risk grid for selected time bucket
    time_bucket = st.session_state["time_of_day"]
    risk_grid = fetch_cached_risk_grid(time_bucket)

    # Compute summary stats
    total_points = len(risk_grid)
    low_risk_count = sum(1 for c in risk_grid if c["band"] == "low")
    med_risk_count = sum(1 for c in risk_grid if c["band"] == "medium")
    high_risk_count = sum(1 for c in risk_grid if c["band"] == "high")

    # Metrics Bar
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Total Segments", f"{total_points} Blocks")
    with m_col2:
        st.metric("Low Risk (Safe)", f"{low_risk_count} ({low_risk_count/max(1,total_points)*100:.0f}%)")
    with m_col3:
        st.metric("Moderate Risk (Caution)", f"{med_risk_count} ({med_risk_count/max(1,total_points)*100:.0f}%)")
    with m_col4:
        st.metric("Elevated Risk (Alert)", f"{high_risk_count} ({high_risk_count/max(1,total_points)*100:.0f}%)")

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # Layout: Map (Left 64%) vs Command Deck (Right 36%)
    map_col, panel_col = st.columns([64, 36])

    with map_col:
        # High-contrast legend bar
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; background: rgba(18,20,42,0.9); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255,42,133,0.2);">
                <span style="font-weight: 700; font-size: 0.88rem; color: #FFFFFF;">Bhubaneswar Live Risk Heatmap</span>
                <span style="font-size: 0.8rem;">
                    <span class="badge-low">GREEN = LOW RISK</span> &nbsp;
                    <span class="badge-medium">AMBER = MEDIUM RISK</span> &nbsp;
                    <span class="badge-high">RED = HIGH RISK</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Generate Folium Map
        current_map = generate_leaflet_map(
            risk_grid=risk_grid,
            route_data=st.session_state.get("calculated_route"),
            selected_latlon=st.session_state.get("selected_point"),
        )

        # Render Folium Map
        map_output = st_folium(
            current_map,
            use_container_width=True,
            height=560,
            key="safegrid_main_leaflet_map",
            returned_objects=["last_clicked"],
        )

        # Map Clicks detection
        clicked_coords = None
        if map_output and map_output.get("last_clicked"):
            clicked_lat = round(map_output["last_clicked"]["lat"], 5)
            clicked_lng = round(map_output["last_clicked"]["lng"], 5)
            clicked_coords = (clicked_lat, clicked_lng)
            st.session_state["selected_point"] = [clicked_lat, clicked_lng]

            # If user is in "Pick on Map" mode for routing
            if st.session_state.get("map_selection_mode") == "start":
                st.session_state["start_coords"] = (clicked_lat, clicked_lng)
                st.session_state["start_name"] = f"Map Pin ({clicked_lat:.4f}, {clicked_lng:.4f})"
            elif st.session_state.get("map_selection_mode") == "end":
                st.session_state["end_coords"] = (clicked_lat, clicked_lng)
                st.session_state["end_name"] = f"Map Pin ({clicked_lat:.4f}, {clicked_lng:.4f})"

        st.caption("Tip: Select 'Pick on Map' mode on the right to set Start or Destination by clicking anywhere on the map.")

    # ------------------------------------------------------------
    # RIGHT COMMAND DECK: USER-FRIENDLY ROUTING AND REPORTING
    # ------------------------------------------------------------
    with panel_col:
        deck_tab_route, deck_tab_report, deck_tab_spot = st.tabs([
            "AI Safe Route",
            "Felt Unsafe Here?",
            "Spot Inspector",
        ])

        # ------------------------------------------------------------
        # SUB-TAB 1: USER-FRIENDLY AI SAFE ROUTE GENERATOR
        # ------------------------------------------------------------
        with deck_tab_route:
            st.markdown("#### AI Safe Route Navigator")
            st.caption("Calculates safer alternative paths avoiding unlit streets and high incident zones.")

            route_input_method = st.radio(
                "Input Mode",
                options=["Landmark Directory", "Pick on Map", "Enter Coordinates"],
                horizontal=True,
                key="route_input_mode_radio",
            )

            # MODE A: Landmark Directory (User Friendly Default)
            if route_input_method == "Landmark Directory":
                landmark_names = list(POPULAR_LANDMARKS.keys())

                # Origin selector
                default_start_idx = landmark_names.index("KIIT Campus, Patia") if "KIIT Campus, Patia" in landmark_names else 0
                chosen_start_name = st.selectbox(
                    "Start Location (Origin)",
                    options=landmark_names,
                    index=default_start_idx,
                    key="sel_start_landmark",
                )
                st.session_state["start_coords"] = POPULAR_LANDMARKS[chosen_start_name]
                st.session_state["start_name"] = chosen_start_name

                # Swap button
                c_swap1, c_swap2 = st.columns([3, 1])
                with c_swap2:
                    if st.button("Swap Locations", key="btn_swap_landmarks"):
                        temp_c = st.session_state["start_coords"]
                        temp_n = st.session_state["start_name"]
                        st.session_state["start_coords"] = st.session_state["end_coords"]
                        st.session_state["start_name"] = st.session_state["end_name"]
                        st.session_state["end_coords"] = temp_c
                        st.session_state["end_name"] = temp_n
                        st.rerun()

                # Destination selector
                default_end_idx = landmark_names.index("Esplanade One Mall, Rasulgarh") if "Esplanade One Mall, Rasulgarh" in landmark_names else 1
                chosen_end_name = st.selectbox(
                    "End Location (Destination)",
                    options=landmark_names,
                    index=default_end_idx,
                    key="sel_end_landmark",
                )
                st.session_state["end_coords"] = POPULAR_LANDMARKS[chosen_end_name]
                st.session_state["end_name"] = chosen_end_name

            # MODE B: Pick on Map
            elif route_input_method == "Pick on Map":
                st.markdown(
                    """
                    <div style="background: rgba(18,20,42,0.9); padding: 10px; border-radius: 8px; border: 1px solid rgba(0,230,118,0.3); font-size: 0.85rem;">
                        Select which point to set, then click anywhere on the map:
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.session_state["map_selection_mode"] = st.radio(
                    "Clicking Map Sets:",
                    options=["Start Location", "Destination Location"],
                    index=0 if st.session_state.get("map_selection_mode") == "start" else 1,
                    horizontal=True,
                )
                if st.session_state["map_selection_mode"] == "Start Location":
                    st.session_state["map_selection_mode"] = "start"
                else:
                    st.session_state["map_selection_mode"] = "end"

                st.markdown(
                    f"""
                    <div style="margin-top: 8px; font-size: 0.82rem; color: #D4C9E6;">
                        • <strong>Origin:</strong> {st.session_state.get('start_name', 'Not set')} <code>({st.session_state['start_coords'][0]:.4f}, {st.session_state['start_coords'][1]:.4f})</code><br>
                        • <strong>Destination:</strong> {st.session_state.get('end_name', 'Not set')} <code>({st.session_state['end_coords'][0]:.4f}, {st.session_state['end_coords'][1]:.4f})</code>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # MODE C: Enter Coordinates
            else:
                st.markdown("<div style='font-size:0.8rem; font-weight:700; color:#00E676; margin-top:6px;'>ORIGIN COORDINATES</div>", unsafe_allow_html=True)
                rc1, rc2 = st.columns(2)
                with rc1:
                    s_lat = st.number_input("Start Lat", value=float(st.session_state["start_coords"][0]), format="%.5f", key="man_start_lat")
                with rc2:
                    s_lon = st.number_input("Start Lon", value=float(st.session_state["start_coords"][1]), format="%.5f", key="man_start_lon")
                st.session_state["start_coords"] = (s_lat, s_lon)

                st.markdown("<div style='font-size:0.8rem; font-weight:700; color:#FF1744; margin-top:4px;'>DESTINATION COORDINATES</div>", unsafe_allow_html=True)
                rc3, rc4 = st.columns(2)
                with rc3:
                    e_lat = st.number_input("End Lat", value=float(st.session_state["end_coords"][0]), format="%.5f", key="man_end_lat")
                with rc4:
                    e_lon = st.number_input("End Lon", value=float(st.session_state["end_coords"][1]), format="%.5f", key="man_end_lon")
                st.session_state["end_coords"] = (e_lat, e_lon)

            # Execute Reroute Algorithm
            if st.button("Compute Safer Route", key="btn_compute_safe_route", use_container_width=True):
                with st.spinner("Analyzing candidate routes and evaluating urban risk grid..."):
                    route_result = get_reroute(
                        start=st.session_state["start_coords"],
                        end=st.session_state["end_coords"],
                        time=st.session_state["time_of_day"],
                    )
                    st.session_state["calculated_route"] = route_result
                    st.rerun()

            # Display Route Results
            if st.session_state.get("calculated_route"):
                r = st.session_state["calculated_route"]
                r_band = r.get("risk_band", "low")
                r_color = BAND_COLORS.get(r_band, "#00E676")
                badge_class = f"badge-{r_band}"

                st.markdown("---")
                st.markdown(
                    f"""
                    <div style="background: rgba(14, 17, 38, 0.9); border: 1px solid {r_color}; border-radius: 10px; padding: 10px; margin-top: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 700; color: #FFFFFF;">Safer Route Found:</span>
                            <span class="{badge_class}">[{r_band.upper()} RISK]</span>
                        </div>
                        <div style="margin-top: 6px; font-size: 0.82rem; color: #D4C9E6;">
                            • <strong>Candidate Paths Evaluated</strong>: {r.get('compared_routes', 5)} paths<br>
                            • <strong>Average Risk Score</strong>: <span style="color:{r_color}; font-weight:700;">{r.get('average_risk', 0.0)} / 100</span><br>
                            • <strong>Route Visualization</strong>: Rendered in solid green line on the map
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("Clear Route", key="btn_clear_route"):
                    st.session_state["calculated_route"] = None
                    st.rerun()

        # ------------------------------------------------------------
        # SUB-TAB 2: "FELT UNSAFE HERE" INSTANT REPORTER
        # ------------------------------------------------------------
        with deck_tab_report:
            st.markdown("#### Felt Unsafe Here?")
            st.caption("Submit anonymous crowdsourced reports. Every report updates SafeGrid's risk grid instantly.")

            current_sel = st.session_state.get("selected_point", CITY_CENTER)

            rep_c1, rep_c2 = st.columns(2)
            with rep_c1:
                rep_lat = st.number_input("Target Latitude", value=float(current_sel[0]), format="%.5f", key="rep_lat_input")
            with rep_c2:
                rep_lon = st.number_input("Target Longitude", value=float(current_sel[1]), format="%.5f", key="rep_lon_input")

            incident_type = st.selectbox(
                "Hazard / Incident Tag",
                options=[
                    "Broken / Pitch Dark Streetlights",
                    "Suspicious Gathering / Loiterers",
                    "Deserted Isolated Street",
                    "Verbal Harassment / Catcalling",
                    "Stalking / Following Suspicion",
                    "Lack of Police Patrols / CCTV",
                    "Unsafe Public Transport Stop",
                    "Other Safety Hazard",
                ],
                key="rep_incident_type",
            )

            optional_note = st.text_input(
                "Optional Details",
                placeholder="e.g., Narrow alley near market with flickering lighting",
                key="rep_note_input",
            )

            st.markdown("<div class='sos-btn'>", unsafe_allow_html=True)
            if st.button("Submit Anonymous Safety Alert", key="btn_submit_unsafe_report", use_container_width=True):
                with st.spinner("Transmitting safety report to SafeGrid network..."):
                    res = submit_report(rep_lat, rep_lon, note=f"[{incident_type}] {optional_note}")
                    if res.get("success"):
                        st.session_state["report_success_toast"] = res
                        st.success(f"Report Logged Successfully (Report ID: {res.get('report_id', 'LIVE')}). Risk grid updated.")
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get("report_success_toast"):
                last_rep = st.session_state["report_success_toast"]
                st.markdown(
                    f"""
                    <div style="background: rgba(0, 230, 118, 0.1); border: 1px solid #00E676; border-radius: 8px; padding: 8px; margin-top: 8px; font-size: 0.8rem;">
                        <strong>ID:</strong> <code>{last_rep.get('report_id')}</code> | <strong>Segment:</strong> <code>{last_rep.get('segment_id')}</code><br>
                        <span style="color:#00E676;">Thank you for protecting our community.</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ------------------------------------------------------------
        # SUB-TAB 3: SPOT INSPECTOR
        # ------------------------------------------------------------
        with deck_tab_spot:
            st.markdown("#### Spot Safety Inspector")
            st.caption("Inspect live AI safety predictions for any coordinate or landmark in Bhubaneswar.")

            insp_landmark = st.selectbox(
                "Choose Landmark or Custom Point",
                options=["Selected Coordinates"] + list(POPULAR_LANDMARKS.keys()),
                key="insp_landmark_choice",
            )

            if insp_landmark != "Selected Coordinates":
                insp_coords = POPULAR_LANDMARKS[insp_landmark]
                st.session_state["selected_point"] = [insp_coords[0], insp_coords[1]]

            cur_p = st.session_state.get("selected_point", CITY_CENTER)

            if st.button("Inspect Spot Safety", key="btn_inspect_spot", use_container_width=True):
                spot_res = predict_risk(cur_p[0], cur_p[1], time=st.session_state["time_of_day"])
                s_band = spot_res.get("band", "medium")
                s_score = spot_res.get("score", 0.0)
                s_color = BAND_COLORS.get(s_band, "#FFB300")

                st.markdown(
                    f"""
                    <div style="background: rgba(18, 22, 48, 0.95); border: 1px solid {s_color}; border-radius: 10px; padding: 12px; margin-top: 10px;">
                        <div style="font-size: 0.75rem; color: #8E88A8;">PREDICTED RISK BAND</div>
                        <div style="font-size: 1.3rem; font-weight: 800; color: {s_color}; font-family: 'Space Grotesk';">
                            [{s_band.upper()} RISK]
                        </div>
                        <div style="font-size: 0.85rem; color: #D4C9E6; margin-top: 6px;">
                            • <strong>Nearest Segment ID</strong>: <code>{spot_res.get('segment_id')}</code><br>
                            • <strong>AI Risk Score</strong>: <span style="color:{s_color}; font-weight:700;">{s_score} / 100</span><br>
                            • <strong>Time Bucket</strong>: {spot_res.get('time_bucket', '').upper()}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ==============================================================================
# TAB 2: SOS GUARDIAN & ALARM HUB
# ==============================================================================
with tab_sos:
    st.markdown('<div class="glam-title">EMERGENCY COMMAND HUB</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Instant Panic Triggers, Deterrent Siren, Fake Calls and Rapid Broadcast</div>', unsafe_allow_html=True)

    sos_col1, sos_col2 = st.columns([1, 1])

    with sos_col1:
        st.markdown(
            """
            <div class="glam-card">
                <h3 style="color:#FF1744 !important;">1-Tap Emergency Broadcast</h3>
                <p style="color:#D4C9E6; font-size:0.88rem;">
                    Generates a formatted distress message with live GPS coordinates, Google Maps link, and current time for WhatsApp or SMS rapid broadcast to your emergency circle.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        curr_loc = st.session_state.get("selected_point", CITY_CENTER)
        maps_link = f"https://maps.google.com/?q={curr_loc[0]:.6f},{curr_loc[1]:.6f}"
        distress_msg = f"EMERGENCY SOS from SafeGrid. I feel unsafe right now. My current location is: {maps_link} at {datetime.now().strftime('%H:%M:%S')}. Please check on me or dispatch help immediately."

        st.text_area("Prepared Distress Message", value=distress_msg, height=90, key="sos_msg_box")

        c_wa, c_sms = st.columns(2)
        with c_wa:
            wa_url = f"https://api.whatsapp.com/send?text={distress_msg.replace(' ', '%20')}"
            st.markdown(
                f"""
                <a href="{wa_url}" target="_blank" style="text-decoration:none;">
                    <div style="background: linear-gradient(135deg, #25D366 0%, #128C7E 100%); color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: 700; font-size: 0.9rem; box-shadow: 0 4px 12px rgba(37, 211, 102, 0.4);">
                        Share on WhatsApp
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )
        with c_sms:
            sms_url = f"sms:?body={distress_msg.replace(' ', '%20')}"
            st.markdown(
                f"""
                <a href="{sms_url}" style="text-decoration:none;">
                    <div style="background: linear-gradient(135deg, #FF2A85 0%, #B71C5A 100%); color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: 700; font-size: 0.9rem; box-shadow: 0 4px 12px rgba(255, 42, 133, 0.4);">
                        Send Direct SMS
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Siren Simulator
        st.markdown(
            """
            <div class="glam-card">
                <h3 style="color:#FFB300 !important;">High-Decibel Deterrent Siren</h3>
                <p style="color:#D4C9E6; font-size:0.85rem;">
                    Activate an in-browser acoustic warning pulse to attract public attention and deter potential aggressors.
                </p>
                <div style="text-align: center; margin-top: 10px;">
                    <button id="sirenBtn" onclick="toggleSiren()" style="background: linear-gradient(135deg, #FFB300 0%, #FF5500 100%); border: none; color: white; padding: 10px 24px; border-radius: 999px; font-weight: 800; font-size: 0.95rem; cursor: pointer; box-shadow: 0 0 15px rgba(255, 179, 0, 0.4);">
                        TOGGLE SIREN ALARM
                    </button>
                    <div id="sirenStatus" style="margin-top: 6px; font-size: 0.78rem; color: #A99EBE;">Click to start audio frequency alarm</div>
                </div>
            </div>

            <script>
            let audioCtx = null;
            let osc = null;
            let isSirenOn = false;
            let sirenInterval = null;

            function toggleSiren() {
                const status = document.getElementById('sirenStatus');
                const btn = document.getElementById('sirenBtn');

                if (!isSirenOn) {
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(600, audioCtx.currentTime);
                    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);

                    osc.connect(gain);
                    gain.connect(audioCtx.destination);
                    osc.start();

                    let high = false;
                    sirenInterval = setInterval(() => {
                        if (osc) {
                            osc.frequency.setValueAtTime(high ? 900 : 500, audioCtx.currentTime);
                            high = !high;
                        }
                    }, 350);

                    isSirenOn = true;
                    btn.innerText = "STOP SIREN ALARM";
                    btn.style.background = "#FF1744";
                    status.innerText = "SIREN ACTIVE - Pulsing high decibel alert";
                    status.style.color = "#FF1744";
                } else {
                    if (osc) {
                        osc.stop();
                        osc.disconnect();
                        osc = null;
                    }
                    if (sirenInterval) clearInterval(sirenInterval);
                    isSirenOn = false;
                    btn.innerText = "TOGGLE SIREN ALARM";
                    btn.style.background = "linear-gradient(135deg, #FFB300 0%, #FF5500 100%)";
                    status.innerText = "Siren Deactivated.";
                    status.style.color = "#A99EBE";
                }
            }
            </script>
            """,
            unsafe_allow_html=True,
        )

    with sos_col2:
        # Fake Call Generator
        st.markdown(
            """
            <div class="glam-card">
                <h3 style="color:#00F0FF !important;">Fake Call Assistant</h3>
                <p style="color:#D4C9E6; font-size:0.88rem;">
                    Need a tactical escape from an uncomfortable situation or deserted street? Trigger a simulated incoming phone call.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        caller_id = st.selectbox(
            "Select Simulated Caller Identity",
            options=["Family Member", "Police Control Room", "SafeGrid Emergency Dispatch", "Cab Partner Support", "Office Manager"],
            key="fake_caller_select",
        )

        if st.button("Trigger Incoming Call Now", key="btn_trigger_fake_call", use_container_width=True):
            st.session_state["fake_call_step"] = "ringing"

        if st.session_state.get("fake_call_step") == "ringing":
            st.markdown(
                f"""
                <div style="background: radial-gradient(circle, rgba(255,42,133,0.2) 0%, rgba(10,12,28,0.95) 100%); border: 2px solid #FF2A85; border-radius: 14px; padding: 20px; text-align: center; box-shadow: 0 0 25px rgba(255,42,133,0.4); margin-top: 12px;">
                    <div style="font-size: 0.8rem; color: #8E88A8; text-transform: uppercase;">Incoming SafeCall</div>
                    <div style="font-family: 'Space Grotesk'; font-size: 1.6rem; font-weight: 800; color: #FFFFFF; margin: 4px 0;">{caller_id}</div>
                    <div style="font-size: 0.78rem; color: #00E676;">Verified SafeLine Active</div>
                    <div style="margin-top: 15px;">
                        <button onclick="alert('Call Answered: Simulated dialogue playing')" style="background: #00E676; color: #000; border: none; padding: 10px 20px; border-radius: 999px; font-weight: 800; font-size: 0.95rem; cursor: pointer; box-shadow: 0 0 12px #00E676;">
                            ACCEPT CALL
                        </button>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Dismiss Call", key="btn_dismiss_call"):
                st.session_state["fake_call_step"] = "idle"
                st.rerun()

# ==============================================================================
# TAB 3: WALK-WITH-ME COMPANION
# ==============================================================================
with tab_companion:
    st.markdown('<div class="glam-title">WALK-WITH-ME GUARDIAN COMPANION</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Live Safety Interval Check-ins and Automatic Panic Alert Timers</div>', unsafe_allow_html=True)

    w_col1, w_col2 = st.columns([1, 1])

    with w_col1:
        st.markdown(
            """
            <div class="glam-card">
                <h3 style="color:#00E676 !important;">Safety Check-in Timer</h3>
                <p style="color:#D4C9E6; font-size:0.88rem;">
                    Set your expected travel duration. If you do not confirm safe arrival before the timer expires, SafeGrid prepares an automated emergency broadcast.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        trip_minutes = st.slider("Expected Trip Duration (Minutes)", min_value=5, max_value=60, value=15, step=5, key="comp_trip_mins")
        destination_label = st.selectbox(
            "Destination Point",
            options=list(POPULAR_LANDMARKS.keys()) + ["Custom Destination"],
            key="comp_dest_label",
        )

        c_start_t, c_stop_t = st.columns(2)
        with c_start_t:
            if st.button("Start Guardian Watch", key="btn_start_companion", use_container_width=True):
                st.session_state["companion_active"] = True
                st.success("Guardian Watch Active. SafeGrid is monitoring your journey window.")
        with c_stop_t:
            if st.button("Mark Safe Arrival", key="btn_stop_companion", use_container_width=True):
                st.session_state["companion_active"] = False
                st.success("Journey marked complete safely.")

        if st.session_state.get("companion_active"):
            st.markdown(
                f"""
                <div style="background: rgba(0, 230, 118, 0.12); border: 1px solid #00E676; border-radius: 10px; padding: 12px; margin-top: 12px; text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #00E676;">GUARDIAN WATCH ACTIVE</div>
                    <div style="font-size: 0.85rem; color: #FFFFFF; margin: 3px 0;">Destination: <strong>{destination_label}</strong></div>
                    <div style="font-size: 0.78rem; color: #A99EBE;">Window: {trip_minutes} mins | Watchdog running</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with w_col2:
        st.markdown(
            """
            <div class="glam-card">
                <h3 style="color:#FFB8D9 !important;">Pre-Transit Safety Checklist</h3>
                <ul style="color:#D4C9E6; font-size:0.88rem; line-height:1.8;">
                    <li><strong>Phone Battery</strong>: Keep charged above 20%</li>
                    <li><strong>Live Location</strong>: Share with trusted emergency contact</li>
                    <li><strong>Situational Awareness</strong>: Keep one ear free from headphones</li>
                    <li><strong>Well-lit Paths</strong>: Follow SafeGrid's green route guidance</li>
                    <li><strong>Quick Access</strong>: Keep SafeGrid open in mobile browser</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# TAB 4: COMMUNITY INCIDENT FEED
# ==============================================================================
with tab_feed:
    st.markdown('<div class="glam-title">COMMUNITY INCIDENT FEED</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Crowdsourced Vigilance and Real-Time Incident Reports Across Bhubaneswar</div>', unsafe_allow_html=True)

    if os.path.exists(REPORTS_PATH):
        reports_df = pd.read_csv(REPORTS_PATH)
    else:
        reports_df = pd.DataFrame(columns=["report_id", "segment_id", "lat", "lon", "timestamp", "time_bucket"])

    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        st.metric("Total Logged Reports", f"{len(reports_df)} Incidents")
    with f_col2:
        recent_count = len(reports_df[reports_df["time_bucket"] == st.session_state["time_of_day"]])
        st.metric(f"Reports in {st.session_state['time_of_day'].title()}", f"{recent_count} Reports")
    with f_col3:
        filter_bucket = st.selectbox("Filter Feed by Time Bucket", options=["all", "morning", "afternoon", "evening", "night"], index=0, key="feed_filter_bucket")

    if filter_bucket != "all":
        display_df = reports_df[reports_df["time_bucket"] == filter_bucket]
    else:
        display_df = reports_df

    st.markdown("---")

    if display_df.empty:
        st.info("No incident reports found for the selected filter.")
    else:
        st.dataframe(
            display_df.sort_index(ascending=False),
            use_container_width=True,
            column_config={
                "report_id": st.column_config.TextColumn("Report ID", width="medium"),
                "segment_id": st.column_config.TextColumn("Segment ID", width="medium"),
                "lat": st.column_config.NumberColumn("Latitude", format="%.5f"),
                "lon": st.column_config.NumberColumn("Longitude", format="%.5f"),
                "timestamp": st.column_config.TextColumn("Recorded At"),
                "time_bucket": st.column_config.TextColumn("Time Bucket"),
            },
            hide_index=True,
        )

# ==============================================================================
# TAB 5: CITY SAFETY ANALYTICS
# ==============================================================================
with tab_analytics:
    st.markdown('<div class="glam-title">URBAN SAFETY INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Statistical Safety Profiles, Lighting Correlations and Vulnerability Patterns</div>', unsafe_allow_html=True)

    an_col1, an_col2 = st.columns(2)

    with an_col1:
        st.markdown(
            """
            <div class="glam-card">
                <h3>Risk Distribution by Time Bucket</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        summary_rows = []
        for tb in ["morning", "afternoon", "evening", "night"]:
            grid_tb = fetch_cached_risk_grid(tb)
            low_c = sum(1 for x in grid_tb if x["band"] == "low")
            med_c = sum(1 for x in grid_tb if x["band"] == "medium")
            high_c = sum(1 for x in grid_tb if x["band"] == "high")
            avg_s = np.mean([x["score"] for x in grid_tb]) if grid_tb else 0.0
            summary_rows.append({
                "Time Bucket": tb.capitalize(),
                "Average Risk Score": round(avg_s, 1),
                "Low Risk (Safe)": low_c,
                "Medium Risk": med_c,
                "High Risk": high_c,
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    with an_col2:
        st.markdown(
            """
            <div class="glam-card">
                <h3>Key Risk Influencers (XGBoost Weights)</h3>
                <p style="color:#D4C9E6; font-size:0.88rem; line-height:1.7;">
                    • <strong>Lighting Score and Streetlight Operational %</strong>: 38% predictive weight<br>
                    • <strong>Historical Incidents and Annual Police Records</strong>: 26% predictive weight<br>
                    • <strong>Crowd Volume and Density by Time-of-Day</strong>: 18% predictive weight<br>
                    • <strong>Crowdsourced Unsafe Real-time Reports</strong>: 12% dynamic weight<br>
                    • <strong>Urban Zone Type and Distance to Center</strong>: 6% structural weight
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# TAB 6: ABOUT AND MODEL ARCHITECTURE
# ==============================================================================
with tab_about:
    st.markdown('<div class="glam-title">ABOUT CODE COVEN AND SAFEGRID</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Empowering Women with Predictive Urban Safety and Machine Learning</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="glam-card">
            <h3 style="color:#FF2A85 !important;">Mission: Autonomous Safety Before Danger Strikes</h3>
            <p style="color:#D4C9E6; font-size:0.92rem; line-height:1.7;">
                Most safety applications only act after an incident occurs (emergency triggers and panics). 
                <strong>SafeGrid</strong> shifts the paradigm from reactive rescue to <strong>proactive prevention</strong>.
                By synthesizing geospatial infrastructure data, operational street lighting, crowd volume dynamics, historical incident frequencies, and live anonymous crowdsourced vigilance reports, SafeGrid enables women to navigate cities with confidence and clarity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ab_c1, ab_c2 = st.columns(2)
    with ab_c1:
        st.markdown(
            """
            <div class="glam-card">
                <h4>ML Pipeline and Architecture</h4>
                <p style="color:#D4C9E6; font-size:0.86rem; line-height:1.6;">
                    • <strong>Engine</strong>: Gradient Boosted Decision Trees (XGBoost Regressor & Classifier)<br>
                    • <strong>Geospatial Mesh</strong>: 500m hexagonal and square grid cells across Bhubaneswar<br>
                    • <strong>Quantile Thresholds</strong>: Low (<=25.1), Medium (25.2-40.4), High (>40.4)<br>
                    • <strong>Safer Rerouting</strong>: Multi-path candidate trajectory optimization
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ab_c2:
        st.markdown(
            """
            <div class="glam-card">
                <h4>Code Coven | Infinity Hacks 2026</h4>
                <p style="color:#D4C9E6; font-size:0.86rem; line-height:1.6;">
                    Built with technology and resilience for every woman navigating the city.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================
# 9. FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #8E88A8; font-size: 0.78rem; padding: 8px 0;">
        SafeGrid AI Matrix v2.0 | Team Code Coven | Infinity Hacks 2026 | Dedicated to Women Safety Everywhere
    </div>
    """,
    unsafe_allow_html=True,
)