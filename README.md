# drift-sre

Production-ready Python library for statistical drift detection and automated incident enrichment using the Page-Hinkley algorithm.

## Overview

`drift-sre` monitors system metrics in real-time and detects statistical distribution shifts (drift) that indicate potential system issues. Unlike fixed threshold monitoring, it identifies subtle changes that may signal "grey failures" before they become critical.

### The Four Golden Signals

This library monitors key system metrics based on Google's "Four Golden Signals" of observability:

- **Latency**: System Load (1m) - How long requests take
- **Traffic**: Network Throughput - How much demand is being placed on the system
- **Errors**: Socket Errors - Rate of requests that fail
- **Saturation**: CPU, RAM, Disk I/O - How "full" the service is

### What is "Drift"?

Drift occurs when a metric's distribution shifts significantly from its baseline. For example:
- **CPU Usage**: A process starts looping or thrashing (High saturation)
- **RAM Usage**: A potential memory leak causes slow, steady increase
- **Disk I/O**: Hard drive failing or bottlenecks occurring
- **Network Throughput**: Possible DDoS attack or API data burst
- **System Load**: CPU overwhelmed, tasks queuing up
- **Socket Errors**: High number of failed connection attempts

## Quickstart

### Installation

```bash
pip install drift-sre
```

### Basic Usage

```python
from drift_sre import DriftMonitor

# Initialize the monitor
m = DriftMonitor(
    discord_url="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
    metrics=['cpu', 'ram', 'disk_io', 'network', 'load', 'socket_errors'],
    sensitivity=0.05,  # How sensitive to small changes
    threshold=50,      # How much evidence needed to trigger
    interval=1.0       # Check every second
)

# Start monitoring (runs as background daemon thread)
m.start()

# Your application continues running...
# The monitor runs in the background until your process exits
```

### Flask Integration

```python
from flask import Flask
from drift_sre import DriftMonitor

app = Flask(__name__)

# Start drift monitoring
monitor = DriftMonitor(
    discord_url="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
    metrics=['cpu', 'ram'],
    sensitivity=0.05,
    threshold=50,
    interval=1.0
)
monitor.start()

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run()
```

### FastAPI Integration

```python
from fastapi import FastAPI
from drift_sre import DriftMonitor

app = FastAPI()

# Start drift monitoring
monitor = DriftMonitor(
    discord_url="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
    metrics=['cpu', 'ram', 'network'],
    sensitivity=0.05,
    threshold=50,
    interval=1.0
)
monitor.start()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

## Configuration

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sensitivity` (Delta) | 0.05 | Noise gate: Lower values detect tiny shifts; higher values ignore normal jitter |
| `threshold` (Lambda) | 50 | Confidence: How much evidence of drift is needed before triggering. High values prevent false positives |
| `interval` | 1.0 | Sampling rate: How often (in seconds) to check system health |
| `cool_down` | 60 | Seconds between Discord notifications (prevents spam) |
| `alpha` | 0.1 | EMA forgetting factor: Controls how much weight recent values have vs historical mean |

For detailed configuration guidance, see [docs/CONFIG.md](docs/CONFIG.md).

## Thread-Safe Configuration Updates

You can update configuration parameters at runtime (e.g., from a Flask route):

```python
# Update sensitivity (delta)
monitor.update_sensitivity(0.01)

# Update threshold (lambda)
monitor.update_threshold(75)

# Update sampling interval
monitor.update_interval(2.0)

# Update notification cool-down
monitor.update_cool_down(120)
```

## How It Works

### Page-Hinkley Algorithm

The Page-Hinkley test is an online change detection algorithm that monitors a stream of values and detects when the mean of the distribution shifts significantly. The algorithm:

- Detects **changes in distribution**, not just absolute values
- Works in an **online/streaming** fashion (no need to store all historical data)
- Is **adaptive** - learns the baseline automatically from incoming data
- Uses **vectorized NumPy operations** for efficient multi-metric monitoring

For detailed algorithm explanation, see [docs/ALGORITHM.md](docs/ALGORITHM.md).

### Architecture

```
User Application
    ↓
DriftMonitor (daemon thread)
    ├── Collector (psutil) → collects 6 metrics
    ├── Engine (Page-Hinkley) → detects drift
    ├── Snapshot → captures forensic data on drift
    └── Notifier → sends Discord alerts (with cool-down)
```

## Monitored Metrics

| Category | Metric | What Drift Means |
|----------|--------|------------------|
| Saturation | CPU Usage (%) | Process looping or thrashing |
| Saturation | RAM Usage (%) | Potential memory leak (slow, steady drift) |
| Saturation | Disk I/O Wait (%) | Hard drive failing or bottlenecks |
| Traffic | Network Throughput (bytes/sec) | Possible DDoS or API data burst |
| Latency | System Load (1m) | CPU overwhelmed, tasks queuing |
| Errors | Socket Errors | High number of failed connections |

## Documentation

- [Configuration Guide](docs/CONFIG.md) - Detailed parameter explanations and tuning recommendations
- [Algorithm Documentation](docs/ALGORITHM.md) - Mathematical explanation of Page-Hinkley
- [Integration Examples](docs/INTEGRATION.md) - Detailed integration examples for Flask, FastAPI, Django

## Requirements

- Python 3.8+
- numpy >= 1.20.0
- psutil >= 5.9.0
- requests >= 2.25.0

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
