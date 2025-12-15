"""
Integration Tests for Event Correlation.
"""

import pytest
from coherence.correlation.correlator import EventCorrelator, IncidentType

def test_flapping_detection():
    """Ensure rapid status changes trigger FLAPPING incident."""
    correlator = EventCorrelator(history_window=10, flapping_threshold=3)
    
    # Simulate oscillating stream
    # STABLE -> UNSTABLE -> STABLE -> UNSTABLE (3 transitions)
    stream = [
        {"status": "STABLE", "veto": None},
        {"status": "UNSTABLE", "veto": {"type": "COMPUTE"}},
        {"status": "STABLE", "veto": None},
        {"status": "UNSTABLE", "veto": {"type": "COMPUTE"}},
    ]
    
    incident = None
    for report in stream:
        res = correlator.ingest(report)
        if res:
            incident = res
            
    assert incident is not None
    assert incident.type == IncidentType.FLAPPING
    assert incident.severity == "WARN"

def test_cascade_detection():
    """Ensure multiple different sensor failures trigger CASCADE."""
    correlator = EventCorrelator(history_window=10)
    
    # Sequence: CPU failure, then Memory failure
    stream = [
        {"status": "UNSTABLE", "veto": {"type": "COMPUTE"}},
        {"status": "UNSTABLE", "veto": {"type": "COMPUTE"}},
        {"status": "UNSTABLE", "veto": {"type": "RESOURCE"}}, # Second type
    ]
    
    incident = None
    for report in stream:
        res = correlator.ingest(report)
        if res:
            incident = res
            
    assert incident is not None
    assert incident.type == IncidentType.CASCADING
    assert "COMPUTE" in incident.description
    assert "RESOURCE" in incident.description

def test_stable_behavior():
    """Ensure stable stream produces no incidents."""
    correlator = EventCorrelator()
    for _ in range(5):
        res = correlator.ingest({"status": "STABLE", "veto": None})
        assert res is None
