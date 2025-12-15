
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Anomaly:
    timestamp: pd.Timestamp
    metric: str
    value: float
    score: float
    type: str  # 'spike', 'variance', 'trend'

class AdvancedDetector:
    """
    Enterprise-grade detection engine using Pandas for high-performance 
    time-series analysis. Ports logic from Mythotech 'detect_anomalies.py'.
    """

    def __init__(self, window_size: int = 12, sensitivity: float = 3.0):
        self.window_size = window_size
        self.sensitivity = sensitivity

    def detect_spikes(self, df: pd.DataFrame, metric_col: str = 'value') -> pd.DataFrame:
        """
        Detects sudden shocks using Robust Z-Score (MAD).
        Returns DataFrame with 'is_anomaly' and 'score' columns.
        """
        if df.empty:
            return df

        # Calculate Rolling Median and MAD
        rolling_median = df[metric_col].rolling(window=self.window_size, min_periods=1).median()
        rolling_mad = df[metric_col].rolling(window=self.window_size, min_periods=1).apply(
            lambda x: np.median(np.abs(x - np.median(x))), raw=True
        )

        # Calculate Robust Z-Score
        # Constant 1.4826 makes MAD consistent with StdDev for normal distribution
        score = 1.4826 * (df[metric_col] - rolling_median) / rolling_mad
        score = score.fillna(0.0)

        df['score'] = score
        df['is_anomaly'] = score.abs() > self.sensitivity
        df['anomaly_type'] = 'spike'
        
        return df[df['is_anomaly']].copy()

    def detect_variance_escalation(self, df: pd.DataFrame, metric_col: str = 'value') -> pd.DataFrame:
        """
        Detects 'Seizure' state (increasing entropy) using Rolling Variance.
        """
        if df.empty:
            return df

        # Calculate Rolling Variance
        rolling_var = df[metric_col].rolling(window=self.window_size, min_periods=5).var()
        
        # Detect where variance is 2x the baseline (mean variance of full window)
        baseline_var = rolling_var.mean()
        df['score'] = rolling_var / (baseline_var + 1e-6) # Avoid div/0
        
        df['is_anomaly'] = df['score'] > 2.0  # Threshold: 2x baseline
        df['anomaly_type'] = 'variance'

        return df[df['is_anomaly']].copy()
