"""
Test Flask app to verify drift-sre works
"""

from flask import Flask, jsonify
from drift import DriftMonitor
import os
import time

app = Flask(__name__)

# Initialize monitor (without Discord webhook for testing)
monitor = DriftMonitor(
    discord_webhook=None,  # Set to your webhook URL for real notifications
    check_interval=5,
    min_anomaly_duration=3,
    auto_start=True
)

# Customize a metric
monitor.configure_metric('ram_percent', threshold=10.0, drift=2.0)

@app.route('/')
def hello():
    return "Drift-SRE Test Server - Monitoring Active"

@app.route('/metrics')
def get_metrics():
    """Get current metrics"""
    metrics = monitor.get_current_metrics()
    return jsonify(metrics)

@app.route('/anomalies')
def get_anomalies():
    """Get anomaly history"""
    history = monitor.get_anomaly_history()
    return jsonify({
        'count': len(history),
        'recent': history[-5:] if history else []
    })

@app.route('/config')
def get_config():
    """Get configuration"""
    return jsonify(monitor.get_configuration())

if __name__ == '__main__':
    print("Starting Flask app with Drift-SRE monitoring...")
    print("Visit http://localhost:5000/metrics to see current metrics")
    app.run(debug=True, port=5000)

