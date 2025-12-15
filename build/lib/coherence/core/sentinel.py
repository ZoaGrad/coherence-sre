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
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List, Any, Union

# Third-party imports
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich import box

# --- Core Imports ---
# We keep the basic scanners for fallback/bootstrap
from ..detection.detectors import VarianceScanner
from ..correlation.correlator import EventCorrelator, Incident, IncidentType

# --- Configuration & Constants ---

@dataclass(frozen=True)
class ThresholdConfig:
    cpu_variance_limit: float = 10.0
    alloc_rate_limit_mb_s: float = 100.0
    amplification_ratio_limit: float = 1.1
    window_size_seconds: int = 60
    poll_interval: float = 1.0
    max_signal_lag_seconds: float = 300.0

CONFIG = ThresholdConfig()

@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_used_mb: float
    net_sent_packets: int
    net_recv_packets: int

class CoherenceSentinel:
    def __init__(self) -> None:
        self.history: deque[SystemMetrics] = deque(maxlen=CONFIG.window_size_seconds)
        self.status: str = "WARMUP"
        
        # Level 1: Basic Physics (Always Available)
        self.variance_scanner = VarianceScanner(threshold_multiplier=2.0)
        self.basic_correlator = EventCorrelator()
        
        # Level 2: Synaptic Brain (Advanced Physics)
        self.advanced_detector = None
        self.advanced_correlator = None
        self.has_brain = False
        
        # Robust Initialization
        try:
            import pandas as pd
            from ..detection.advanced import AdvancedDetector
            from ..correlation.engine import CorrelationEngine as AdvancedCorrelator
            
            # Initialize Advanced Logic
            self.advanced_detector = AdvancedDetector(window_size=CONFIG.window_size_seconds)
            self.advanced_correlator = AdvancedCorrelator()
            
            self.has_brain = True
        except ImportError:
            # Expected if dependencies missing
            pass
        except Exception as e:
            # Bad Brain: Graceful fallback
            print(f"[WARN] Brain init failed: {e}. Running in Lobotomy Mode.")
            self.advanced_detector = None
            self.advanced_correlator = None
            self.has_brain = False
        
    def ingest(self, metrics: SystemMetrics) -> None:
        self.history.append(metrics)

    def analyze(self) -> Dict[str, Any]:
        if len(self.history) < 5:
            return {
                "status": "WARMUP", 
                "metrics": {}, 
                "veto": None, 
                "narrative": None,
                "brain": "advanced" if self.has_brain else "basic"
            }

        # --- Phase 2.3: Hygiene (Blindness Veto) ---
        latest = self.history[-1]
        now = time.time()
        signal_lag = now - latest.timestamp
        
        if signal_lag > CONFIG.max_signal_lag_seconds:
             return {
                "status": "STALE",
                "metrics": {"signal_lag": signal_lag},
                "veto": None,
                "error": f"Signal Lag: {signal_lag:.1f}s > Limit",
                "narrative": None,
                "brain": "advanced" if self.has_brain else "basic"
            }

        try:
            # 1. Calculate Basic Physics (The Fast Path) -> Safety Critical
            # CPU
            cpu_values = [m.cpu_percent for m in self.history]
            variance_result = self.variance_scanner.detect(cpu_values, baseline_variance=1.0)
            cpu_std_dev = math.sqrt(variance_result.score)
            cpu_mean = sum(cpu_values) / len(cpu_values)

            # Mem
            oldest = self.history[0]
            newest = self.history[-1]
            time_delta = newest.timestamp - oldest.timestamp
            mem_delta = newest.memory_used_mb - oldest.memory_used_mb
            alloc_rate = max(0.0, mem_delta / time_delta) if time_delta > 0 else 0.0

            # Net
            s_delta = newest.net_sent_packets - oldest.net_sent_packets
            r_delta = newest.net_recv_packets - oldest.net_recv_packets
            amp_ratio = (s_delta / r_delta) if r_delta > 0 else 1.0

            metrics = {
                "cpu_mean": cpu_mean,
                "cpu_variance": cpu_std_dev,
                "alloc_rate": alloc_rate,
                "amp_ratio": amp_ratio,
                "signal_lag": signal_lag
            }

            # 2. Determine Veto (Basic)
            veto = None
            if cpu_std_dev > CONFIG.cpu_variance_limit:
                veto = {"type": "COMPUTE", "action": "SHED_LOAD", "reason": f"Variance {cpu_std_dev:.1f} > Limit"}
            elif alloc_rate > CONFIG.alloc_rate_limit_mb_s:
                veto = {"type": "RESOURCE", "action": "THROTTLE", "reason": f"Rate {alloc_rate:.1f}MB/s > Limit"}
            elif amp_ratio > CONFIG.amplification_ratio_limit:
                veto = {"type": "INTENT", "action": "CAP_RETRIES", "reason": f"Amp {amp_ratio:.2f}x > Limit"}

            status = "INSTABLE" if veto else "STABLE"
            
            # 3. Advanced Analysis (The Brain)
            # Upgrades the analysis to generate a Narrative
            narrative_incident = None
            
            if self.has_brain and self.advanced_detector and self.advanced_correlator:
                try:
                    import pandas as pd
                    # Convert Deque to DataFrame
                    df = pd.DataFrame([asdict(m) for m in self.history])
                    
                    # Detect Anomalies (DataFrame)
                    # AdvancedDetector expects 'value' column usually. Let's run it on CPU.
                    cpu_df = df[['timestamp', 'cpu_percent']].rename(columns={'cpu_percent': 'value'})
                    cpu_df['host'] = 'local' # Dummy host for single-node CLI
                    
                    # Run logic
                    anomalies = self.advanced_detector.detect_variance_escalation(cpu_df)
                    spikes = self.advanced_detector.detect_spikes(cpu_df)
                    
                    # Combine
                    all_anomalies = pd.concat([anomalies, spikes])
                    if not spikes.empty and anomalies.empty:
                        all_anomalies = spikes # ensure correct logic if one empty
                    
                    # Correlate
                    if not all_anomalies.empty:
                        incidents = self.advanced_correlator.correlate(all_anomalies)
                        if incidents:
                            narrative_incident = incidents[-1] # Take the latest
                except Exception as e:
                    # Advanced Logic Failure: Do NOT crash the Sentinel
                    # Just degrade to Basic
                    pass

            return {
                "status": status, 
                "metrics": metrics, 
                "veto": veto, 
                "narrative": narrative_incident, # The Advanced Object
                "brain": "advanced" if self.has_brain else "basic"
            }

        except Exception as e:
            return {"status": "ERROR", "metrics": {}, "veto": None, "error": str(e)}

# --- Adapters (Standard) ---
class MetricAdapter:
    def get_metrics(self) -> SystemMetrics: raise NotImplementedError

class LiveAdapter(MetricAdapter):
    def get_metrics(self) -> SystemMetrics:
        try:
            m, n, c = psutil.virtual_memory(), psutil.net_io_counters(), psutil.cpu_percent(interval=None)
            return SystemMetrics(time.time(), float(c), m.used/1048576, n.packets_sent, n.packets_recv)
        except: raise RuntimeError("Sensor Fail")

class SimAdapter(MetricAdapter):
    def __init__(self): self.step, self.mem, self.ns, self.nr = 0, 4000.0, 1000, 1000
    def get_metrics(self) -> SystemMetrics:
        self.step += 1; t = time.time()
        # Lag
        if 60 < self.step < 70: t -= 400
        # Seizure
        c = random.choice([10.0, 95.0]) if 20 < self.step < 35 else random.uniform(40,50)
        # Fever
        self.mem += 500.0 if 25 < self.step < 40 else 5.0
        return SystemMetrics(t, c, self.mem, self.ns + self.step*10, self.nr + self.step*10)

# --- UI Loop ---
def make_dashboard(sentinel_data: Dict[str, Any]) -> Layout:
    layout = Layout()
    layout.split_column(Layout(name="header", size=3), Layout(name="main", ratio=1), Layout(name="footer", size=3))
    
    status = sentinel_data.get("status", "BOOT")
    metrics = sentinel_data.get("metrics", {})
    narrative = sentinel_data.get("narrative") # Advanced Incident Object
    veto = sentinel_data.get("veto")
    err = sentinel_data.get("error")
    brain_status = sentinel_data.get("brain", "unknown")

    color_map = {"STABLE": "green", "INSTABLE": "red", "WARMUP": "yellow", "ERROR": "magenta", "STALE": "grey50"}
    
    # Priority: Error > Narrative > Veto > Status
    if narrative and narrative.risk_score > 0.5:
        # Advanced Incident detected
        status_disp = "CRITICAL"
        header_col = "red"
    elif status == "INSTABLE" and not narrative:
        # Basic Veto only
        status_disp = "INSTABLE"
        header_col = "red"
    else:
        status_disp = status
        header_col = color_map.get(status, "white")

    layout["header"].update(Panel(Text(f" COHERENCE SENTINEL // {status_disp} ", style="bold white on black", justify="center"), style=f"bold {header_col}"))
    
    table = Table(box=box.SIMPLE_HEAD, expand=True)
    table.add_column("Sensor", style="cyan"); table.add_column("Metric", style="white"); table.add_column("State", justify="right")
    
    if status == "STALE":
        table.add_row("SYSTEM", f"Lag: {metrics.get('signal_lag',0):.1f}s", "[bold grey50]SIGNAL LOST[/]")
    elif err:
        table.add_row("SYSTEM", f"Error: {err}", "[bold magenta]FAIL[/]")
    elif metrics:
        c_v = metrics.get('cpu_variance',0)
        table.add_row("COMPUTE", f"Var: {c_v:.2f}", "[red]SEIZURE[/]" if c_v > CONFIG.cpu_variance_limit else "[green]OK[/]")
        table.add_row("RESOURCE", f"Rate: {metrics.get('alloc_rate',0):.1f}", "[red]FEVER[/]" if metrics.get('alloc_rate',0)>CONFIG.alloc_rate_limit_mb_s else "[green]OK[/]")
        table.add_row("INTENT", f"Amp: {metrics.get('amp_ratio',1):.2f}", "[red]AUTO-IMMUNE[/]" if metrics.get('amp_ratio',1)>CONFIG.amplification_ratio_limit else "[green]OK[/]")
    else:
        table.add_row("System", "Calibrating...", "[yellow]WARMUP[/]")
        
    layout["main"].update(Panel(table, title="Telemetry"))
    
    # Footer Logic: Narrative > Veto > Default
    if narrative:
        # Advanced Logic Detected a Story
        ft = f" [bold red]⚠️ INCIDENT DETECTED[/] | {narrative.narrative}"
    elif veto:
        ft = f" [bold red]VETO[/] | {veto['reason']} | ACTION: {veto['action']}"
    elif status == "STALE":
        ft = " [dim]Signal lost. Veto disengaged.[/]"
    else:
        ft = f" [dim]System Coherent. Brain Online: {brain_status.upper()}[/]"
        
    layout["footer"].update(Panel(ft, style="white"))
    return layout

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["sim", "live", "datadog"], default="sim")
    args = parser.parse_args()

    adapter = None
    if args.source == "live": adapter = LiveAdapter()
    elif args.source == "sim": adapter = SimAdapter()
    elif args.source == "datadog":
        try:
            from ..ingestion.adapters import DatadogAdapter
            adapter = DatadogAdapter()
        except: sys.exit("[ERROR] Datadog adapter missing.")

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
    except KeyboardInterrupt: sys.exit(0)
