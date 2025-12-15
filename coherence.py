import time
import math
import argparse
import random
import psutil
import sys
from collections import deque
from dataclasses import dataclass
from typing import Dict, Optional

# Third-party imports for the dashboard
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich import box

# --- Configuration ---
CONFIG = {
    "window_size_seconds": 60,
    "poll_interval": 1.0,
    "thresholds": {
        # Sensor A: Compute - StdDev > 10%
        "cpu_variance_limit": 10.0,
        # Sensor B: Resource - Rate > 100MB/s
        "alloc_rate_limit_mb_s": 100.0,
        # Sensor C: Intent - Egress/Ingress > 1.1x
        "amplification_ratio_limit": 1.1,
    }
}

@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_used_mb: float
    net_sent_packets: int
    net_recv_packets: int

class CoherenceSentinel:
    """
    The Core Logic.
    Deterministic analysis engine. Calculates Variance, Rates, and Ratios.
    """
    def __init__(self):
        self.history: deque[SystemMetrics] = deque(maxlen=CONFIG["window_size_seconds"])
        self.status = "WARMUP"
        self.last_veto = None

    def ingest(self, metrics: SystemMetrics):
        self.history.append(metrics)

    def analyze(self) -> Dict:
        if len(self.history) < 5:
            return {"status": "WARMUP", "metrics": {}, "veto": None}

        # --- Sensor 1: CPU Variance (Seizure Detection) ---
        cpu_values = [m.cpu_percent for m in self.history]
        cpu_mean = sum(cpu_values) / len(cpu_values)
        variance = sum((x - cpu_mean) ** 2 for x in cpu_values) / len(cpu_values)
        cpu_std_dev = math.sqrt(variance)

        # --- Sensor 2: Memory Allocation Rate (Fever Detection) ---
        # d(Memory)/d(Time) over the window
        time_delta = self.history[-1].timestamp - self.history[0].timestamp
        mem_delta = self.history[-1].memory_used_mb - self.history[0].memory_used_mb
        # We only care about positive growth (leaks/churn)
        alloc_rate_mb_s = max(0, mem_delta / time_delta) if time_delta > 0 else 0

        # --- Sensor 3: Amplification Ratio (Auto-Immune Detection) ---
        # Packets Sent / Packets Recv (Proxy for Downstream/Upstream ratio)
        sent_delta = self.history[-1].net_sent_packets - self.history[0].net_sent_packets
        recv_delta = self.history[-1].net_recv_packets - self.history[0].net_recv_packets
        
        # Avoid div/0
        amp_ratio = (sent_delta / recv_delta) if recv_delta > 0 else 1.0

        metrics = {
            "cpu_mean": cpu_mean,
            "cpu_variance": cpu_std_dev,
            "alloc_rate": alloc_rate_mb_s,
            "amp_ratio": amp_ratio
        }

        # --- The Veto Engine ---
        veto = None
        if cpu_std_dev > CONFIG["thresholds"]["cpu_variance_limit"]:
            veto = {"type": "COMPUTE", "action": "SHED_LOAD", "reason": f"Variance {cpu_std_dev:.1f} > Limit"}
        elif alloc_rate_mb_s > CONFIG["thresholds"]["alloc_rate_limit_mb_s"]:
            veto = {"type": "RESOURCE", "action": "THROTTLE", "reason": f"Rate {alloc_rate_mb_s:.1f}MB/s > Limit"}
        elif amp_ratio > CONFIG["thresholds"]["amplification_ratio_limit"]:
            veto = {"type": "INTENT", "action": "CAP_RETRIES", "reason": f"Amp {amp_ratio:.2f}x > Limit"}

        status = "INSTABLE" if veto else "STABLE"
        return {"status": status, "metrics": metrics, "veto": veto}

# --- Adapters ---

class LiveAdapter:
    def get_metrics(self) -> SystemMetrics:
        mem = psutil.virtual_memory()
        net = psutil.net_io_counters()
        # Non-blocking CPU call
        cpu = psutil.cpu_percent(interval=None) 
        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu,
            memory_used_mb=mem.used / 1024 / 1024,
            net_sent_packets=net.packets_sent,
            net_recv_packets=net.packets_recv
        )

class SimAdapter:
    def __init__(self):
        self.step = 0
        self.base_net_sent = 1000
        self.base_net_recv = 1000
        self.base_mem = 4000

    def get_metrics(self) -> SystemMetrics:
        self.step += 1
        t = time.time()
        
        # Simulate "Seizure" at step 20-30
        if 20 < self.step < 30:
            cpu = random.choice([10.0, 90.0]) # High Variance
        else:
            cpu = random.uniform(40, 50) # Stable

        # Simulate "Fever" at step 40-50
        mem_churn = 500 if 40 < self.step < 50 else 5
        self.base_mem += mem_churn

        return SystemMetrics(
            timestamp=t,
            cpu_percent=cpu,
            memory_used_mb=self.base_mem,
            net_sent_packets=self.base_net_sent + (self.step * 10),
            net_recv_packets=self.base_net_recv + (self.step * 10)
        )

# --- UI / Main Loop ---

def make_dashboard(sentinel_data: Dict) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )

    # Status Header
    status = sentinel_data.get("status", "BOOT")
    color = "green" if status == "STABLE" else "red" if status == "INSTABLE" else "yellow"
    
    header_text = Text(" COHERENCE SENTINEL // SYSTEM 5 VETO ENGINE ", style="bold white on black", justify="center")
    layout["header"].update(Panel(header_text, style=f"bold {color}"))

    # Metrics Table
    metrics = sentinel_data.get("metrics", {})
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("Sensor", style="cyan")
    table.add_column("Metric (The Truth)", style="white")
    table.add_column("State", justify="right")

    if metrics:
        # CPU
        c_var = metrics['cpu_variance']
        c_state = "[red]SEIZURE[/red]" if c_var > CONFIG["thresholds"]["cpu_variance_limit"] else "[green]OK[/green]"
        table.add_row("COMPUTE", f"Variance: {c_var:.2f} (Mean: {metrics['cpu_mean']:.1f}%)", c_state)

        # Mem
        m_rate = metrics['alloc_rate']
        m_state = "[red]FEVER[/red]" if m_rate > CONFIG["thresholds"]["alloc_rate_limit_mb_s"] else "[green]OK[/green]"
        table.add_row("RESOURCE", f"Alloc Rate: {m_rate:.1f} MB/s", m_state)

        # Net
        n_amp = metrics['amp_ratio']
        n_state = "[red]AUTO-IMMUNE[/red]" if n_amp > CONFIG["thresholds"]["amplification_ratio_limit"] else "[green]OK[/green]"
        table.add_row("INTENT", f"Amp Ratio: {n_amp:.2f}x", n_state)
    else:
        table.add_row("System", "Calibrating baseline...", "[yellow]WARMUP[/yellow]")

    layout["main"].update(Panel(table, title="Real-Time Telemetry"))

    # Veto Footer
    veto = sentinel_data.get("veto")
    if veto:
        veto_text = f" [bold red]VETO TRIGGERED[/bold red] | {veto['reason']} | ACTION: {veto['action']} "
    else:
        veto_text = " [dim]No active veto. System Coherent.[/dim] "
    
    layout["footer"].update(Panel(veto_text, style="white"))

    return layout

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coherence Sentinel: Variance-based instability detection.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--live", action="store_true", help="Monitor live system metrics via psutil")
    group.add_argument("--simulate", action="store_true", help="Run in simulation mode with synthetic data")
    args = parser.parse_args()

    if args.live:
        adapter = LiveAdapter()
    elif args.simulate:
        adapter = SimAdapter()

    sentinel = CoherenceSentinel()
    console = Console()
    
    try:
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                metric = adapter.get_metrics()
                sentinel.ingest(metric)
                report = sentinel.analyze()
                live.update(make_dashboard(report))
                time.sleep(CONFIG["poll_interval"])
    except KeyboardInterrupt:
        print("\nSentinel Offline.")
