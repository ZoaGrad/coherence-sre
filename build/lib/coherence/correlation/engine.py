
import pandas as pd
from datetime import timedelta
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Incident:
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    host: str
    risk_score: float
    narrative: str
    evidence: List[Dict[str, Any]]

class CorrelationEngine:
    """
    Temporal Logic Engine. Groups isolated anomalies into cohesive Incidents.
    Ports logic from Mythotech 'correlate_incidents.py'.
    """

    def __init__(self, time_window_minutes: int = 5):
        self.window = timedelta(minutes=time_window_minutes)

    def correlate(self, anomalies: pd.DataFrame) -> List[Incident]:
        """
        Groups anomalies by Host and Time Window.
        """
        incidents = []
        if anomalies.empty:
            return incidents

        # Ensure sorted by time
        anomalies = anomalies.sort_values('timestamp')

        # Group by Host
        for host, group in anomalies.groupby('host'):
            # Temporal Grouping (Simple Sliding Window)
            # We iterate through anomalies and cluster them if they are close in time
            
            cluster_start = group.iloc[0]['timestamp']
            cluster_end = cluster_start + self.window
            current_cluster = []

            for _, row in group.iterrows():
                ts = row['timestamp']
                
                if ts <= cluster_end:
                    # Add to current cluster
                    current_cluster.append(row)
                    # Extend window if needed (chain reaction)
                    cluster_end = max(cluster_end, ts + self.window)
                else:
                    # Finalize current cluster
                    if len(current_cluster) >= 2: # Minimum 2 signals for an Incident
                        incidents.append(self._generate_incident(host, current_cluster))
                    
                    # Start new cluster
                    current_cluster = [row]
                    cluster_start = ts
                    cluster_end = ts + self.window
            
            # Finalize last cluster
            if len(current_cluster) >= 2:
                incidents.append(self._generate_incident(host, current_cluster))

        return incidents

    def _generate_incident(self, host: str, cluster: List[Any]) -> Incident:
        """Generates a Hypothesis/Narrative for the cluster."""
        df = pd.DataFrame(cluster)
        start = df['timestamp'].min()
        end = df['timestamp'].max()
        
        # Calculate Aggregate Risk
        risk_score = min(1.0, df['score'].abs().mean() / 10.0) 
        
        # Generate Narrative
        types = df['anomaly_type'].unique()
        narrative = f"Detected instability on {host}. "
        
        if 'variance' in types and 'spike' in types:
            narrative += "Pattern: CASCADING FAILURE (Variance escalation leading to Spikes)."
        elif 'variance' in types:
            narrative += "Pattern: COMPUTE SEIZURE (High Variance)."
        elif 'spike' in types:
            narrative += "Pattern: SYSTEM SHOCK (Sudden Load)."
            
        return Incident(
            start_time=start,
            end_time=end,
            host=host,
            risk_score=risk_score,
            narrative=narrative,
            evidence=cluster
        )
