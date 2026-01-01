# Advanced Usage

This guide covers advanced features and patterns for Drift-SRE.

## Custom Metrics

You can register custom metrics that aren't part of the default system metrics.

### Basic Custom Metric

```python
from drift import DriftMonitor, MetricConfig

def get_queue_depth():
    """Return current queue depth"""
    return my_queue.size()

monitor = DriftMonitor(discord_webhook="...")

# Register custom metric
monitor.register_custom_metric(
    name='queue_depth',
    collector=get_queue_depth,
    config=MetricConfig(
        algorithm='EWMA',
        alpha=0.2,
        threshold_sigma=3.0,
        description='Application queue depth'
    )
)

monitor.start()
```

### Custom Metric with State

```python
class ApplicationMetrics:
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
    
    def get_error_rate(self):
        """Calculate error rate"""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100

app_metrics = ApplicationMetrics()

monitor.register_custom_metric(
    'error_rate',
    app_metrics.get_error_rate,
    MetricConfig(
        algorithm='CUMSUM',
        threshold=5.0,
        drift=1.0,
        description='Application error rate percentage'
    )
)
```

### Custom Metric from External Source

```python
import requests

def get_api_response_time():
    """Get API response time from monitoring endpoint"""
    try:
        response = requests.get('http://localhost:8080/metrics', timeout=1)
        data = response.json()
        return data.get('response_time_ms', 0.0)
    except:
        return 0.0

monitor.register_custom_metric(
    'api_response_time',
    get_api_response_time,
    MetricConfig(
        algorithm='EWMA',
        alpha=0.3,
        threshold_sigma=4.0
    )
)
```

## Multiple Monitors

You can run multiple monitors with different configurations:

```python
# Monitor for production
prod_monitor = DriftMonitor(
    discord_webhook="PROD_WEBHOOK",
    check_interval=5,
    min_anomaly_duration=3
)

# Monitor for staging (more sensitive)
staging_monitor = DriftMonitor(
    discord_webhook="STAGING_WEBHOOK",
    check_interval=10,
    min_anomaly_duration=2
)

# Different configurations
prod_monitor.configure_metric('cpu_percent', threshold=30.0)
staging_monitor.configure_metric('cpu_percent', threshold=20.0)

prod_monitor.start()
staging_monitor.start()
```

## Programmatic Alert Handling

You can handle alerts programmatically instead of (or in addition to) Discord:

```python
def handle_anomaly(result):
    """Custom handler for anomalies"""
    if result['has_anomalies']:
        for anomaly in result['anomalies']:
            # Send to custom alerting system
            send_to_pagerduty(anomaly)
            
            # Log to file
            log_anomaly(anomaly)
            
            # Update metrics in monitoring system
            update_prometheus(anomaly)

monitor = DriftMonitor(check_interval=5)

# Manual checking with custom handling
import threading

def check_loop():
    while True:
        result = monitor.check_metrics()
        handle_anomaly(result)
        time.sleep(5)

threading.Thread(target=check_loop, daemon=True).start()
```

## Integration Patterns

### Flask with Graceful Shutdown

```python
from flask import Flask
from drift import DriftMonitor
import atexit

app = Flask(__name__)
monitor = DriftMonitor(
    discord_webhook=os.getenv('DISCORD_WEBHOOK'),
    check_interval=5
)

def shutdown_monitor():
    monitor.stop()

atexit.register(shutdown_monitor)

@app.before_first_request
def start_monitoring():
    monitor.start()

@app.route('/')
def hello():
    return "Hello, World!"
```

### FastAPI with Startup/Shutdown Events

```python
from fastapi import FastAPI
from drift import DriftMonitor
import os

app = FastAPI()
monitor = DriftMonitor(
    discord_webhook=os.getenv('DISCORD_WEBHOOK'),
    check_interval=5
)

@app.on_event("startup")
async def startup_event():
    monitor.start()

@app.on_event("shutdown")
async def shutdown_event():
    monitor.stop()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

### Django with AppConfig

```python
# myapp/apps.py
from django.apps import AppConfig
from drift import DriftMonitor
import os

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    
    def ready(self):
        if not os.environ.get('RUN_MAIN'):
            return  # Skip in migrations
        
        self.monitor = DriftMonitor(
            discord_webhook=os.getenv('DISCORD_WEBHOOK'),
            check_interval=5
        )
        self.monitor.start()
        
        import atexit
        atexit.register(self.monitor.stop)
```

## Conditional Monitoring

Monitor only during certain conditions:

```python
monitor = DriftMonitor(discord_webhook="...")

# Only monitor during business hours
import datetime

def should_monitor():
    hour = datetime.datetime.now().hour
    return 9 <= hour <= 17

def conditional_monitor():
    while True:
        if should_monitor():
            if not monitor.monitoring_active:
                monitor.start()
        else:
            if monitor.monitoring_active:
                monitor.stop()
        time.sleep(60)

threading.Thread(target=conditional_monitor, daemon=True).start()
```

## Metric Grouping

Disable/enable groups of metrics:

```python
# Disable all network metrics
for metric in ['net_sent_mb', 'net_recv_mb', 'connections']:
    monitor.configure_metric(metric, enabled=False)

# Enable only critical metrics
critical_metrics = ['cpu_percent', 'ram_percent']
for metric in monitor.get_configuration().keys():
    if metric not in critical_metrics:
        monitor.configure_metric(metric, enabled=False)
```

## Dynamic Configuration Updates

Update configuration based on time of day or conditions:

```python
import datetime

def update_config_for_time():
    hour = datetime.datetime.now().hour
    
    if 9 <= hour <= 17:  # Business hours
        # More sensitive during business hours
        monitor.configure_metric('cpu_percent', threshold=20.0)
    else:  # Off hours
        # Less sensitive off hours
        monitor.configure_metric('cpu_percent', threshold=40.0)

# Update every hour
def config_updater():
    while True:
        update_config_for_time()
        time.sleep(3600)

threading.Thread(target=config_updater, daemon=True).start()
```

## Exporting Metrics

Export metrics to external systems:

```python
def export_to_prometheus(metrics):
    """Export metrics to Prometheus"""
    from prometheus_client import Gauge
    
    cpu_gauge = Gauge('system_cpu_percent', 'CPU usage')
    ram_gauge = Gauge('system_ram_percent', 'RAM usage')
    
    cpu_gauge.set(metrics['cpu_percent'])
    ram_gauge.set(metrics['ram_percent'])

monitor = DriftMonitor(check_interval=5)

def export_loop():
    while True:
        metrics = monitor.get_current_metrics()
        export_to_prometheus(metrics)
        time.sleep(10)

threading.Thread(target=export_loop, daemon=True).start()
monitor.start()
```

## Testing Your Configuration

Test your configuration before deploying:

```python
# Create test monitor without Discord
test_monitor = DriftMonitor(check_interval=1)

# Configure as needed
test_monitor.configure_metric('ram_percent', threshold=10.0)

# Simulate metrics
test_metrics = {
    'ram_percent': 50.0,
    'cpu_percent': 30.0,
    # ... other metrics
}

# Check for anomalies
result = test_monitor.check_metrics(test_metrics)
print(result)
```

## Performance Considerations

- **Check Interval:** Lower intervals (1-2s) increase CPU usage. 5-10s is usually sufficient.
- **Metric Count:** More metrics = more CPU. Disable metrics you don't need.
- **History Size:** Anomaly history is limited to 100 entries to prevent memory growth.
- **Thread Safety:** All operations are thread-safe, but avoid frequent configuration changes.

## Best Practices

1. **Start Simple:** Use defaults first, tune based on actual behavior
2. **Monitor Gradually:** Enable metrics one at a time
3. **Test Changes:** Test configuration changes in staging first
4. **Review History:** Regularly review anomaly history to tune thresholds
5. **Document Config:** Keep track of why you changed each configuration
6. **Graceful Shutdown:** Always stop monitors during application shutdown

