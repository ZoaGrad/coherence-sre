"""
Coherence SRE: Rich TUI Dashboard.
"""

from typing import Dict, Optional, Any
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from coherence.core.model import CONFIG
from coherence.correlation.correlator import Incident

def make_dashboard(sentinel_data: Dict[str, Any], incident: Optional[Incident]) -> Layout:
    """
    Constructs the Dashboard.
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
