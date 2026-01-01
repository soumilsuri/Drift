# API Reference

Complete API documentation for Drift-SRE.

## DriftMonitor

Main class for anomaly detection and monitoring.

### `DriftMonitor.__init__()`

Initialize a new DriftMonitor instance.

**Parameters:**
- `discord_webhook` (str, optional): Discord webhook URL for notifications
- `check_interval` (int, default=5): Seconds between metric checks
- `min_anomaly_duration` (int, default=3): Minimum consecutive anomalies before alerting
- `auto_start` (bool, default=False): Start monitoring immediately
- `enable_recovery_notifications` (bool, default=True): Send notifications when metrics recover
- `custom_configs` (Dict[str, MetricConfig], optional): Custom metric configurations

**Example:**
```python
monitor = DriftMonitor(
    discord_webhook="https://discord.com/api/webhooks/...",
    check_interval=5,
    min_anomaly_duration=3
)
```

### `DriftMonitor.start()`

Start background monitoring in a daemon thread.

**Returns:** None

**Example:**
```python
monitor.start()
```

### `DriftMonitor.stop()`

Stop background monitoring.

**Returns:** None

**Example:**
```python
monitor.stop()
```

### `DriftMonitor.configure_metric()`

Configure a specific metric's detection parameters.

**Parameters:**
- `metric_name` (str): Name of the metric to configure
- `algorithm` (str, default='CUMSUM'): 'CUMSUM' or 'EWMA'
- `threshold` (float, optional): CUMSUM threshold (lower = more sensitive)
- `drift` (float, optional): CUMSUM drift parameter
- `reference_mean` (float, optional): CUMSUM reference mean
- `alpha` (float, optional): EWMA smoothing factor (0-1)
- `threshold_sigma` (float, optional): EWMA threshold in standard deviations
- `enabled` (bool, default=True): Whether to enable this metric

**Returns:** None

**Example:**
```python
monitor.configure_metric(
    'ram_percent',
    threshold=10.0,
    drift=2.0
)
```

### `DriftMonitor.update_metric_config()`

Update configuration for a specific metric using a MetricConfig object.

**Parameters:**
- `metric_name` (str): Name of the metric to update
- `config` (MetricConfig): New MetricConfig object

**Returns:** None

**Example:**
```python
from drift import MetricConfig

config = MetricConfig(
    algorithm='CUMSUM',
    threshold=15.0,
    drift=3.0
)
monitor.update_metric_config('cpu_percent', config)
```

### `DriftMonitor.register_custom_metric()`

Register a custom metric with a collector function.

**Parameters:**
- `name` (str): Name of the custom metric
- `collector` (Callable[[], float]): Function that returns the metric value
- `config` (MetricConfig): Configuration for this metric

**Returns:** None

**Example:**
```python
def get_queue_depth():
    return my_queue.size()

monitor.register_custom_metric(
    'queue_depth',
    get_queue_depth,
    MetricConfig(algorithm='EWMA', threshold_sigma=3.0)
)
```

### `DriftMonitor.check_metrics()`

Check all metrics for anomalies (can be called manually).

**Parameters:**
- `metrics` (Dict[str, float], optional): Metrics to check. If None, collects fresh metrics.

**Returns:** Dict with keys:
- `timestamp` (str): ISO timestamp
- `has_anomalies` (bool): Whether any anomalies were detected
- `anomaly_count` (int): Number of anomalies
- `anomalies` (List[Dict]): List of anomaly details
- `metrics` (Dict): All collected metrics
- `scores` (Dict): Detection scores for all metrics

**Example:**
```python
result = monitor.check_metrics()
if result['has_anomalies']:
    print(f"Found {result['anomaly_count']} anomalies")
```

### `DriftMonitor.get_current_metrics()`

Get the most recently collected metrics (thread-safe).

**Returns:** Dict[str, Any] of metric names to values

**Example:**
```python
metrics = monitor.get_current_metrics()
print(f"CPU: {metrics['cpu_percent']}%")
```

### `DriftMonitor.get_anomaly_history()`

Get history of detected anomalies.

**Returns:** List[Dict] of anomaly detection results (last 100)

**Example:**
```python
history = monitor.get_anomaly_history()
for entry in history[-5:]:  # Last 5
    print(entry['timestamp'], entry['anomaly_count'])
```

### `DriftMonitor.get_configuration()`

Get all metric configurations as a dictionary.

**Returns:** Dict[str, Dict[str, Any]] mapping metric names to their configurations

**Example:**
```python
configs = monitor.get_configuration()
print(configs['ram_percent'])
# {'algorithm': 'CUMSUM', 'threshold': 10.0, ...}
```

### `DriftMonitor.get_config()`

Get configuration for a specific metric.

**Parameters:**
- `metric_name` (str): Name of the metric

**Returns:** MetricConfig or None if not found

**Example:**
```python
config = monitor.get_config('cpu_percent')
print(config.threshold)
```

### `DriftMonitor.reset()`

Reset all detectors and clear history.

**Returns:** None

**Example:**
```python
monitor.reset()
```

## MetricConfig

Configuration class for a single metric.

### `MetricConfig.__init__()`

**Parameters:**
- `algorithm` (str, default='CUMSUM'): 'CUMSUM' or 'EWMA'
- `threshold` (float, default=5.0): CUMSUM threshold
- `drift` (float, default=0.5): CUMSUM drift
- `reference_mean` (float, optional): CUMSUM reference mean
- `alpha` (float, default=0.3): EWMA smoothing factor
- `threshold_sigma` (float, default=3.0): EWMA threshold
- `enabled` (bool, default=True): Whether metric is enabled
- `description` (str, default=""): Description of the metric

**Example:**
```python
from drift import MetricConfig

config = MetricConfig(
    algorithm='CUMSUM',
    threshold=10.0,
    drift=2.0,
    description='RAM monitoring'
)
```

## Exceptions

### `DriftError`

Base exception for all drift-sre errors.

### `ConfigurationError`

Raised when there's an error in configuration.

### `NotificationError`

Raised when notification sending fails.

**Example:**
```python
from drift import DriftMonitor, NotificationError

try:
    monitor = DriftMonitor(discord_webhook="invalid_url")
except NotificationError as e:
    print(f"Notification error: {e}")
```

## Anomaly Dictionary Structure

Anomaly dictionaries returned in results have the following structure:

```python
{
    'metric': str,           # Metric name
    'value': float,          # Current metric value
    'score': float,          # Detection score
    'algorithm': str,        # 'CUMSUM' or 'EWMA'
    'severity': str,         # 'medium' or 'high'
    'duration': int,         # Consecutive anomaly checks
    'timestamp': str,        # ISO timestamp
    'config': dict           # Algorithm-specific config
}
```

