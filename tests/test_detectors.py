"""
Unit Tests for Coherence Detection Logic.
"""

import pytest
import statistics
from coherence.detection.detectors import VarianceScanner, SpikeDetector

# --- VarianceScanner Tests ---

def test_variance_stable():
    """Ensure stable data does not trigger variance anomaly."""
    scanner = VarianceScanner(threshold_multiplier=2.0)
    data = [50.0, 51.0, 49.0, 50.0, 50.5] # Low variance
    baseline = 2.0 # Arbitrary baseline
    
    result = scanner.detect(data, baseline_variance=baseline)
    assert not result.is_anomaly
    assert result.details["metric"] == "variance"

def test_variance_thrashing():
    """Ensure high variance (thrashing) triggers anomaly."""
    scanner = VarianceScanner(threshold_multiplier=2.0)
    # Alternating 10 and 90 (High Variance)
    data = [10.0, 90.0, 10.0, 90.0, 10.0] 
    
    # Calculate actual variance: approx 1600
    baseline = 100.0 
    
    result = scanner.detect(data, baseline_variance=baseline)
    assert result.is_anomaly
    assert result.score > 1000.0

# --- SpikeDetector Tests ---

def test_spike_mad_robustness():
    """
    Verify MAD handles outliers better than Standard Deviation.
    With standard Z-score, a huge outlier shifts the mean, hiding the spike.
    With MAD, the median stays stable.
    """
    detector = SpikeDetector(threshold_sigma=3.0)
    
    # History of stable 10s
    history = [10.0] * 20 
    # Target is 50 (Huge spike)
    data = history + [50.0]
    
    result = detector.detect(data)
    
    assert result.is_anomaly
    # MAD of [10, 10...] is 0. Z-score should be inf or very high.
    assert result.score > 3.0

def test_spike_stable():
    """Verify normal noise is ignored."""
    detector = SpikeDetector(threshold_sigma=3.0)
    history = [10.0, 11.0, 9.0, 10.5, 9.5]
    data = history + [10.2]
    
    result = detector.detect(data)
    assert not result.is_anomaly

def test_insufficient_data():
    """Detectors should handle empty/small lists gracefully."""
    scanner = VarianceScanner()
    res_var = scanner.detect([1.0], 5.0)
    assert not res_var.is_anomaly
    assert res_var.details["reason"] == "insufficient_data"

    detector = SpikeDetector()
    res_spike = detector.detect([1.0, 2.0])
    assert not res_spike.is_anomaly
    assert res_spike.details["reason"] == "insufficient_data"
