"""
Coherence SRE: Temporal Event Correlation.

This module implements the 'Memory' of the Sentinel. It tracks a stream of
instantaneous detection events to identify complex failure patterns over time,
such as cascading failures or flapping states.

Copyright (c) 2025 Blackglass Continuum. MIT License.
"""

import time
from collections import deque, Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class IncidentType(Enum):
    """Classifications of temporal instability."""
    NONE = "NONE"
    FLAPPING = "FLAPPING"  # Rapid oscillation between Stable/Instable
    CASCADING = "CASCADE"  # Multiple sensor types triggering in sequence
    PERSISTENT = "PERSISTENT" # Single sensor failing for extended duration

@dataclass
class Incident:
    """A correlated alert describing a pattern of failure."""
    type: IncidentType
    severity: str # "WARN", "CRITICAL"
    description: str
    timestamp: float
    duration_seconds: float

class EventCorrelator:
    """
    Analyzes the stream of analysis reports to find temporal patterns.
    """
    
    def __init__(self, history_window: int = 10, flapping_threshold: int = 3):
        """
        Args:
            history_window (int): Number of recent analysis ticks to track.
            flapping_threshold (int): State changes required to trigger 'Flapping'.
        """
        # We track the full analysis objects
        self.history: deque[Dict[str, Any]] = deque(maxlen=history_window)
        self.flapping_threshold = flapping_threshold
        self.active_incident: Optional[Incident] = None
        self.start_time: Optional[float] = None

    def ingest(self, analysis_report: Dict[str, Any]) -> Optional[Incident]:
        """
        Ingests a single analysis report and checks for patterns.
        
        Args:
            analysis_report: The dictionary returned by CoherenceSentinel.analyze()
        
        Returns:
            Optional[Incident]: An incident report if a pattern is matched, else None.
        """
        self.history.append(analysis_report)
        
        # 1. Check for Flapping (Oscillation)
        if self._detect_flapping():
            return Incident(
                type=IncidentType.FLAPPING,
                severity="WARN",
                description="System is oscillating (Flapping) between Stable and Unstable.",
                timestamp=time.time(),
                duration_seconds=0.0 # Flapping is instantaneous state logic
            )

        # 2. Check for Cascading Failure (Multi-Sensor)
        cascade = self._detect_cascade()
        if cascade:
            return Incident(
                type=IncidentType.CASCADING,
                severity="CRITICAL",
                description=f"Cascading Failure detected: {cascade}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
            
        return None

    def _detect_flapping(self) -> bool:
        """
        Returns True if the system status has changed frequently in the window.
        """
        # Original Guard: "if len(self.history) < self.history.maxlen:"
        # Architect Note: We should probably start detecting even before window is full.
        # But per spec, I will stick to what was provided or safely strict logic. A partial history flapping is valid.
        # Let's start usage if we have at least 3 items.
        if len(self.history) < 3:
            return False

        transitions = 0
        last_status = self.history[0].get("status")
        
        for report in list(self.history)[1:]:
            current_status = report.get("status")
            if current_status != last_status and current_status != "WARMUP": # Ignore warmup transitions ideally? Or count them?
                transitions += 1
            last_status = current_status
            
        return transitions >= self.flapping_threshold

    def _detect_cascade(self) -> Optional[str]:
        """
        Returns a string description if multiple DISTINCT veto types 
        have fired within the window.
        """
        veto_types = set()
        for report in self.history:
            veto = report.get("veto")
            if veto:
                veto_types.add(veto.get("type"))
        
        # If we see COMPUTE + RESOURCE or COMPUTE + INTENT, etc.
        if len(veto_types) >= 2:
            return " + ".join(sorted(list(veto_types)))
        
        return None
