import time
import os
import random
import psutil
from typing import Any
from ..core.model import SystemMetrics

class AdapterError(Exception):
    pass

class MetricAdapter:
    def get_metrics(self) -> SystemMetrics: raise NotImplementedError

class LiveAdapter(MetricAdapter):
    def get_metrics(self) -> SystemMetrics:
        try:
            m, n, c = psutil.virtual_memory(), psutil.net_io_counters(), psutil.cpu_percent(interval=None)
            # Use real timestamp
            return SystemMetrics(time.time(), float(c), m.used/1048576, n.packets_sent, n.packets_recv)
        except Exception: raise RuntimeError("Sensor Fail")

class SimAdapter(MetricAdapter):
    def __init__(self) -> None: 
        self.step = 0
        self.mem = 4000.0
        self.ns = 1000
        self.nr = 1000
        
    def get_metrics(self) -> SystemMetrics:
        self.step += 1; t = time.time()
        # Lag
        if 60 < self.step < 70: t -= 400
        # Seizure
        c = random.choice([10.0, 95.0]) if 20 < self.step < 35 else random.uniform(40,50)
        # Fever
        self.mem += 500.0 if 25 < self.step < 40 else 5.0
        return SystemMetrics(t, c, self.mem, self.ns + self.step*10, self.nr + self.step*10)

class DatadogAdapter(MetricAdapter):
    def __init__(self) -> None:
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
        self._net_sent_acc: float = 0.0
        self._net_recv_acc: float = 0.0
        self._last_fetch: float = 0.0

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
        metric_ts: float = float(now) # Default to now if fail
        
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
                last_point = pointlist[-1]
                # Cast timestamp to float
                raw_ts = float(last_point[0])
                metric_ts = raw_ts / 1000.0 if raw_ts > 10000000000 else raw_ts
                results[key] = float(last_point[1] or 0.0)

            # Translation
            cpu = 100.0 - results.get("cpu", 0.0)
            mem = results.get("mem", 0.0) / 1024 / 1024
            
            # Net Accumulation
            self._accumulate(results.get("net_out", 0.0), results.get("net_in", 0.0), metric_ts)
            
            return SystemMetrics(
                timestamp=metric_ts, 
                cpu_percent=cpu,
                memory_used_mb=mem,
                net_sent_packets=int(self._net_sent_acc),
                net_recv_packets=int(self._net_recv_acc)
            )

        except Exception as e:
            raise AdapterError(f"Datadog Fetch Error: {e}")

    def _accumulate(self, sent_rate: float, recv_rate: float, current_time: float) -> None:
        if self._last_fetch == 0:
            delta = 1.0
        else:
            delta = current_time - self._last_fetch
            # Guard against huge deltas or negative time
            if delta < 0 or delta > 600: delta = 1.0
            
        self._net_sent_acc += (sent_rate * delta)
        self._net_recv_acc += (recv_rate * delta)
        self._last_fetch = current_time
