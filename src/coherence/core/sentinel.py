"""
Coherence SRE: Core Sentinel Logic.
"""

from collections import deque
from typing import Dict, Optional, List, Any
import math

from coherence.core.model import SystemMetrics, CONFIG
from coherence.detection.detectors import VarianceScanner

class CoherenceSentinel:
    """
    The Core Logic Engine.
    """
    
    def __init__(self) -> None:
        """Initializes the Sentinel with history and detectors."""
        self.history: deque[SystemMetrics] = deque(maxlen=CONFIG.window_size_seconds)
        self.status: str = "WARMUP"
        
        # Sprint 2: Modular Math
        self.variance_scanner = VarianceScanner(
            threshold_multiplier=2.0 
        )
        
    def ingest(self, metrics: SystemMetrics) -> None:
        self.history.append(metrics)

    def analyze(self) -> Dict[str, Any]:
        """Performs analysis using modular detectors."""
        if len(self.history) < 5:
            return {"status": "WARMUP", "metrics": {}, "veto": None}

        try:
            # --- Sensor 1: Compute Variance ---
            cpu_values = [m.cpu_percent for m in self.history]
            # Trick scanner with dummy baseline to get raw variance
            variance_result = self.variance_scanner.detect(cpu_values, baseline_variance=1.0)
            
            cpu_variance = variance_result.score
            cpu_std_dev = math.sqrt(cpu_variance)
            cpu_mean = sum(cpu_values) / len(cpu_values)

            # --- Sensor 2: Memory Allocation Rate ---
            oldest = self.history[0]
            newest = self.history[-1]
            time_delta = newest.timestamp - oldest.timestamp
            mem_delta = newest.memory_used_mb - oldest.memory_used_mb
            
            if time_delta > 0:
                alloc_rate_mb_s = max(0.0, mem_delta / time_delta)
            else:
                alloc_rate_mb_s = 0.0

            # --- Sensor 3: Amplification Ratio ---
            sent_delta = newest.net_sent_packets - oldest.net_sent_packets
            recv_delta = newest.net_recv_packets - oldest.net_recv_packets
            
            if recv_delta > 0:
                amp_ratio = sent_delta / recv_delta
            else:
                amp_ratio = 1.0

            metrics = {
                "cpu_mean": cpu_mean,
                "cpu_variance": cpu_std_dev,
                "alloc_rate": alloc_rate_mb_s,
                "amp_ratio": amp_ratio
            }

            # --- The Veto Engine ---
            veto: Optional[Dict[str, str]] = None
            
            if cpu_std_dev > CONFIG.cpu_variance_limit:
                veto = {
                    "type": "COMPUTE",
                    "action": "SHED_LOAD",
                    "reason": f"Variance {cpu_std_dev:.1f} > Limit"
                }
            elif alloc_rate_mb_s > CONFIG.alloc_rate_limit_mb_s:
                veto = {
                    "type": "RESOURCE",
                    "action": "THROTTLE",
                    "reason": f"Rate {alloc_rate_mb_s:.1f}MB/s > Limit"
                }
            elif amp_ratio > CONFIG.amplification_ratio_limit:
                veto = {
                    "type": "INTENT",
                    "action": "CAP_RETRIES",
                    "reason": f"Amp {amp_ratio:.2f}x > Limit"
                }

            status = "UNSTABLE" if veto else "STABLE"
            return {"status": status, "metrics": metrics, "veto": veto}

        except Exception as e:
            return {"status": "ERROR", "metrics": {}, "veto": None, "error": str(e)}
