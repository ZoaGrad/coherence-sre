
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sys
import os

# Add src to path to simulate package install if running locally
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from coherence.detection.advanced import AdvancedDetector
from coherence.correlation.engine import CorrelationEngine

def generate_synthetic_data(duration_minutes: int = 60) -> pd.DataFrame:
    """Generates a 'Seizure' pattern (CPU Variance) followed by a 'Fever' (Memory)."""
    print(f"Generating {duration_minutes} minutes of synthetic telemetry...")
    
    timestamps = [datetime.now() + timedelta(seconds=i) for i in range(duration_minutes * 60)]
    data = []
    
    # Base pattern: Stable
    for ts in timestamps:
        # Default: Stable CPU (40-60%)
        cpu = random.uniform(40, 60)
        host = "host-001"
        
        # Minute 10-15: Compute Seizure (High Variance)
        # Thrashing between 10% and 90%
        elapsed_min = (ts - timestamps[0]).seconds / 60
        if 10 <= elapsed_min <= 15:
            cpu = random.choice([10.0, 95.0]) # Thrashing
            
        data.append({
            "timestamp": ts,
            "host": host,
            "metric": "cpu_usage",
            "value": cpu
        })
        
    return pd.DataFrame(data)

def run_simulation():
    print("--- COHERENCE FLIGHT SIMULATOR v1.0 ---")
    
    # 1. Ingest (Synthetic)
    df = generate_synthetic_data(duration_minutes=30)
    print(f"Ingested {len(df)} data points.")
    
    # 2. Detect (The Brain)
    print("\n[Running Advanced Detection...]")
    detector = AdvancedDetector(window_size=60) # 1 minute window
    
    # Check for Variance (Seizure)
    anomalies = detector.detect_variance_escalation(df, metric_col='value')
    
    num_anomalies = len(anomalies)
    print(f"Detected {num_anomalies} anomalies.")
    
    if num_anomalies > 0:
        print(f"Sample Anomaly:\n{anomalies.head(1)[['timestamp', 'score', 'anomaly_type']].to_string(index=False)}")

    # 3. Correlate (The Memory)
    print("\n[Running Correlation Engine...]")
    engine = CorrelationEngine(time_window_minutes=5)
    incidents = engine.correlate(anomalies)
    
    print(f"Generated {len(incidents)} Incidents.")
    
    for i, incident in enumerate(incidents):
        print(f"\n--- INCIDENT #{i+1} ---")
        print(f"Host: {incident.host}")
        print(f"Risk Score: {incident.risk_score:.2f}")
        print(f"Duration: {incident.start_time.strftime('%H:%M:%S')} - {incident.end_time.strftime('%H:%M:%S')}")
        print(f"Narrative: {incident.narrative}")
        print("-----------------------")

if __name__ == "__main__":
    run_simulation()
