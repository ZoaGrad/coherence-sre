# Coherence SRE: The Variance Sentinel

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Detect system instability 4 hours before the crash.**

Coherence is a lightweight, read-only Sentinel that monitors the *variance* (instability) of your infrastructure rather than just the *average* (load). It detects "Silent Failures"—retry storms, memory churn, and thread thrashing—that traditional dashboards miss until it's too late.

### ⚡ The Problem: Averages Lie
Most monitoring tools alert on thresholds (e.g., `CPU > 80%`).
By the time CPU hits 80%, the cascading failure has already begun.

* **The Seizure:** A system thrashing between 10% and 90% CPU averages out to 50% (Healthy). Coherence sees the **Variance** (80%) and alerts immediately.
* **The Fever:** A system allocating 10GB/s of RAM but clearing it immediately shows flat memory usage. Coherence tracks the **Allocation Rate** and predicts the GC death spiral.
* **The Auto-Immune:** A service retrying failed requests creates a storm. Success rates look fine (eventually 200 OK), but **Amplification Ratio** explodes.

### 🛠 What It Does
Coherence runs as a standalone CLI or sidecar. It ingests standard metrics (from `psutil`, `/proc`, or API hooks) and applies three laws of reliability:

1.  **Compute Seizure Detection:**
    *   *Metric:* CPU Standard Deviation / Window.
    *   *Signal:* High variance with low load = Lock Contention / Thrashing.
2.  **Resource Fever Detection:**
    *   *Metric:* Memory Allocation Rate ($d(RAM)/dt$).
    *   *Signal:* High churn with flat RSS = Garbage Collection Risk.
3.  **Intent Amplification (Auto-Immune):**
    *   *Metric:* Egress Requests / Ingress Requests.
    *   *Signal:* Ratio > 1.1 = Retry Storm / Feedback Loop.

### 🚀 Quick Start (No Database Required)

Coherence is designed to be "drop-in" safe. It is read-only and requires no infrastructure changes.

```bash
# 1. Install
pip install -r requirements.txt

# 2. Run in "Sentinel Mode" (Live Dashboard)
python coherence.py --live

# 3. Run in "Simulation Mode" (Demo)
python coherence.py --simulate
```

### 🧠 The Philosophy

Distributed systems fail because of unbounded recursion and positive feedback loops. Coherence enforces the System 5 Veto:
It does not try to "fix" the bug. It recommends a Non-Algorithmic Veto (Load Shedding, Circuit Breaking) to preserve the system's core integrity.

### 🛡️ License

MIT License. Free for everyone.
