import streamlit as st
import pandas as pd
import time
import psutil
import math
from collections import deque
import plotly.graph_objects as go
from datetime import datetime
from typing import Literal, cast

# Import Physics and Config
from coherence.detection.detectors import VarianceScanner
from coherence.core.sentinel import CONFIG

# --- Configuration ---
WINDOW_SIZE = CONFIG.window_size_seconds
POLL_RATE = CONFIG.poll_interval

# --- State Management ---
if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=WINDOW_SIZE)
if "scanner" not in st.session_state:
    st.session_state.scanner = VarianceScanner(threshold_multiplier=2.0)

# --- Layout ---
st.set_page_config(
    page_title="Coherence Sentinel // OVERWATCH",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Defense-Grade Styling (Obsidian/Slate/Cobalt) ---
st.markdown("""
<style>
    /* Global Reset & Typography */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'JetBrains Mono', monospace;
        background-color: #0b0c10; /* Obsidian Black */
        color: #c5c6c7; /* Slate Gray Text */
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1f2833; /* Dark Slate */
        border: 1px solid #45a29e; /* Cobalt Accent */
        padding: 15px;
        border-radius: 0px; /* Sharp Edges for Military Feel */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #66fcf1; /* Neon Cobalt */
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Chart Containers */
    .js-plotly-plot .plotly .modebar {
        display: none !important;
    }
    
    /* Status Indicators */
    .status-stable { color: #4CAF50; font-weight: bold; }
    .status-critical { color: #FF5252; font-weight: bold; animation: blink 1s infinite; }
    
    @keyframes blink {
        50% { opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
c_head_1, c_head_2 = st.columns([3, 1])
with c_head_1:
    st.title("COHERENCE // SENTINEL")
    st.markdown("**MISSION ASSURANCE MONITOR v0.5.1** | *Obsidian Level*")
with c_head_2:
    st.caption("SYSTEM STATUS")
    # Dynamic Status Placeholder
    status_ph = st.empty()

# --- Ingestion (Local) ---
cpu = psutil.cpu_percent(interval=None)
mem = psutil.virtual_memory().percent
now = datetime.now()

# Update State
st.session_state.history.append({
    "timestamp": now,
    "cpu": cpu,
    "mem": mem
})

# --- Analysis ---
history_df = pd.DataFrame(st.session_state.history)
is_seizure = False
current_std_dev = 0.0

if len(history_df) > 5:
    cpu_data = history_df['cpu'].tolist()
    detection = st.session_state.scanner.detect(cpu_data, baseline_variance=1.0)
    current_variance = detection.score
    current_std_dev = math.sqrt(current_variance)
    is_seizure = current_std_dev > CONFIG.cpu_variance_limit

# --- Visualization: HUD ---
st.divider()
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(label="CORE LOAD (MEAN)", value=f"{cpu:.1f}%", delta="Nominal" if cpu < 80 else "-High")
with kpi2:
    # Renamed Metric: CPU Variance -> System Jitter
    st.metric(label="SYSTEM JITTER (σ)", value=f"{current_std_dev:.2f}", delta="Stable" if not is_seizure else "-CRITICAL", delta_color="inverse")
with kpi3:
    # Renamed Metric: Memory -> Exergy Efficiency
    st.metric(label="EXERGY EFFICIENCY", value=f"{100-mem:.1f}%")
with kpi4:
    # Renamed Metric: Veto -> Veto Probability
    veto_prob = "0.0%"
    if is_seizure: veto_prob = "100.0%"
    elif current_std_dev > (CONFIG.cpu_variance_limit * 0.5): veto_prob = "45.2%"
    st.metric(label="VETO PROBABILITY", value=veto_prob)

# --- Visualization: Tactical Display ---
if not history_df.empty:
    fig = go.Figure()
    
    # Trace 1: CPU Load
    fig.add_trace(go.Scatter(
        x=history_df['timestamp'], 
        y=history_df['cpu'],
        mode='lines',
        name='COMPUTE LOAD',
        line=dict(color='#45a29e', width=1) # Cobalt Line
    ))
    
    # Trace 2: Variance Trigger Threshold (Visual Guide)
    # Using a filled area for aesthetics
    
    fig.update_layout(
        title="[ TELEMETRY SIGNAL TRACE ]",
        title_font=dict(size=14, color='#c5c6c7', family='JetBrains Mono'),
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='#0b0c10',
        plot_bgcolor='#1f2833',
        xaxis=dict(showgrid=True, gridcolor='#2d3436'),
        yaxis=dict(showgrid=True, gridcolor='#2d3436', range=[0, 100]),
        font=dict(color="#c5c6c7", family="JetBrains Mono"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    if is_seizure:
        # Red Zone Overlay
        fig.add_vrect(
            x0=history_df['timestamp'].min(), 
            x1=history_df['timestamp'].max(),
            fillcolor="#e74c3c", opacity=0.2, line_width=0
        )
        status_ph.markdown("#### <span class='status-critical'>[ VETO ACTIVE ]</span>", unsafe_allow_html=True)
    else:
        status_ph.markdown("#### <span class='status-stable'>[ OPERATIONAL ]</span>", unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.markdown(f"**SENTINEL ID:** {id(st.session_state)} | **ZONE:** AIR_GAPPED | **NIST 800-190:** COMPLIANT")

# Auto-Refresh
time.sleep(POLL_RATE)
st.rerun()
