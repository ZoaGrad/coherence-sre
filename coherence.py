"""
Coherence SRE: The Variance Sentinel.

This module implements a deterministic analysis engine for distributed systems.
It monitors statistical variance, resource allocation rates, and amplification
ratios to detect system instability before cascading failure.

Copyright (c) 2025 Blackglass Continuum. MIT License.
"""

import time
import argparse
import random
import psutil
import sys
from collections import deque
from dataclasses import dataclass
from typing import Dict, Optional, List, Any

# Third-party imports for the dashboard
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich import box

# --- Modular Logic Imports ---
from detectors import VarianceScanner
from correlator import EventCorrelator, Incident, IncidentType

# --- Configuration & Constants ---

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
            
            import math
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

# --- Adapters (Unchanged) ---
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

# --- UI / Main Loop ---

def make_dashboard(sentinel_data: Dict[str, Any], incident: Optional[Incident]) -> Layout:
    """
    Constructs the Dashboard.
    Now includes Sprint 3 Incident Alerts in the footer.
    """
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )

    # Status Header
    status = sentinel_data.get("status", "BOOT")
    color_map = {"STABLE": "green", "UNSTABLE": "red", "WARMUP": "yellow", "ERROR": "magenta"}
    
    # Override status color if we have a Critical Incident
    if incident and incident.severity == "CRITICAL":
        status = "CRITICAL"
        color_map["CRITICAL"] = "red"
        
    color = color_map.get(status, "white")
    
    header_text = Text(
        " COHERENCE SENTINEL // SYSTEM 5 VETO ENGINE ", 
        style="bold white on black", 
        justify="center"
    )
    layout["header"].update(Panel(header_text, style=f"bold {color}"))

    # Metrics Table
    metrics = sentinel_data.get("metrics", {})
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("Sensor", style="cyan")
    table.add_column("Metric (The Truth)", style="white")
    table.add_column("State", justify="right")

    if metrics and status != "ERROR":
        c_var = metrics.get('cpu_variance', 0.0)
        c_mean = metrics.get('cpu_mean', 0.0)
        c_state = "[red]SEIZURE[/red]" if c_var > CONFIG.cpu_variance_limit else "[green]OK[/green]"
        table.add_row("COMPUTE", f"Variance: {c_var:.2f} (Mean: {c_mean:.1f}%)", c_state)

        m_rate = metrics.get('alloc_rate', 0.0)
        m_state = "[red]FEVER[/red]" if m_rate > CONFIG.alloc_rate_limit_mb_s else "[green]OK[/green]"
        table.add_row("RESOURCE", f"Alloc Rate: {m_rate:.1f} MB/s", m_state)

        n_amp = metrics.get('amp_ratio', 1.0)
        n_state = "[red]AUTO-IMMUNE[/red]" if n_amp > CONFIG.amplification_ratio_limit else "[green]OK[/green]"
        table.add_row("INTENT", f"Amp Ratio: {n_amp:.2f}x", n_state)
    elif status == "ERROR":
         table.add_row("System", f"Internal Error: {sentinel_data.get('error')}", "[bold magenta]FAIL[/bold magenta]")
    else:
        table.add_row("System", "Calibrating baseline...", "[yellow]WARMUP[/yellow]")

    layout["main"].update(Panel(table, title="Real-Time Telemetry"))

    # Footer: Veto or Incident
    veto = sentinel_data.get("veto")
    
    if incident:
        # High-Level Incident overrides Low-Level Veto display
        icon = "🔥" if incident.severity == "CRITICAL" else "⚠️"
        footer_text = f" {icon} [bold red]{incident.type.name} INCIDENT[/bold red] | {incident.description} "
    elif veto:
        footer_text = f" [bold red]VETO TRIGGERED[/bold red] | {veto['reason']} | ACTION: {veto['action']} "
    else:
        footer_text = " [dim]No active veto. System Coherent.[/dim] "
    
    layout["footer"].update(Panel(footer_text, style="white"))

    return layout

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Coherence Sentinel: Variance-based instability detection."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--live", action="store_true", help="Monitor live metrics")
    group.add_argument("--simulate", action="store_true", help="Run simulation")
    args = parser.parse_args()

    adapter: MetricAdapter
    if args.live:
        adapter = LiveAdapter()
    elif args.simulate:
        adapter = SimAdapter()

    sentinel = CoherenceSentinel()
    
    # Sprint 3: Initialize Memory
    correlator = EventCorrelator()
    
    console = Console()
    
    try:
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                metric = adapter.get_metrics()
                sentinel.ingest(metric)
                report = sentinel.analyze()
                
                # Sprint 3: Correlate Events
                incident = correlator.ingest(report)
                
                live.update(make_dashboard(report, incident))
                time.sleep(CONFIG.poll_interval)
    except KeyboardInterrupt:
        sys.exit(0)
