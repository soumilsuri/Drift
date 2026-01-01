# Getting Started

This guide will help you get started with Drift-SRE in just a few minutes.

## Installation

Install drift-sre using pip:

```bash
pip install drift-sre
```

## Discord Webhook Setup

Before you can receive notifications, you'll need to create a Discord webhook:

1. Open your Discord server
2. Go to Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Give it a name (e.g., "Server Monitor")
5. Choose a channel for notifications
6. Copy the webhook URL

The webhook URL will look like:
```
https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz
```

## Basic Usage

Here's a minimal example that gets you started:

```python
from drift import DriftMonitor

# Initialize monitor with Discord webhook
monitor = DriftMonitor(
    discord_webhook="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
    check_interval=5  # Check metrics every 5 seconds
)

# Start monitoring
monitor.start()

# Your application continues running...
# Monitor runs in background thread
```

That's it! The monitor will:
- Collect system metrics every 5 seconds
- Detect anomalies using smart defaults
- Send Discord notifications when anomalies are detected
- Send recovery notifications when metrics return to normal

## Customizing Detection

You can customize how sensitive the detection is for each metric:

```python
from drift import DriftMonitor

monitor = DriftMonitor(
    discord_webhook="YOUR_WEBHOOK_URL",
    check_interval=5
)

# Make RAM monitoring more sensitive
monitor.configure_metric(
    'ram_percent',
    threshold=10.0,  # Lower = more sensitive
    drift=2.0         # Smaller = catches smaller changes
)

# Make CPU monitoring less sensitive (only major spikes)
monitor.configure_metric(
    'cpu_percent',
    threshold=30.0,   # Higher = less sensitive
    drift=10.0        # Larger = only big changes
)

monitor.start()
```

## Integration Examples

### Flask

```python
from flask import Flask
from drift import DriftMonitor

app = Flask(__name__)

# Initialize monitor
monitor = DriftMonitor(
    discord_webhook="YOUR_WEBHOOK_URL",
    check_interval=5
)
monitor.start()

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run()
```

### FastAPI

```python
from fastapi import FastAPI
from drift import DriftMonitor

app = FastAPI()

# Initialize monitor
monitor = DriftMonitor(
    discord_webhook="YOUR_WEBHOOK_URL",
    check_interval=5
)
monitor.start()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

### Django

In your `settings.py`:

```python
# settings.py
import os
from drift import DriftMonitor

# Initialize monitor
DRIFT_MONITOR = DriftMonitor(
    discord_webhook=os.getenv("DISCORD_WEBHOOK_URL"),
    check_interval=5
)
DRIFT_MONITOR.start()
```

In your `apps.py`:

```python
# apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        from django.conf import settings
        if hasattr(settings, 'DRIFT_MONITOR'):
            settings.DRIFT_MONITOR.start()
```

## Stopping the Monitor

To stop monitoring (e.g., during application shutdown):

```python
monitor.stop()
```

## Next Steps

- Read the [Configuration Guide](configuration.md) to learn about tuning detection parameters
- Check out the [Metrics Guide](metrics-guide.md) to understand each metric
- See [Advanced Usage](advanced.md) for custom metrics and more

