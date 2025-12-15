"""
Coherence SRE: Data Models and Configuration.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List, Any

@dataclass(frozen=True)
class ThresholdConfig:
    """Immutable configuration for detection thresholds."""
    cpu_variance_limit: float = 10.0
    alloc_rate_limit_mb_s: float = 100.0
    amplification_ratio_limit: float = 1.1
    window_size_seconds: int = 60
    poll_interval: float = 1.0

# Global Configuration Instance
CONFIG = ThresholdConfig()

@dataclass
class SystemMetrics:
    """Data transfer object for system telemetry."""
    timestamp: float
    cpu_percent: float
    memory_used_mb: float
    net_sent_packets: int
    net_recv_packets: int
