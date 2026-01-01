"""
Flask integration example for Drift-SRE

Shows how to integrate Drift-SRE into a Flask application.
"""

from flask import Flask
from drift import DriftMonitor
import os
import atexit

app = Flask(__name__)

# Initialize monitor
monitor = DriftMonitor(
    discord_webhook=os.getenv('DISCORD_WEBHOOK_URL'),
    check_interval=5,
    min_anomaly_duration=3
)

# Customize metrics if needed
monitor.configure_metric('ram_percent', threshold=10.0, drift=2.0)
monitor.configure_metric('cpu_percent', threshold=25.0, drift=5.0)

# Start monitoring (only once)
_monitoring_started = False

@app.before_request
def ensure_monitoring_started():
    global _monitoring_started
    if not _monitoring_started and not monitor.monitoring_active:
        monitor.start()
        _monitoring_started = True
        print("Drift-SRE monitoring started")

# Stop monitoring on app shutdown
def shutdown_monitor():
    monitor.stop()
    print("Drift-SRE monitoring stopped")

atexit.register(shutdown_monitor)

@app.route('/')
def hello():
    return "Hello, World! Monitoring is active."

@app.route('/metrics')
def get_metrics():
    """Get current metrics"""
    metrics = monitor.get_current_metrics()
    return {
        'cpu_percent': metrics.get('cpu_percent'),
        'ram_percent': metrics.get('ram_percent'),
        'timestamp': metrics.get('timestamp')
    }

@app.route('/anomalies')
def get_anomalies():
    """Get anomaly history"""
    history = monitor.get_anomaly_history()
    return {
        'count': len(history),
        'recent': history[-5:] if history else []
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)

