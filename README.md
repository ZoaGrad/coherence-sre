# Coherence SRE: The Variance Sentinel

[![Coherence CI](https://github.com/ZoaGrad/coherence-sre/actions/workflows/main.yml/badge.svg)](https://github.com/ZoaGrad/coherence-sre/actions/workflows/main.yml)


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/Status-Enterprise%20v0.2.0-green.svg)]()

**Detect system instability 4 hours before the crash.**

Coherence is a deterministic SRE engine that monitors the *variance* (instability) of your infrastructure rather than just the *average* (load). It detects "Silent Failures"—retry storms, memory churn, and thread thrashing—that traditional dashboards miss.

### ⚡ The Problem: Averages Lie

Most monitoring tools alert on thresholds (e.g., `CPU > 80%`). By the time CPU hits 80%, the cascading failure has already begun.

* **Seizure (Computational Entropy):** Detects when variance explodes while averages remain normal.
* **Fever (Resource Leaks):** Tracks allocation velocity (MB/s) rather than just capacity.
* **Auto-Immune (Retry Storms):** Identifies amplification ratios in network traffic.

### 🛠 Architecture (Enterprise V0.2.0)

Coherence enforces a strict, modular separation of concerns:

```
src/coherence/
├── core/           # The Sentinel (State Management)
├── detection/      # The Physics (Variance, MAD, Robust Z-Score)
├── correlation/    # The Memory (Temporal Logic, Incidents)
└── ingestion/      # The Senses (Adapters, Connectors)
```

### 🚀 Quick Start (Flight Simulator)

We include a deterministic "Flight Simulator" that generates a synthetic cascading failure (Compute Seizure → Memory Fever) to demonstrate the engine's capability without touching your production.

```bash
# 1. Install Dependencies
pip install -e .

# 2. Run the Flight Simulator
# (Requires pandas/numpy for simulation)
pip install pandas numpy 
python examples/flight_simulator.py
```

**Output:**
```text
[Running Advanced Detection...]
Detected 319 anomalies.

[Running Correlation Engine...]
--- INCIDENT #1 ---
Host: host-001
Risk Score: 0.50
Duration: 19:20:29 - 19:25:47
Narrative: Detected instability on host-001. Pattern: COMPUTE SEIZURE (High Variance).
```

### 🧠 The Philosophy: System 5 Veto

Distributed systems fail because of unbounded recursion and positive feedback loops. Coherence enforces the **System 5 Veto**: It does not "fix" the bug. It recommends a Non-Algorithmic Veto (Load Shedding, Circuit Breaking) to preserve the system's core integrity.

### 🛡️ License

MIT License. Free for everyone.

## 🔌 Live Ingestion (Optional)

Coherence can ingest real telemetry from providers like Datadog. This is **strictly optional**. The tool remains read-only and air-gapped by default.

### Datadog Setup
1. Install optional dependencies:
   ```bash
   pip install ".[connectors]"
   ```

2. Create a .env file (do not commit this):
   ```bash
   cp .env.example .env
   ```

3. Add your keys:
   ```env
   DATADOG_API_KEY=your_key
   DATADOG_APP_KEY=your_key
   DATADOG_SITE=us5.datadoghq.com
   ```

4. Run with source:
   ```bash
   python -m coherence.core.sentinel --source datadog
   ```

> **Note on Physics**: Datadog returns metrics as rates (e.g., packets/sec). Coherence internally integrates these rates back into cumulative counters to satisfy the Variance Sentinel's differential logic.

## 🐳 Deployment (Docker)

Coherence is designed to run as a sidecar container in Kubernetes or ECS.

### Build
```bash
docker build -t coherence-sre .
```

### Run (Simulation)
```bash
docker run -it --rm coherence-sre
```

### Run (Production / Datadog)
```bash
docker run -it --rm --env-file .env coherence-sre --source datadog
```