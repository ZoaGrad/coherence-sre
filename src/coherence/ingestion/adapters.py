"""
Coherence SRE: Ingestion Adapters.
"""

import time
import random
import psutil
from typing import Protocol,runtime_checkable

from coherence.core.model import SystemMetrics

class MetricAdapter:
    def get_metrics(self) -> SystemMetrics:
        raise NotImplementedError

class LiveAdapter(MetricAdapter):
    def get_metrics(self) -> SystemMetrics:
        try:
            mem = psutil.virtual_memory()
            net = psutil.net_io_counters()
            cpu = psutil.cpu_percent(interval=None) 
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=float(cpu),
                memory_used_mb=mem.used / 1024 / 1024,
                net_sent_packets=net.packets_sent,
                net_recv_packets=net.packets_recv
            )
        except Exception as e:
            raise RuntimeError(f"Sensor failure: {str(e)}")

class SimAdapter(MetricAdapter):
    def __init__(self) -> None:
        self.step = 0
        self.base_net_sent = 1000
        self.base_net_recv = 1000
        self.base_mem = 4000.0

    def get_metrics(self) -> SystemMetrics:
        self.step += 1
        t = time.time()
        # Cascade Scenario: Seizure -> Fever
        if 20 < self.step < 30:
            cpu = random.choice([10.0, 90.0]) 
        else:
            cpu = random.uniform(40.0, 50.0)
            
        if 25 < self.step < 35: # Overlap to trigger Cascade
            mem_churn = 500.0
        else:
            mem_churn = 5.0
        self.base_mem += mem_churn

        return SystemMetrics(
            timestamp=t,
            cpu_percent=cpu,
            memory_used_mb=self.base_mem,
            net_sent_packets=self.base_net_sent + (self.step * 10),
            net_recv_packets=self.base_net_recv + (self.step * 10)
        )
