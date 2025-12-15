import time
import os
from typing import Any

# Lazy SystemMetrics def
try:
    from ..core.sentinel import SystemMetrics
except ImportError:
    from dataclasses import dataclass
    @dataclass
    class SystemMetrics:
        timestamp: float
        cpu_percent: float
        memory_used_mb: float
        net_sent_packets: int
        net_recv_packets: int

class AdapterError(Exception):
    pass

class DatadogAdapter:
    def __init__(self):
        try:
            import pandas as pd
            from datadog import initialize, api
            from dotenv import load_dotenv
        except ImportError:
            raise AdapterError("Datadog dependencies missing.")

        load_dotenv()
        self.api_key = os.getenv("DATADOG_API_KEY")
        self.app_key = os.getenv("DATADOG_APP_KEY")
        self.site = os.getenv("DATADOG_SITE", "us5.datadoghq.com")
        
        if not self.api_key or not self.app_key:
            raise AdapterError("Missing API Keys.")
            
        initialize(api_key=self.api_key, app_key=self.app_key, api_host=f"https://api.{self.site}")
        self.host_filter = os.getenv("DATADOG_HOST_FILTER", "*") 

        # Accumulators
        self._net_sent_acc = 0.0
        self._net_recv_acc = 0.0
        self._last_fetch = 0.0

    def get_metrics(self) -> SystemMetrics:
        now = int(time.time())
        # KEY CHANGE: Look back 60s to avoid nulls
        query_end = now - 60
        start = query_end - 300
        
        queries = {
            "cpu": f"avg:system.cpu.idle{{{self.host_filter}}}",
            "mem": f"avg:system.mem.used{{{self.host_filter}}}",
            "net_out": f"avg:system.net.packets_sent{{{self.host_filter}}}",
            "net_in": f"avg:system.net.packets_recv{{{self.host_filter}}}"
        }
        
        results = {}
        metric_ts = now # Default to now if fail
        
        try:
            from datadog import api
            for key, q in queries.items():
                resp = api.Metric.query(start=start, end=query_end, query=q)
                
                if resp['status'] != 'ok' or 'series' not in resp or not resp['series']:
                    results[key] = 0.0
                    continue
                    
                pointlist = resp['series'][0]['pointlist']
                if not pointlist:
                    results[key] = 0.0
                    continue
                    
                # Take last valid point
                # Datadog returns [ms_timestamp, value] usually? 
                # Actually Datadog Python API returns [sec_timestamp, value]
                # We trust the timestamp from the API to detect lag.
                last_point = pointlist[-1]
                metric_ts = last_point[0] / 1000 if last_point[0] > 10000000000 else last_point[0]
                results[key] = last_point[1] or 0.0

            # Translation
            cpu = 100.0 - results["cpu"]
            mem = results["mem"] / 1024 / 1024
            
            # Net Accumulation
            self._accumulate(results["net_out"], results["net_in"], metric_ts)
            
            return SystemMetrics(
                timestamp=metric_ts, # Use actual data time
                cpu_percent=cpu,
                memory_used_mb=mem,
                net_sent_packets=int(self._net_sent_acc),
                net_recv_packets=int(self._net_recv_acc)
            )

        except Exception as e:
            raise AdapterError(f"Datadog Fetch Error: {e}")

    def _accumulate(self, sent_rate, recv_rate, current_time):
        if self._last_fetch == 0:
            delta = 1.0
        else:
            delta = current_time - self._last_fetch
            # Guard against huge deltas or negative time
            if delta < 0 or delta > 600: delta = 1.0
            
        self._net_sent_acc += (sent_rate * delta)
        self._net_recv_acc += (recv_rate * delta)
        self._last_fetch = current_time
