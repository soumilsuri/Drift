"""
Drift-SRE: Real-time Anomaly Detection Library for SRE

A lightweight, embeddable library for monitoring server metrics and detecting
anomalies with Discord notifications.
"""

from drift.monitor import DriftMonitor
from drift.config import MetricConfig
from drift.exceptions import DriftError, ConfigurationError, NotificationError

__version__ = "0.1.0"
__all__ = [
    'DriftMonitor',
    'MetricConfig',
    'DriftError',
    'ConfigurationError',
    'NotificationError'
]

