# Drift-SRE

**Real-time Anomaly Detection Library for SRE**

Drift-SRE is a lightweight, embeddable Python library that monitors server metrics and detects anomalies in real-time, with intelligent Discord notifications. Perfect for integrating into your existing applications without requiring separate services.

## Quick Start

```python
from drift import DriftMonitor

# Initialize with Discord webhook
monitor = DriftMonitor(
    discord_webhook="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
    check_interval=5  # seconds
)

# Customize specific metrics (optional)
monitor.configure_metric('ram_percent', threshold=10.0, drift=2.0)
monitor.configure_metric('cpu_percent', threshold=25.0, drift=5.0)

# Start monitoring in background
monitor.start()

# That's it! Monitor runs in background thread
```

## Installation

```bash
pip install drift-sre
```

## Features

- **Embeddable**: Runs in the same process as your application
- **Zero External Services**: No separate monitoring server required (except Discord for notifications)
- **Smart Defaults**: Sensible configurations for all system metrics out of the box
- **Per-Metric Tuning**: Configure each metric independently with CUMSUM or EWMA algorithms
- **Discord Notifications**: Beautiful embeds with rate limiting and recovery notifications
- **Custom Metrics**: Register your own metrics with custom collectors
- **Thread-Safe**: Safe to use with Flask, FastAPI, Django, and other frameworks

## Monitored Metrics

- CPU usage percentage
- RAM usage percentage
- Disk read/write throughput
- Network sent/received bytes
- System load average
- Active network connections

## Algorithms

### CUMSUM (Cumulative Sum)
Best for stable metrics like CPU and RAM. Detects sustained shifts from normal behavior.

### EWMA (Exponentially Weighted Moving Average)
Best for variable metrics like network traffic and disk I/O. Adapts to changing patterns.

## Documentation

- [Getting Started](docs/getting-started.md) - Installation and basic setup
- [Configuration Guide](docs/configuration.md) - Tuning detection parameters
- [Metrics Guide](docs/metrics-guide.md) - Understanding each metric
- [API Reference](docs/api-reference.md) - Complete API documentation
- [Advanced Usage](docs/advanced.md) - Custom metrics and integrations
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Examples

See the [examples](examples/) directory for:
- Basic usage
- Flask integration
- FastAPI integration
- Custom metrics

## Requirements

- Python 3.8+
- psutil (for system metrics)
- requests (for Discord webhooks)

## License

MIT License

## Contributing

Contributions welcome! Please see our contributing guidelines.

