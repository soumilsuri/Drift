# Configuration Guide

This guide explains how to configure Drift-SRE for optimal anomaly detection.

## Available Metrics

Drift-SRE monitors the following system metrics by default:

- `cpu_percent` - CPU usage percentage
- `ram_percent` - RAM usage percentage
- `load_avg` - System load average (1-minute)
- `net_sent_mb` - Network bytes sent (cumulative)
- `net_recv_mb` - Network bytes received (cumulative)
- `disk_read_mb` - Disk read bytes (cumulative)
- `disk_write_mb` - Disk write bytes (cumulative)
- `connections` - Number of active network connections

## Algorithms

### CUMSUM (Cumulative Sum)

Best for **stable metrics** like CPU and RAM that have predictable baseline values.

**Parameters:**
- `threshold` (default: 5.0) - Detection sensitivity. Lower values = more sensitive
- `drift` (default: 0.5) - Minimum change to detect. Smaller values = catches smaller changes
- `reference_mean` (optional) - Expected normal value. If not set, uses first value as baseline

**How it works:**
CUMSUM accumulates deviations from a reference mean. When the cumulative deviation exceeds the threshold, an anomaly is detected. It's excellent for detecting sustained shifts.

**Example:**
```python
monitor.configure_metric(
    'cpu_percent',
    algorithm='CUMSUM',
    threshold=25.0,      # Alert when cumulative deviation > 25
    drift=5.0,          # Ignore changes smaller than 5%
    reference_mean=30.0 # Expect CPU around 30%
)
```

### EWMA (Exponentially Weighted Moving Average)

Best for **variable metrics** like network traffic and disk I/O that have changing patterns.

**Parameters:**
- `alpha` (default: 0.3) - Smoothing factor (0-1). Higher = more reactive to recent changes
- `threshold_sigma` (default: 3.0) - Number of standard deviations for anomaly threshold

**How it works:**
EWMA adapts to changing patterns by giving more weight to recent values. It calculates a moving average and variance, then flags values that deviate significantly from the expected range.

**Example:**
```python
monitor.configure_metric(
    'net_sent_mb',
    algorithm='EWMA',
    alpha=0.1,           # Smooth - less reactive to spikes
    threshold_sigma=5.0  # Alert when > 5 standard deviations
)
```

## Default Configurations

Drift-SRE comes with sensible defaults for each metric:

| Metric | Algorithm | Threshold/Alpha | Drift/Sigma | Notes |
|--------|-----------|-----------------|-------------|-------|
| `cpu_percent` | CUMSUM | 25.0 | 5.0 | Only sustained high usage |
| `ram_percent` | CUMSUM | 10.0 | 2.0 | More sensitive (catches leaks) |
| `load_avg` | CUMSUM | 15.0 | 1.0 | System load average |
| `net_sent_mb` | EWMA | 0.1 | 5.0 | Smooth, handles bursts |
| `net_recv_mb` | EWMA | 0.1 | 5.0 | Smooth, handles bursts |
| `disk_read_mb` | EWMA | 0.15 | 4.5 | Moderate sensitivity |
| `disk_write_mb` | EWMA | 0.15 | 4.5 | Moderate sensitivity |
| `connections` | EWMA | 0.15 | 5.0 | Network connections |

## Tuning Recommendations

### Too Many False Positives?

**For CUMSUM:**
- Increase `threshold` (e.g., 25.0 → 35.0)
- Increase `drift` (e.g., 2.0 → 5.0)
- Adjust `reference_mean` to match your actual baseline

**For EWMA:**
- Increase `threshold_sigma` (e.g., 3.0 → 5.0)
- Decrease `alpha` (e.g., 0.3 → 0.1) to be less reactive

### Missing Real Anomalies?

**For CUMSUM:**
- Decrease `threshold` (e.g., 25.0 → 15.0)
- Decrease `drift` (e.g., 5.0 → 2.0)

**For EWMA:**
- Decrease `threshold_sigma` (e.g., 5.0 → 3.0)
- Increase `alpha` (e.g., 0.1 → 0.3) to be more reactive

### Example: Tuning RAM Monitoring

RAM can be volatile, so you might want to catch memory leaks early:

```python
# Very sensitive - catches small increases
monitor.configure_metric(
    'ram_percent',
    algorithm='CUMSUM',
    threshold=5.0,       # Very sensitive
    drift=1.0,          # Catch small changes
    reference_mean=50.0
)
```

Or if you're getting too many alerts:

```python
# Less sensitive - only major issues
monitor.configure_metric(
    'ram_percent',
    algorithm='CUMSUM',
    threshold=20.0,     # Less sensitive
    drift=5.0,         # Only large changes
    reference_mean=60.0
)
```

## When to Use Each Algorithm

**Use CUMSUM when:**
- Metric has a stable baseline (CPU, RAM)
- You want to detect sustained shifts
- Metric doesn't have natural bursts or spikes

**Use EWMA when:**
- Metric is naturally variable (network, disk I/O)
- Metric has bursty patterns
- You want adaptive detection that learns from recent behavior

## Disabling Metrics

You can disable specific metrics:

```python
monitor.configure_metric('net_sent_mb', enabled=False)
```

## Runtime Configuration

You can update configuration at runtime:

```python
# Start with defaults
monitor = DriftMonitor(discord_webhook="...")
monitor.start()

# Later, adjust based on observed behavior
monitor.configure_metric('ram_percent', threshold=15.0)
```

## Getting Current Configuration

```python
config = monitor.get_configuration()
print(config['ram_percent'])
# {'algorithm': 'CUMSUM', 'threshold': 10.0, 'drift': 2.0, ...}
```

