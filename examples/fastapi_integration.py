"""
FastAPI integration example for Drift-SRE

Shows how to integrate Drift-SRE into a FastAPI application.
"""

from fastapi import FastAPI
from drift import DriftMonitor
import os

app = FastAPI()

# Initialize monitor
monitor = DriftMonitor(
    discord_webhook=os.getenv('DISCORD_WEBHOOK_URL'),
    check_interval=5,
    min_anomaly_duration=3
)

# Customize metrics
monitor.configure_metric('ram_percent', threshold=10.0, drift=2.0)

@app.on_event("startup")
async def startup_event():
    """Start monitoring when FastAPI starts"""
    monitor.start()
    print("Drift-SRE monitoring started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop monitoring when FastAPI shuts down"""
    monitor.stop()
    print("Drift-SRE monitoring stopped")

@app.get("/")
def read_root():
    return {"message": "Hello, World! Monitoring is active."}

@app.get("/metrics")
def get_metrics():
    """Get current system metrics"""
    metrics = monitor.get_current_metrics()
    return {
        'cpu_percent': metrics.get('cpu_percent'),
        'ram_percent': metrics.get('ram_percent'),
        'timestamp': metrics.get('timestamp')
    }

@app.get("/anomalies")
def get_anomalies():
    """Get anomaly detection history"""
    history = monitor.get_anomaly_history()
    return {
        'count': len(history),
        'recent': history[-5:] if history else []
    }

@app.get("/config")
def get_config():
    """Get current configuration"""
    return monitor.get_configuration()

