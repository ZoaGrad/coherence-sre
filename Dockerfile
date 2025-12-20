# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev

# Create venv and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
COPY pyproject.toml .
# Install basic deps + connectors (optional, but good for the image to support them)
COPY src/ src/
COPY README.md .
COPY LICENSE .

RUN pip install --no-cache-dir .[connectors]

# Stage 2: Runner (The Iron Shell)
FROM python:3.11-slim

WORKDIR /app

# Security: Create non-root user
RUN groupadd -r sentinel && useradd -r -g sentinel sentinel

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Application Code
COPY src/ src/
COPY README.md .
COPY LICENSE .

# Permissions
RUN chown -R sentinel:sentinel /app

# Switch to non-root
USER sentinel

# Default Command: Simulation Mode
# Users can override with "--source datadog"
ENTRYPOINT ["python", "-m", "coherence.core.sentinel"]
CMD ["--simulate"]
