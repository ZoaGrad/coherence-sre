"""
Lab 2: DDoS Simulation & Circuit Breaking (SY0-701: 2.2)
Scenario: A sudden spike in requests causes resource exhaustion.
Objective: Demonstrate how Coherence Sentinel's 'Veto' logic (Variance) detects the storm.
"""
import time
import random
import statistics
from dataclasses import dataclass

@dataclass
class Packet:
    timestamp: float
    size_bytes: int

class SentinelVeto:
    def __init__(self, limit: float):
        self.history = []
        self.variance_limit = limit

    def ingest(self, packet: Packet):
        self.history.append(packet.size_bytes)
        if len(self.history) > 50: self.history.pop(0)

    def check(self) -> bool:
        if len(self.history) < 10: return False
        
        # Calculate Variance
        variance = statistics.variance(self.history)
        
        # If variance explodes (Erratic traffic size or bursts), Trigger Veto
        return variance > self.variance_limit

def simulate_ddos():
    sentinel = SentinelVeto(limit=5000)
    
    print("Phase 1: Normal Traffic")
    for _ in range(20):
        # Normal: Consistent packet sizes
        p = Packet(time.time(), random.randint(100, 150))
        sentinel.ingest(p)
        if sentinel.check():
            print("[FALSE POSITIVE] Sentinel fired too early.")
            return

    print("Phase 2: Attack Start (High Variance)")
    veto_triggered = False
    for _ in range(20):
        # Attack: Huge variance in payloads (fragmentation attacks etc)
        p = Packet(time.time(), random.choice([10, 2000])) 
        sentinel.ingest(p)
        if sentinel.check():
            print(f"[SUCCESS] Veto Triggered! Variance: {statistics.variance(sentinel.history):.2f}")
            veto_triggered = True
            break
            
    assert veto_triggered, "Sentinel failed to detect DDoS variance signature"

if __name__ == "__main__":
    print("Running Security+ Lab 2: DDoS & Veto...")
    try:
        simulate_ddos()
    except AssertionError as e:
        print(f"[FAIL] {e}")
