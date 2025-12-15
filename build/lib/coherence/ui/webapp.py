import streamlit as st
import pandas as pd
import time
import psutil
import math
from collections import deque
import plotly.graph_objects as go
from datetime import datetime

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
    # Use config threshold
    st.session_state.scanner = VarianceScanner(threshold_multiplier=2.0)

# --- Layout ---
st.set_page_config(
    page_title="Coherence Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for "War Room" feel
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4b4b4b;
    }
    .status-ok { border-left-color: #2ecc71; }
    .status-warn { border-left-color: #f1c40f; }
    .status-crit { border-left-color: #e74c3c; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Coherence SRE // OVERWATCH")
st.caption("Demo Interface · Stateless · Local Metrics Only")

# --- Ingestion (Local) ---
# For the web demo, we stick to psutil for instant gratification
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

if len(history_df) > 5:
    # 1. Variance Physics
    cpu_data = history_df['cpu'].tolist()
    # Using the scanner from Phase 2 logic (detection/detectors.py)
    # Detects based on baseline=1.0? 
    # The detector logic: if variance > baseline * 2.0 (default in init)
    # This is a relative check.
    # To show "Seizure", we might want to use the absolute threshold from CONFIG too?
    # CLI uses: if cpu_std_dev > CONFIG.cpu_variance_limit
    # Let's align with CLI for consistency.
    
    detection = st.session_state.scanner.detect(cpu_data, baseline_variance=1.0)
    current_variance = detection.score # Variance
    current_std_dev = math.sqrt(current_variance)
    
    # Use Config Threshold for Red Alert
    is_seizure = current_std_dev > CONFIG.cpu_variance_limit
else:
    current_std_dev = 0.0
    is_seizure = False

# --- Visualization ---

# Top Metrics Row
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("CPU Load (Mean)", f"{cpu:.1f}%")
with c2:
    color = "normal" if not is_seizure else "inverse"
    st.metric("CPU Variance (Ache)", f"{current_std_dev:.2f}", delta_color=color)
with c3:
    st.metric("Memory Usage", f"{mem:.1f}%")
with c4:
    status_text = "STABLE"
    if is_seizure: status_text = "SEIZURE"
    st.metric("System Status", status_text)

# Main Graph: Variance vs Load
if not history_df.empty:
    fig = go.Figure()
    
    # Trace 1: CPU Load (The Lie)
    fig.add_trace(go.Scatter(
        x=history_df['timestamp'], 
        y=history_df['cpu'],
        mode='lines',
        name='CPU Load',
        line=dict(color='#3498db', width=2)
    ))
    
    fig.update_layout(
        title="Real-Time Coherence Trace",
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Time",
        yaxis_title="Load %",
        font=dict(color="white")
    )
    
    if is_seizure:
        # Add Red Zone
        fig.add_vrect(
            x0=history_df['timestamp'].min(), 
            x1=history_df['timestamp'].max(),
            fillcolor="red", opacity=0.1, line_width=0
        )

    st.plotly_chart(fig, use_container_width=True)

# Auto-Refresh Logic
time.sleep(POLL_RATE)
st.rerun()
