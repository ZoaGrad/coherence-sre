
"""
Coherence SRE: The Variance Sentinel.
"""
import time
import math
import argparse
import random
import psutil
import sys
from collections import deque
from dataclasses import dataclass
from typing import Dict, Optional, List, Any, Union

# Third-party imports
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich import box

# ... [Imports from detection/correlation unchanged] ...
from ..detection.detectors import VarianceScanner
# from ..correlation.correlator import EventCorrelator # Uncomment when fully ready

# ... [CONFIG and ThresholdConfig unchanged] ...
@dataclass(frozen=True)
class ThresholdConfig:
    cpu_variance_limit: float = 10.0
    alloc_rate_limit_mb_s: float = 100.0
    amplification_ratio_limit: float = 1.1
    window_size_seconds: int = 60
    poll_interval: float = 1.0

CONFIG = ThresholdConfig()

@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_used_mb: float
    net_sent_packets: int
    net_recv_packets: int

# ... [CoherenceSentinel Class unchanged] ...
class CoherenceSentinel:
    def __init__(self) -> None:
        self.history: deque[SystemMetrics] = deque(maxlen=CONFIG.window_size_seconds)
        self.status: str = "WARMUP"
        self.variance_scanner = VarianceScanner(window_size=CONFIG.window_size_seconds)
        
    def ingest(self, metrics: SystemMetrics) -> None:
        self.history.append(metrics)

    def analyze(self) -> Dict[str, Any]:
        if len(self.history) < 5:
            return {"status": "WARMUP", "metrics": {}, "veto": None}
        
        try:
            # CPU
            cpu_values = [m.cpu_percent for m in self.history]
            variance_result = self.variance_scanner.detect(cpu_values, baseline_variance=1.0)
            cpu_variance = variance_result.score
            cpu_std_dev = math.sqrt(cpu_variance)
            cpu_mean = sum(cpu_values) / len(cpu_values)

            # Mem
            oldest = self.history[0]
            newest = self.history[-1]
            time_delta = newest.timestamp - oldest.timestamp
            mem_delta = newest.memory_used_mb - oldest.memory_used_mb
            alloc_rate_mb_s = max(0.0, mem_delta / time_delta) if time_delta > 0 else 0.0

            # Net
            sent_delta = newest.net_sent_packets - oldest.net_sent_packets
            recv_delta = newest.net_recv_packets - oldest.net_recv_packets
            amp_ratio = (sent_delta / recv_delta) if recv_delta > 0 else 1.0

            metrics = {
                "cpu_mean": cpu_mean,
                "cpu_variance": cpu_std_dev,
                "alloc_rate": alloc_rate_mb_s,
                "amp_ratio": amp_ratio
            }

            veto = None
            if cpu_std_dev > CONFIG.cpu_variance_limit:
                veto = {"type": "COMPUTE", "action": "SHED_LOAD", "reason": f"Variance {cpu_std_dev:.1f} > Limit"}
            elif alloc_rate_mb_s > CONFIG.alloc_rate_limit_mb_s:
                veto = {"type": "RESOURCE", "action": "THROTTLE", "reason": f"Rate {alloc_rate_mb_s:.1f}MB/s > Limit"}
            elif amp_ratio > CONFIG.amplification_ratio_limit:
                veto = {"type": "INTENT", "action": "CAP_RETRIES", "reason": f"Amp {amp_ratio:.2f}x > Limit"}

            status = "INSTABLE" if veto else "STABLE"
            return {"status": status, "metrics": metrics, "veto": veto}
        except Exception as e:
            return {"status": "ERROR", "metrics": {}, "veto": None, "error": str(e)}

# --- Adapters ---
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
        if 20 < self.step < 30:
            cpu = random.choice([10.0, 90.0]) 
        else:
            cpu = random.uniform(40.0, 50.0)
        mem_churn = 500.0 if 40 < self.step < 50 else 5.0
        self.base_mem += mem_churn
        return SystemMetrics(t, cpu, self.base_mem, 
                             self.base_net_sent + (self.step * 10), 
                             self.base_net_recv + (self.step * 10))

# --- UI Loop (Simplified for brevity in update, keep original) ---
def make_dashboard(sentinel_data: Dict[str, Any]) -> Layout:
    # ... [Keep existing UI code] ...
    # (Assuming UI code is preserved or imported)
    pass 

# For the purpose of this file generation, I need to include the UI code 
# or else the script breaks. I will re-include the minimal UI logic.
def make_dashboard(sentinel_data: Dict[str, Any]) -> Layout:
    layout = Layout()
    layout.split_column(Layout(name="header", size=3), Layout(name="main", ratio=1), Layout(name="footer", size=3))
    status = sentinel_data.get("status", "BOOT")
    color = {"STABLE": "green", "INSTABLE": "red", "WARMUP": "yellow", "ERROR": "magenta"}.get(status, "white")
    layout["header"].update(Panel(Text(" COHERENCE SENTINEL ", style="bold white on black", justify="center"), style=f"bold {color}"))
    
    metrics = sentinel_data.get("metrics", {})
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("Sensor", style="cyan"); table.add_column("Metric", style="white"); table.add_column("State", justify="right")
    
    if metrics and status != "ERROR":
        table.add_row("COMPUTE", f"Var: {metrics.get('cpu_variance',0):.2f}", "[red]SEIZURE[/red]" if metrics.get('cpu_variance',0)>CONFIG.cpu_variance_limit else "[green]OK[/green]")
        table.add_row("RESOURCE", f"Rate: {metrics.get('alloc_rate',0):.1f}", "[red]FEVER[/red]" if metrics.get('alloc_rate',0)>CONFIG.alloc_rate_limit_mb_s else "[green]OK[/green]")
        table.add_row("INTENT", f"Amp: {metrics.get('amp_ratio',1):.2f}", "[red]AUTO-IMMUNE[/red]" if metrics.get('amp_ratio',1)>CONFIG.amplification_ratio_limit else "[green]OK[/green]")
    elif status == "ERROR":
        table.add_row("System", f"Error: {sentinel_data.get('error')}", "[bold magenta]FAIL[/bold magenta]")
    else:
        table.add_row("System", "Calibrating...", "[yellow]WARMUP[/yellow]")
        
    layout["main"].update(Panel(table, title="Telemetry"))
    veto = sentinel_data.get("veto")
    layout["footer"].update(Panel(f"[bold red]VETO[/] {veto['reason']}" if veto else "[dim]Coherent[/dim]", style="white"))
    return layout

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coherence Sentinel")
    parser.add_argument("--source", choices=["sim", "live", "datadog"], default="sim", help="Telemetry source")
    args = parser.parse_args()

    adapter: MetricAdapter
    if args.source == "live":
        adapter = LiveAdapter()
    elif args.source == "sim":
        adapter = SimAdapter()
    elif args.source == "datadog":
        try:
            from ..ingestion.adapters import DatadogAdapter
            adapter = DatadogAdapter()
        except ImportError:
            print("[ERROR] Datadog adapter missing. Install with: pip install '.[connectors]'")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Datadog init failed: {e}")
            sys.exit(1)

    sentinel = CoherenceSentinel()
    console = Console()
    
    try:
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                metric = adapter.get_metrics()
                sentinel.ingest(metric)
                report = sentinel.analyze()
                live.update(make_dashboard(report))
                time.sleep(CONFIG.poll_interval)
    except KeyboardInterrupt:
        sys.exit(0)
