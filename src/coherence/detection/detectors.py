"""
Coherence Detection Module.

This module implements statistical detection algorithms for system stability,
including Variance Scanning and Robust Spike Detection (MAD).

Copyright (c) 2025 Blackglass Continuum. MIT License.
"""

import math
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AnomalyResult:
    """
    Result object for a detection algorithm.

    Attributes:
        is_anomaly (bool): Whether the data triggered the detector.
        score (float): The calculated magnitude of the signal (e.g., Variance, Z-Score).
        details (Dict[str, Any]): Contextual metadata for debugging.
    """
    is_anomaly: bool
    score: float
    details: Dict[str, Any] = field(default_factory=dict)

class VarianceScanner:
    """
    Detects instability by monitoring statistical variance against a baseline.
    """

    def __init__(self, threshold_multiplier: float = 2.0) -> None:
        """
        Args:
            threshold_multiplier (float): Factor by which variance must exceed
            baseline to trigger an anomaly. Defaults to 2.0.
        """
        self.threshold_multiplier = threshold_multiplier

    def detect(self, data: List[float], baseline_variance: float) -> AnomalyResult:
        """
        Analyzes the variance of the provided data window.

        Args:
            data (List[float]): The window of metrics to analyze.
            baseline_variance (float): The expected 'normal' variance.

        Returns:
            AnomalyResult: Contains the calculated variance (score) and anomaly status.
        """
        if len(data) < 2:
            return AnomalyResult(
                is_anomaly=False, 
                score=0.0, 
                details={"reason": "insufficient_data"}
            )

        try:
            # Calculate Variance (Sample variance)
            variance = statistics.variance(data)
        except statistics.StatisticsError:
            # Handle edge cases where statistics module fails (e.g. data < 2 handled above)
             return AnomalyResult(
                is_anomaly=False, 
                score=0.0, 
                details={"reason": "statistics_error"}
            )

        # Logic: Is Current Variance > Baseline * Multiplier?
        # We assume baseline_variance is positive.
        threshold = baseline_variance * self.threshold_multiplier
        is_anomaly = variance > threshold

        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=variance,
            details={
                "metric": "variance",
                "threshold": threshold,
                "baseline": baseline_variance
            }
        )


class SpikeDetector:
    """
    Detects transient spikes using Median Absolute Deviation (MAD).
    Robust against outliers compared to Standard Deviation.
    """

    def __init__(self, threshold_sigma: float = 3.0) -> None:
        """
        Args:
            threshold_sigma (float): The Modified Z-Score threshold. 
            Values > 3.0 are typically considered anomalies.
        """
        self.threshold_sigma = threshold_sigma

    def detect(self, data: List[float]) -> AnomalyResult:
        """
        Checks the *last* data point in the list for creating a spike.

        Args:
            data (List[float]): Historical data ending with the point to test.

        Returns:
            AnomalyResult: Score is the Modified Z-Score of the last point.
        """
        if len(data) < 3: # Need median and existence of deviation
             return AnomalyResult(
                is_anomaly=False, 
                score=0.0, 
                details={"reason": "insufficient_data"}
            )
        
        target = data[-1]
        history = data # strict MAD calculation should include the point, or not? 
        # Standard approach: MAD of the whole window, check if target is outlier.
        
        median = statistics.median(history)
        deviations = [abs(x - median) for x in history]
        mad = statistics.median(deviations)
        
        # Consistency Constant for Normal Distribution
        k = 1.4826 
        
        # Avoid Division by Zero (Perfectly flat line)
        if mad == 0:
            # If MAD is 0, any deviation from median is technically infinite Z-score.
            # We treat strict 0 variance as a special case.
            if target != median:
                # Infinite spike
                mod_z_score = float('inf')
            else:
                mod_z_score = 0.0
        else:
            mod_z_score = (target - median) / mad  # Note: Sometimes defined as 0.6745 * (x-med)/MAD. 
            # If we use the standard K=1.4826 (1/0.6745), then Sigma = (x - med) / (K * MAD)?
            # Actually standard Modified Z-score M_i = 0.6745 * (x_i - median) / MAD
            # Let's stick to the prompt's implication or standard definition.
            # Using M = 0.6745 * diff / MAD. 
            # If user asks for "threshold_sigma", they usually mean "How many standard deviations away".
            # For normal dist, Sigma approx 1.4826 * MAD.
            # So Z = (x - mean) / Sigma approx (x - median) / (1.4826 * MAD).
            # Which simplifies to 0.6745 * (x - median) / MAD.
            
            mod_z_score = 0.6745 * (target - median) / mad

        # We care about magnitude (absolute z-score)
        abs_score = abs(mod_z_score)
        
        is_anomaly = abs_score > self.threshold_sigma

        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=abs_score,
            details={
                "metric": "mad_z_score",
                "median": median,
                "mad": mad
            }
        )
