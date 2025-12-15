"""
Coherence SRE: CLI Entry Point.
"""

import sys
import time
import argparse
from rich.console import Console
from rich.live import Live

from coherence.core.model import CONFIG
from coherence.core.sentinel import CoherenceSentinel
from coherence.ingestion.adapters import LiveAdapter, SimAdapter, MetricAdapter
from coherence.ui.dashboard import make_dashboard
# Import Sprint 3 Memory
from coherence.correlation.correlator import EventCorrelator

def main() -> None:
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

if __name__ == "__main__":
    main()
