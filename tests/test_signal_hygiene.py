
import time
import pytest
from coherence.core.sentinel import CoherenceSentinel, SystemMetrics, CONFIG

def test_blindness_veto():
    """
    Verifies that the Sentinel declares 'STALE' status ('Signal Lost')
    when data is older than max_signal_lag_seconds.
    """
    sentinel = CoherenceSentinel()
    
    # 1. Ingest stale data (400s lag > 300s limit)
    now = time.time()
    stale_ts = now - 400
    
    metric = SystemMetrics(
        timestamp=stale_ts,
        cpu_percent=50.0,
        memory_used_mb=1024.0,
        net_sent_packets=1000,
        net_recv_packets=1000
    )
    
    sentinel.ingest(metric)
    
    # Fill history to avoid WARMUP (need 5 points)
    for _ in range(4):
        sentinel.ingest(metric)
        
    analysis = sentinel.analyze()
    
    # 2. Verify Status
    assert analysis["status"] == "STALE"
    assert "signal_lag" in analysis["metrics"]
    assert analysis["metrics"]["signal_lag"] >= 400
    assert analysis["veto"] is None
    
    print("\n[PASS] Blindness Veto verified: STALE status triggered by lag.")

def test_fresh_signal():
    """
    Verifies that fresh data is processed normally.
    """
    sentinel = CoherenceSentinel()
    now = time.time()
    
    metric = SystemMetrics(
        timestamp=now,
        cpu_percent=10.0, # Low CPU -> STABLE
        memory_used_mb=1024.0,
        net_sent_packets=1000,
        net_recv_packets=1000
    )
    
    for _ in range(5):
        sentinel.ingest(metric)
        
    analysis = sentinel.analyze()
    
    assert analysis["status"] == "STABLE"
    assert analysis["metrics"]["signal_lag"] < 1.0
