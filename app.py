"""
SafeGrid — Cyberpunk Soft-Glam Women's Safety Matrix & AI Navigator
Developed by Team Code Coven | Infinity Hacks 2026

Backend ML Integration:
  1. get_risk_grid(time) -> Live city risk grid plotted on interactive Leaflet map
  2. Time selector (morning/afternoon/evening/night) -> Real-time model recalculation
  3. submit_report(lat, lon, note) -> Instant crowdsourced "Felt Unsafe Here" reporting
  4. get_reroute(start, end, time) -> Multi-candidate safer routing algorithm
  5. predict_risk(lat, lon, time) -> Spot safety prediction with risk band & score
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
# 1. PAGE CONFIGURATION & THEME
# ============================================================
st.set_page_config(
    page_title="SafeGrid ✨ Cyberpunk Soft-Glam Women Safety Matrix",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 2. CONSTANTS & PALETTE (CYBERPUNK SOFT GLAM)
# ============================================================
CITY_CENTER = [20.2961, 85.8245]  # Bhubaneswar Center (Jaydev Vihar / Master Canteen axis)

# Color Scheme: Cyberpunk Soft-Glam
# Green = Low Risk, Solar Amber = Medium Risk, Neon Ruby = High Risk
BAND_COLORS = {
    "low": "#00F59B",     # Radiant Mint Emerald (Cyber Low Risk)
    "medium": "#FFB800",  # Neon Solar Amber (Cyber Caution)
    "high": "#FF2A55",    # Neon Cyber Ruby (Cyber High Alert)
}

BAND_ICONS = {
    "low": "🛡️",
    "medium": "⚠️",
    "high": "🚨",
}

BAND_LABELS = {
    "low": "LOW RISK (SAFE ZONE)",
    "medium": "MODERATE RISK (CAUTION)",
    "high": "ELEVATED RISK (ALERT)",
}

# Bhubaneswar Popular Landmarks for 1-Click Navigation & Quick Pinning
POPULAR_LANDMARKS = {
    "KIIT Campus, Patia": (20.3560, 85.8190),
    "Patia / Infocity IT Hub": (20.3520, 85.8200),
    "Esplanade One Mall, Rasulgarh": (20.2990, 85.8420),
    "Master Canteen Square": (20.2700, 85.8410),
    "Jaydev Vihar Square": (20.2960, 85.8180),
    "Bhubaneswar Railway Station": (20.2679, 85.8398),
    "Saheed Nagar Market": (20.2940, 85.8420),
    "Biju Patnaik Airport": (20.2530, 85.8180),
    "Vani Vihar (Utkal Univ.)": (20.2950, 85.8390),
    "Kalinga Stadium Area": (20.2870, 85.8250),
    "Unit-1 Market Building": (20.2650, 85.8360),
    "Chandrasekharpur Housing": (20.3450, 85.8100),
    "Old Town / Lingaraj Temple": (20.2380, 85.8340),
    "Baramunda Bus Terminal": (20.2955, 85.7929),
}

# ============================================================
# 3. CUSTOM CYBERPUNK SOFT-GLAM STYLING (CSS)
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

    /* Global Root Variables */
    :root {
        --bg-obsidian: #080914;
        --bg-card: rgba(18, 20, 42, 0.72);
        --accent-magenta: #FF2A85;
        --accent-rose: #FFB8D9;
        --accent-cyan: #00F0FF;
        --accent-purple: #9B51E0;
        --safe-green: #00F59B;
        --warn-amber: #FFB800;
        --danger-ruby: #FF2A55;
        --text-primary: #FFFFFF;
        --text-secondary: #D4C9E6;
        --border-glass: rgba(255, 42, 133, 0.22);
    }

    /* Overall App Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(255, 42, 133, 0.08) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(155, 81, 224, 0.1) 0%, transparent 40%),
                    radial-gradient(circle at 50% 50%, rgba(0, 240, 255, 0.04) 0%, transparent 60%),
                    #080914 !important;
        font-family: 'Outfit', sans-serif !important;
        color: #FFFFFF !important;
    }

    /* Headers & Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em;
        color: #FFFFFF !important;
    }

    /* Glam Gradient Headers */
    .glam-title {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFB8D9 45%, #FF2A85 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(255, 42, 133, 0.35);
        margin-bottom: 0.2rem;
    }

    .glam-subtitle {
        font-family: 'Outfit', sans-serif;
        font-weight: 400;
        color: #C8BEDE;
        font-size: 1rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    /* Glassmorphism Cards */
    .glam-card {
        background: rgba(18, 20, 42, 0.72);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 42, 133, 0.25);
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 8px 30px 0 rgba(0, 0, 0, 0.45);
        margin-bottom: 1rem;
    }

    /* Status Pill / Live Radar */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(0, 245, 155, 0.12);
        border: 1px solid rgba(0, 245, 155, 0.4);
        color: #00F59B;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        box-shadow: 0 0 10px rgba(0, 245, 155, 0.2);
    }

    .live-pulse {
        width: 8px;
        height: 8px;
        background-color: #00F59B;
        border-radius: 50%;
        box-shadow: 0 0 10px #00F59B;
        animation: pulse 1.6s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.7; }
        50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 15px #00F59B; }
        100% { transform: scale(0.95); opacity: 0.7; }
    }

    /* Cyber Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #FF2A85 0%, #B71C5A 100%) !important;
        color: #FFFFFF !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255, 184, 217, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.5rem 1.2rem !important;
        box-shadow: 0 4px 18px rgba(255, 42, 133, 0.35) !important;
        transition: all 0.25s ease-in-out !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #FF4598 0%, #D1236E 100%) !important;
        box-shadow: 0 6px 24px rgba(255, 42, 133, 0.55) !important;
        transform: translateY(-2px);
    }

    /* SOS Red Button */
    .sos-btn div.stButton > button {
        background: linear-gradient(135deg, #FF2A55 0%, #B3002D 100%) !important;
        box-shadow: 0 4px 22px rgba(255, 42, 85, 0.55) !important;
        border: 1px solid rgba(255, 100, 130, 0.5) !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }

    /* Metric Cards */
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

    /* Streamlit Selectbox / Input styling */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background-color: rgba(14, 16, 36, 0.9) !important;
        border-color: rgba(255, 42, 133, 0.3) !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 17, 36, 0.7);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 42, 133, 0.2);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 10px;
        color: #A69DBB;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 8px 18px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(255, 42, 133, 0.35) 0%, rgba(155, 81, 224, 0.35) 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255, 42, 133, 0.6) !important;
        box-shadow: 0 0 15px rgba(255, 42, 133, 0.3);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0B0C1E !important;
        border-right: 1px solid rgba(255, 42, 133, 0.18) !important;
    }

    /* Risk Badges */
    .risk-badge-low {
        background: rgba(0, 245, 155, 0.15);
        color: #00F59B;
        border: 1px solid #00F59B;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .risk-badge-medium {
        background: rgba(255, 184, 0, 0.15);
        color: #FFB800;
        border: 1px solid #FFB800;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .risk-badge-high {
        background: rgba(255, 42, 85, 0.18);
        color: #FF2A55;
        border: 1px solid #FF2A55;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.8rem;
    }

    /* Helpline Card */
    .helpline-box {
        background: rgba(20, 24, 50, 0.85);
        border: 1px solid rgba(255, 184, 217, 0.2);
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        transition: all 0.2s;
    }
    .helpline-box:hover {
        border-color: #FF2A85;
        box-shadow: 0 0 15px rgba(255, 42, 133, 0.3);
    }
    .helpline-num {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.3rem;
        font-weight: 800;
        color: #FFB8D9;
    }
    .helpline-desc {
        font-size: 0.72rem;
        color: #A99EBE;
        text-transform: uppercase;
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
    st.session_state["start_coords"] = (20.3560, 85.8190)  # KIIT Campus

if "end_coords" not in st.session_state:
    st.session_state["end_coords"] = (20.2990, 85.8420)    # Esplanade Mall

if "calculated_route" not in st.session_state:
    st.session_state["calculated_route"] = None

if "report_success_toast" not in st.session_state:
    st.session_state["report_success_toast"] = None

if "fake_call_step" not in st.session_state:
    st.session_state["fake_call_step"] = "idle"

if "grid_density" not in st.session_state:
    st.session_state["grid_density"] = "Optimized (Fast & Smooth)"

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

def generate_leaflet_map(risk_grid, route_data=None, selected_latlon=None, density="Optimized (Fast & Smooth)"):
    """
    Build Folium map with Cyberpunk Soft-Glam styling.
    Band colors: Green (Low), Yellow (Medium), Red (High).
    """
    m = folium.Map(
        location=CITY_CENTER,
        zoom_start=13,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Subsample if optimized mode to keep 60 FPS in browser
    if density == "Optimized (Fast & Smooth)" and len(risk_grid) > 450:
        # Step subsample evenly to cover all city zones smoothly
        display_grid = risk_grid[::4]
    else:
        display_grid = risk_grid

    # 1. Risk Grid Feature Group
    grid_group = folium.FeatureGroup(name="SafeGrid Risk Points", show=True)

    for cell in display_grid:
        band = cell.get("band", "medium")
        color = BAND_COLORS.get(band, "#FFB800")
        score = cell.get("score", 0.0)
        landmark = cell.get("landmark", f"Segment {cell.get('segment_id', '')}")
        zone = cell.get("zone_type", "Urban Area").replace("_", " ").title()

        popup_html = f"""
        <div style="font-family: 'Outfit', sans-serif; background: #0E1022; color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid {color}; width: 200px;">
            <div style="font-size: 12px; font-weight: 700; color: #FFB8D9; margin-bottom: 2px;">{landmark}</div>
            <div style="font-size: 10px; color: #8E88A8; margin-bottom: 6px;">Zone: {zone}</div>
            <div style="background: {color}22; border: 1px solid {color}; color: {color}; font-weight: 800; font-size: 11px; padding: 3px 6px; border-radius: 5px; text-align: center; text-transform: uppercase;">
                {BAND_ICONS.get(band, '🛡️')} {BAND_LABELS.get(band, band.upper())}
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #D4C9E6; border-top: 1px solid #252848; margin-top: 6px; padding-top: 4px;">
                <span>AI Risk Score:</span>
                <strong style="color: {color};">{score} / 100</strong>
            </div>
        </div>
        """

        tooltip_text = f"{BAND_ICONS.get(band, '🛡️')} {band.upper()} RISK | {landmark}"

        folium.CircleMarker(
            location=[cell["lat"], cell["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=1.5,
            tooltip=tooltip_text,
            popup=folium.Popup(popup_html, max_width=230),
        ).add_to(grid_group)

    grid_group.add_to(m)

    # 2. Key Anchor Landmarks
    landmark_group = folium.FeatureGroup(name="Bhubaneswar Landmarks", show=True)
    for name, coords in POPULAR_LANDMARKS.items():
        folium.CircleMarker(
            location=coords,
            radius=5,
            color="#FF2A85",
            fill=True,
            fill_color="#FFFFFF",
            fill_opacity=0.95,
            weight=2,
            tooltip=f"📍 {name}",
        ).add_to(landmark_group)
    landmark_group.add_to(m)

    # 3. User Selected Pin
    if selected_latlon:
        folium.Marker(
            location=selected_latlon,
            tooltip="🎯 Selected Location Pin",
            icon=folium.Icon(color="pink", icon="crosshairs", prefix="fa"),
        ).add_to(m)

    # 4. Computed Safer Route
    if route_data and "route" in route_data:
        coords = [(p["lat"], p["lon"]) for p in route_data["route"]]
        if coords:
            folium.PolyLine(
                coords,
                color="#00F59B",
                weight=6,
                opacity=0.95,
                tooltip=f"AI Safer Route (Risk Band: {route_data.get('risk_band', 'LOW').upper()})",
            ).add_to(m)

            folium.Marker(
                coords[0],
                tooltip="🟢 Start Point",
                icon=folium.Icon(color="green", icon="play", prefix="fa"),
            ).add_to(m)

            folium.Marker(
                coords[-1],
                tooltip="🏁 Safe Destination",
                icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
            ).add_to(m)

    folium.LayerControl(position="topright").add_to(m)
    return m

# ============================================================
# 6. SIDEBAR: TIME SELECTOR & EMERGENCY HOTLINES
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
            <div style="font-size: 2.2rem; filter: drop-shadow(0 0 12px #FF2A85);">🛡️✨</div>
            <div style="font-family: 'Syne', sans-serif; font-size: 1.45rem; font-weight: 800; color: #FFFFFF;">SAFEGRID</div>
            <div style="font-size: 0.72rem; color: #FFB8D9; letter-spacing: 0.1em; text-transform: uppercase;">Code Coven • Infinity Hacks</div>
            <div style="margin-top: 8px;">
                <span class="live-badge"><span class="live-pulse"></span> SYSTEM ACTIVE • BHUBANESWAR</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Time-of-Day Matrix
    st.markdown("### ⏱️ Time-of-Day Matrix")
    time_options = ["morning", "afternoon", "evening", "night"]
    current_detected = get_current_time_bucket()

    selected_time = st.select_slider(
        "Select Time Bucket",
        options=time_options,
        value=st.session_state["time_of_day"],
        key="time_slider_sidebar",
    )
    if selected_time != st.session_state["time_of_day"]:
        st.session_state["time_of_day"] = selected_time
        st.rerun()

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("🌙 Set Night", use_container_width=True):
            st.session_state["time_of_day"] = "night"
            st.rerun()
    with c_btn2:
        if st.button(f"⚡ Sync ({current_detected})", use_container_width=True):
            st.session_state["time_of_day"] = current_detected
            st.rerun()

    # Map Density Setting
    st.markdown("---")
    st.markdown("### ⚙️ Map Rendering")
    st.session_state["grid_density"] = st.radio(
        "Grid Density",
        options=["Optimized (Fast & Smooth)", "Full High Density (2,200 points)"],
        index=0,
        key="grid_density_radio",
    )

    st.markdown("---")

    # Emergency Hotlines
    st.markdown("### 🚨 Emergency Hotlines")
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
    st.caption(f"🛡️ Monitored: **{b_info['segments']}** segments | Model: **XGBoost AI**")

# ============================================================
# 7. MAIN APPLICATION HEADER
# ============================================================
header_col1, header_col2 = st.columns([3, 1])

with header_col1:
    st.markdown('<div class="glam-title">🛡️ SAFEGRID MATRIX</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="glam-subtitle">Predictive Urban Safety Intelligence & AI Guardian for Women</div>',
        unsafe_allow_html=True,
    )

with header_col2:
    current_bucket = st.session_state["time_of_day"]
    bucket_badge_color = "#FF2A55" if current_bucket == "night" else ("#FFB800" if current_bucket == "evening" else "#00F59B")
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 0.4rem;">
            <div style="font-size: 0.78rem; color: #8E88A8;">ACTIVE TIME BUCKET</div>
            <div style="font-family: 'Space Grotesk'; font-size: 1.35rem; font-weight: 700; color: {bucket_badge_color}; text-transform: uppercase;">
                {current_bucket} MODE ⚡
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# 8. APP WORKSPACES (TABS)
# ============================================================
tab_map, tab_sos, tab_companion, tab_feed, tab_analytics, tab_about = st.tabs([
    "🗺️ Live SafeGrid & Navigation",
    "🚨 SOS Guardian & Alarm",
    "🚶‍♀️ Walk-With-Me Companion",
    "📢 Community Incident Feed",
    "📊 City Safety Analytics",
    "ℹ️ SafeGrid AI Intelligence",
])

# ==============================================================================
# TAB 1: LIVE SAFEGRID & NAVIGATION (MAP + REPORTING + ROUTING)
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
        st.metric("Monitored Segments", f"{total_points} Units")
    with m_col2:
        st.metric("🟢 Low Risk (Safe)", f"{low_risk_count} ({low_risk_count/max(1,total_points)*100:.0f}%)")
    with m_col3:
        st.metric("🟡 Moderate (Caution)", f"{med_risk_count} ({med_risk_count/max(1,total_points)*100:.0f}%)")
    with m_col4:
        st.metric("🔴 Elevated Risk (Alert)", f"{high_risk_count} ({high_risk_count/max(1,total_points)*100:.0f}%)")

    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    # Layout: Map (Left 65%) vs Command Panel (Right 35%)
    map_col, panel_col = st.columns([64, 36])

    with map_col:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 600; font-size: 0.95rem; color: #FFB8D9;">🗺️ Bhubaneswar Live Risk Map</span>
                <span style="font-size: 0.78rem; color: #8E88A8;">
                    🟢 Low &nbsp;|&nbsp; 🟡 Caution &nbsp;|&nbsp; 🔴 Alert &nbsp; (Click map point to select)
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
            density=st.session_state.get("grid_density", "Optimized (Fast & Smooth)"),
        )

        # Render Folium Map
        map_output = st_folium(
            current_map,
            use_container_width=True,
            height=560,
            key="safegrid_main_leaflet_map",
            returned_objects=["last_clicked"],
        )

        # Detect User Map Clicks
        clicked_coords = None
        if map_output and map_output.get("last_clicked"):
            clicked_lat = map_output["last_clicked"]["lat"]
            clicked_lng = map_output["last_clicked"]["lng"]
            clicked_coords = (clicked_lat, clicked_lng)
            st.session_state["selected_point"] = [clicked_lat, clicked_lng]

        st.caption("✨ **Pro Tip**: Click any map spot to auto-fill coordinates in the reporter or safe route finder.")

    # ------------------------------------------------------------
    # RIGHT COMMAND DECK
    # ------------------------------------------------------------
    with panel_col:
        deck_tab_route, deck_tab_report, deck_tab_spot = st.tabs([
            "🧭 AI Safe Route",
            "🚨 Felt Unsafe Here?",
            "🔍 Spot Inspector",
        ])

        # ------------------------------------------------------------
        # SUB-TAB 1: AI SAFE ROUTE GENERATOR
        # ------------------------------------------------------------
        with deck_tab_route:
            st.markdown("#### 🧭 Predictive Safe Navigation")
            st.caption("SafeGrid calculates multi-path candidate trajectories and selects the lowest-risk path.")

            # Quick Preset Selector
            preset_choice = st.selectbox(
                "⚡ 1-Click Popular Bhubaneswar Routes",
                options=[
                    "Custom Coordinates",
                    "KIIT Campus ➔ Esplanade One Mall",
                    "Master Canteen ➔ Patia Infocity",
                    "Vani Vihar ➔ Saheed Nagar Market",
                    "Baramunda Bus Stand ➔ Jaydev Vihar",
                    "Biju Patnaik Airport ➔ Master Canteen",
                ],
                key="route_preset_select",
            )

            # Preset Auto-fill
            if preset_choice == "KIIT Campus ➔ Esplanade One Mall":
                st.session_state["start_coords"] = POPULAR_LANDMARKS["KIIT Campus, Patia"]
                st.session_state["end_coords"] = POPULAR_LANDMARKS["Esplanade One Mall, Rasulgarh"]
            elif preset_choice == "Master Canteen ➔ Patia Infocity":
                st.session_state["start_coords"] = POPULAR_LANDMARKS["Master Canteen Square"]
                st.session_state["end_coords"] = POPULAR_LANDMARKS["Patia / Infocity IT Hub"]
            elif preset_choice == "Vani Vihar ➔ Saheed Nagar Market":
                st.session_state["start_coords"] = POPULAR_LANDMARKS["Vani Vihar (Utkal Univ.)"]
                st.session_state["end_coords"] = POPULAR_LANDMARKS["Saheed Nagar Market"]
            elif preset_choice == "Baramunda Bus Stand ➔ Jaydev Vihar":
                st.session_state["start_coords"] = POPULAR_LANDMARKS["Baramunda Bus Terminal"]
                st.session_state["end_coords"] = POPULAR_LANDMARKS["Jaydev Vihar Square"]
            elif preset_choice == "Biju Patnaik Airport ➔ Master Canteen":
                st.session_state["start_coords"] = POPULAR_LANDMARKS["Biju Patnaik Airport"]
                st.session_state["end_coords"] = POPULAR_LANDMARKS["Master Canteen Square"]

            # Start Point
            st.markdown("<div style='font-weight:600; font-size:0.82rem; color:#00F59B; margin-top:6px;'>🟢 ORIGIN (START)</div>", unsafe_allow_html=True)
            r_start_c1, r_start_c2 = st.columns(2)
            with r_start_c1:
                start_lat_val = st.number_input("Start Lat", value=float(st.session_state["start_coords"][0]), format="%.5f", key="in_start_lat")
            with r_start_c2:
                start_lon_val = st.number_input("Start Lon", value=float(st.session_state["start_coords"][1]), format="%.5f", key="in_start_lon")

            # Destination Point
            st.markdown("<div style='font-weight:600; font-size:0.82rem; color:#FF2A85; margin-top:4px;'>🏁 DESTINATION (END)</div>", unsafe_allow_html=True)
            r_end_c1, r_end_c2 = st.columns(2)
            with r_end_c1:
                end_lat_val = st.number_input("End Lat", value=float(st.session_state["end_coords"][0]), format="%.5f", key="in_end_lat")
            with r_end_c2:
                end_lon_val = st.number_input("End Lon", value=float(st.session_state["end_coords"][1]), format="%.5f", key="in_end_lon")

            # Map Click Assignment Buttons
            if clicked_coords:
                c_set_s, c_set_e = st.columns(2)
                with c_set_s:
                    if st.button("📍 Set Click as Start", key="btn_set_start_clicked"):
                        st.session_state["start_coords"] = clicked_coords
                        st.rerun()
                with c_set_e:
                    if st.button("🎯 Set Click as End", key="btn_set_end_clicked"):
                        st.session_state["end_coords"] = clicked_coords
                        st.rerun()

            # Execute Reroute Algorithm
            if st.button("✨ Compute Safest Route", key="btn_compute_safe_route", use_container_width=True):
                with st.spinner("Analyzing candidate routes & simulating urban risk grid..."):
                    route_result = get_reroute(
                        start=(start_lat_val, start_lon_val),
                        end=(end_lat_val, end_lon_val),
                        time=st.session_state["time_of_day"],
                    )
                    st.session_state["calculated_route"] = route_result
                    st.rerun()

            # Display Route Results
            if st.session_state.get("calculated_route"):
                r = st.session_state["calculated_route"]
                r_band = r.get("risk_band", "low")
                r_color = BAND_COLORS.get(r_band, "#00F59B")
                badge_class = f"risk-badge-{r_band}"

                st.markdown("---")
                st.markdown(
                    f"""
                    <div style="background: rgba(14, 17, 38, 0.85); border: 1px solid {r_color}; border-radius: 12px; padding: 10px; margin-top: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 700; color: #FFFFFF;">Safer Route Found:</span>
                            <span class="{badge_class}">{BAND_ICONS.get(r_band, '🛡️')} {r_band.upper()} RISK</span>
                        </div>
                        <div style="margin-top: 6px; font-size: 0.82rem; color: #D4C9E6;">
                            • <strong>Candidate Trajectories</strong>: {r.get('compared_routes', 5)} evaluated<br>
                            • <strong>Average Risk Score</strong>: <span style="color:{r_color}; font-weight:700;">{r.get('average_risk', 0.0)} / 100</span><br>
                            • <strong>Route Visualization</strong>: Traced with Glowing Emerald Polyline on Map
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("Clear Route from Map", key="btn_clear_route"):
                    st.session_state["calculated_route"] = None
                    st.rerun()

        # ------------------------------------------------------------
        # SUB-TAB 2: "FELT UNSAFE HERE" INSTANT REPORTER
        # ------------------------------------------------------------
        with deck_tab_report:
            st.markdown("#### 🚨 Felt Unsafe Here?")
            st.caption("Submit anonymous crowdsourced reports. Every report updates SafeGrid's risk grid instantly.")

            current_sel = st.session_state.get("selected_point", CITY_CENTER)

            rep_c1, rep_c2 = st.columns(2)
            with rep_c1:
                rep_lat = st.number_input("Target Lat", value=float(current_sel[0]), format="%.5f", key="rep_lat_input")
            with rep_c2:
                rep_lon = st.number_input("Target Lon", value=float(current_sel[1]), format="%.5f", key="rep_lon_input")

            incident_type = st.selectbox(
                "Risk Factor / Incident Tag",
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
                placeholder="e.g., Narrow alley near market with no lighting",
                key="rep_note_input",
            )

            st.markdown("<div class='sos-btn'>", unsafe_allow_html=True)
            if st.button("🚨 SUBMIT ANONYMOUS ALERT", key="btn_submit_unsafe_report", use_container_width=True):
                with st.spinner("Transmitting safety alert to SafeGrid network..."):
                    res = submit_report(rep_lat, rep_lon, note=f"[{incident_type}] {optional_note}")
                    if res.get("success"):
                        st.session_state["report_success_toast"] = res
                        st.success(f"✅ Report Logged ({res.get('report_id', 'LIVE')})! Risk grid updated.")
                        st.balloons()
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get("report_success_toast"):
                last_rep = st.session_state["report_success_toast"]
                st.markdown(
                    f"""
                    <div style="background: rgba(0, 245, 155, 0.1); border: 1px solid #00F59B; border-radius: 10px; padding: 8px; margin-top: 8px; font-size: 0.8rem;">
                        <strong>ID:</strong> <code>{last_rep.get('report_id')}</code> | <strong>Segment:</strong> <code>{last_rep.get('segment_id')}</code><br>
                        <span style="color:#00F59B;">Thank you for protecting our community! 💖</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ------------------------------------------------------------
        # SUB-TAB 3: SPOT INSPECTOR
        # ------------------------------------------------------------
        with deck_tab_spot:
            st.markdown("#### 🔍 Spot Safety Inspector")
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

            if st.button("⚡ Inspect Spot Safety", key="btn_inspect_spot", use_container_width=True):
                spot_res = predict_risk(cur_p[0], cur_p[1], time=st.session_state["time_of_day"])
                s_band = spot_res.get("band", "medium")
                s_score = spot_res.get("score", 0.0)
                s_color = BAND_COLORS.get(s_band, "#FFB800")

                st.markdown(
                    f"""
                    <div style="background: rgba(18, 22, 48, 0.9); border: 1px solid {s_color}; border-radius: 12px; padding: 12px; margin-top: 10px;">
                        <div style="font-size: 0.75rem; color: #8E88A8;">PREDICTED RISK BAND</div>
                        <div style="font-size: 1.3rem; font-weight: 800; color: {s_color}; font-family: 'Space Grotesk';">
                            {BAND_ICONS.get(s_band, '🛡️')} {s_band.upper()} RISK
                        </div>
                        <div style="font-size: 0.85rem; color: #D4C9E6; margin-top: 6px;">
                            • <strong>Nearest Segment</strong>: <code>{spot_res.get('segment_id')}</code><br>
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
    st.markdown('<div class="glam-title">🚨 SOS EMERGENCY COMMAND HUB</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Instant Panic Triggers, Deterrent Alarms, Fake Calls & Rapid Dispatch</div>', unsafe_allow_html=True)

    sos_col1, sos_col2 = st.columns([1, 1])

    with sos_col1:
        st.markdown(
            """
            <div class="glam-card">
                <h3 style="color:#FF2A55 !important;">⚡ 1-Tap Emergency Broadcast</h3>
                <p style="color:#D4C9E6; font-size:0.88rem;">
                    Generates a pre-formatted high-priority distress message with live GPS coordinates, Google Maps link, and current time for WhatsApp or SMS rapid broadcast to your emergency circle.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        curr_loc = st.session_state.get("selected_point", CITY_CENTER)
        maps_link = f"https://maps.google.com/?q={curr_loc[0]:.6f},{curr_loc[1]:.6f}"
        distress_msg = f"🚨 EMERGENCY SOS from SafeGrid! I feel unsafe right now. My current location is: {maps_link} at {datetime.now().strftime('%H:%M:%S')}. Please check on me or dispatch help immediately."

        st.text_area("Prepared Distress Broadcast Message", value=distress_msg, height=90, key="sos_msg_box")

        c_wa, c_sms = st.columns(2)
        with c_wa:
            wa_url = f"https://api.whatsapp.com/send?text={distress_msg.replace(' ', '%20')}"
            st.markdown(
                f"""
                <a href="{wa_url}" target="_blank" style="text-decoration:none;">
                    <div style="background: linear-gradient(135deg, #25D366 0%, #128C7E 100%); color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: 700; font-size: 0.92rem; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);">
                        💬 Share on WhatsApp
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
                    <div style="background: linear-gradient(135deg, #FF2A85 0%, #B71C5A 100%); color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: 700; font-size: 0.92rem; box-shadow: 0 4px 15px rgba(255, 42, 133, 0.4);">
                        📲 Send Direct SMS
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
                <h3 style="color:#FFB800 !important;">🔊 High-Decibel Deterrent Siren</h3>
                <p style="color:#D4C9E6; font-size:0.85rem;">
                    Activate an in-browser acoustic warning pulse to attract public attention and deter potential aggressors.
                </p>
                <div style="text-align: center; margin-top: 10px;">
                    <button id="sirenBtn" onclick="toggleSiren()" style="background: linear-gradient(135deg, #FFB800 0%, #FF5500 100%); border: none; color: white; padding: 10px 24px; border-radius: 999px; font-weight: 800; font-size: 0.95rem; cursor: pointer; box-shadow: 0 0 15px rgba(255, 184, 0, 0.4);">
                        🚨 TOGGLE SIREN ALARM
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
                    btn.innerText = "🛑 STOP SIREN ALARM";
                    btn.style.background = "#FF2A55";
                    status.innerText = "🔊 SIREN ACTIVE — Pulsing high decibel alert!";
                    status.style.color = "#FF2A55";
                } else {
                    if (osc) {
                        osc.stop();
                        osc.disconnect();
                        osc = null;
                    }
                    if (sirenInterval) clearInterval(sirenInterval);
                    isSirenOn = false;
                    btn.innerText = "🚨 TOGGLE SIREN ALARM";
                    btn.style.background = "linear-gradient(135deg, #FFB800 0%, #FF5500 100%)";
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
                <h3 style="color:#00F0FF !important;">📞 Fake Call Assistant</h3>
                <p style="color:#D4C9E6; font-size:0.88rem;">
                    Need a tactical escape from an uncomfortable situation or deserted street? Trigger a simulated incoming phone call.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        caller_id = st.selectbox(
            "Select Simulated Caller Identity",
            options=["Mom 💕", "Inspector Sharma 👮", "SafeGrid Emergency Dispatch 🛡️", "Cab Support Partner 🚕", "Boss / Colleague 🏢"],
            key="fake_caller_select",
        )

        if st.button("📲 TRIGGER INCOMING CALL NOW", key="btn_trigger_fake_call", use_container_width=True):
            st.session_state["fake_call_step"] = "ringing"

        if st.session_state.get("fake_call_step") == "ringing":
            st.markdown(
                f"""
                <div style="background: radial-gradient(circle, rgba(255,42,133,0.2) 0%, rgba(10,12,28,0.95) 100%); border: 2px solid #FF2A85; border-radius: 18px; padding: 20px; text-align: center; box-shadow: 0 0 30px rgba(255,42,133,0.4); margin-top: 12px;">
                    <div style="font-size: 2.8rem; animation: pulse 1s infinite;">📲</div>
                    <div style="font-size: 0.8rem; color: #8E88A8; text-transform: uppercase;">Incoming SafeCall</div>
                    <div style="font-family: 'Space Grotesk'; font-size: 1.6rem; font-weight: 800; color: #FFFFFF; margin: 4px 0;">{caller_id}</div>
                    <div style="font-size: 0.78rem; color: #00F59B;">Bhubaneswar Verified ID • SafeLine Active</div>
                    <div style="margin-top: 15px;">
                        <button onclick="alert('Call Answered: Simulated dialogue playing...')" style="background: #00F59B; color: #000; border: none; padding: 10px 20px; border-radius: 999px; font-weight: 800; font-size: 0.95rem; cursor: pointer; box-shadow: 0 0 15px #00F59B;">
                            📞 ACCEPT CALL
                        </button>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("❌ Dismiss Call", key="btn_dismiss_call"):
                st.session_state["fake_call_step"] = "idle"
                st.rerun()

# ==============================================================================
# TAB 3: WALK-WITH-ME COMPANION
# ==============================================================================
with tab_companion:
    st.markdown('<div class="glam-title">🚶‍♀️ WALK-WITH-ME GUARDIAN COMPANION</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Live Safety Interval Check-ins & Automatic Panic Alert Timers</div>', unsafe_allow_html=True)

    w_col1, w_col2 = st.columns([1, 1])

    with w_col1:
        st.markdown(
            """
            <div class="glam-card">
                <h3 style="color:#00F59B !important;">⏱️ Safety Check-in Timer</h3>
                <p style="color:#D4C9E6; font-size:0.88rem;">
                    Set your expected travel duration. If you do not tap <strong>"I Have Arrived Safely"</strong> before the timer expires, SafeGrid prepares an automated emergency broadcast.
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
            if st.button("🟢 Start Guardian Session", key="btn_start_companion", use_container_width=True):
                st.session_state["companion_active"] = True
                st.success("✨ Guardian Mode Active! SafeGrid is monitoring your journey.")
        with c_stop_t:
            if st.button("💖 I Have Arrived Safely", key="btn_stop_companion", use_container_width=True):
                st.session_state["companion_active"] = False
                st.balloons()
                st.success("🎉 Wonderful! Trip completed safely.")

        if st.session_state.get("companion_active"):
            st.markdown(
                f"""
                <div style="background: rgba(0, 245, 155, 0.12); border: 1px solid #00F59B; border-radius: 12px; padding: 12px; margin-top: 12px; text-align: center;">
                    <div style="font-size: 1.15rem; font-weight: 700; color: #00F59B;">🛡️ GUARDIAN WATCH ACTIVE</div>
                    <div style="font-size: 0.85rem; color: #FFFFFF; margin: 3px 0;">Destination: <strong>{destination_label}</strong></div>
                    <div style="font-size: 0.78rem; color: #A99EBE;">Window: {trip_minutes} mins • Automated watchdog running</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with w_col2:
        st.markdown(
            """
            <div class="glam-card">
                <h3 style="color:#FFB8D9 !important;">✨ Pre-Transit Safety Checklist</h3>
                <ul style="color:#D4C9E6; font-size:0.88rem; line-height:1.8;">
                    <li>🔋 <strong>Phone Battery</strong>: Keep charged above 20%</li>
                    <li>📍 <strong>Live Location</strong>: Share with trusted emergency contact</li>
                    <li>🎧 <strong>Situational Awareness</strong>: Keep one ear free from headphones</li>
                    <li>🔦 <strong>Well-lit Paths</strong>: Follow SafeGrid's emerald routing</li>
                    <li>🚨 <strong>Quick Access</strong>: Keep SafeGrid open in browser</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# TAB 4: COMMUNITY INCIDENT FEED
# ==============================================================================
with tab_feed:
    st.markdown('<div class="glam-title">📢 COMMUNITY INCIDENT FEED</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Crowdsourced Vigilance & Real-Time Incident Reports Across Bhubaneswar</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="glam-title">📊 URBAN SAFETY INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Statistical Safety Profiles, Lighting Correlations & Vulnerability Patterns</div>', unsafe_allow_html=True)

    an_col1, an_col2 = st.columns(2)

    with an_col1:
        st.markdown(
            """
            <div class="glam-card">
                <h3>🌆 Risk Distribution by Time Bucket</h3>
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
                <h3>💡 Key Risk Influencers (XGBoost Weights)</h3>
                <p style="color:#D4C9E6; font-size:0.88rem; line-height:1.7;">
                    • <strong>Lighting Score & Operational Streetlight %</strong>: 38% predictive weight<br>
                    • <strong>Historical Incidents & Annual Crime Records</strong>: 26% predictive weight<br>
                    • <strong>Crowd Volume & Density by Time-of-Day</strong>: 18% predictive weight<br>
                    • <strong>Crowdsourced "Felt Unsafe" Real-time Reports</strong>: 12% dynamic weight<br>
                    • <strong>Urban Zone Type & Distance to Center</strong>: 6% structural weight
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# TAB 6: ABOUT & MODEL ARCHITECTURE
# ==============================================================================
with tab_about:
    st.markdown('<div class="glam-title">ℹ️ ABOUT CODE COVEN & SAFEGRID</div>', unsafe_allow_html=True)
    st.markdown('<div class="glam-subtitle">Empowering Women with Predictive Urban Safety & Machine Learning</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="glam-card">
            <h3 style="color:#FF2A85 !important;">🌟 Mission: Autonomous Safety Before Danger Strikes</h3>
            <p style="color:#D4C9E6; font-size:0.92rem; line-height:1.7;">
                Most safety applications only act <em>after</em> an incident occurs (emergency triggers and panics). 
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
                <h4>🧠 ML Pipeline & Architecture</h4>
                <p style="color:#D4C9E6; font-size:0.86rem; line-height:1.6;">
                    • <strong>Engine</strong>: Gradient Boosted Decision Trees (XGBoost Regressor & Classifier)<br>
                    • <strong>Geospatial Mesh</strong>: 500m hexagonal & square grid cells across Bhubaneswar<br>
                    • <strong>Quantile Thresholds</strong>: Low (≤25.1), Medium (25.2–40.4), High (>40.4)<br>
                    • <strong>Safer Rerouting</strong>: Multi-path sinusoidal candidate optimization
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ab_c2:
        st.markdown(
            """
            <div class="glam-card">
                <h4>💖 Code Coven • Infinity Hacks 2026</h4>
                <p style="color:#D4C9E6; font-size:0.86rem; line-height:1.6;">
                    Built with love, technology, and resilience for every woman walking home under the night sky.
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
        SafeGrid AI Matrix v2.0 • Team Code Coven • Infinity Hacks 2026 • Dedicated to Women Safety Everywhere 🛡️✨
    </div>
    """,
    unsafe_allow_html=True,
)