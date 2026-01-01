"""
Tests for DriftMonitor
"""

import pytest
import time
from unittest.mock import Mock, patch
from drift import DriftMonitor, MetricConfig
from drift.collectors.system import SystemMetricsCollector


class TestDriftMonitor:
    """Tests for DriftMonitor"""
    
    def test_initialization(self):
        """Test DriftMonitor initialization"""
        monitor = DriftMonitor(
            discord_webhook=None,
            check_interval=5,
            min_anomaly_duration=3
        )
        
        assert monitor.check_interval == 5
        assert monitor.min_anomaly_duration == 3
        assert not monitor.monitoring_active
    
    def test_configure_metric(self):
        """Test configuring a metric"""
        monitor = DriftMonitor()
        
        monitor.configure_metric(
            'cpu_percent',
            threshold=30.0,
            drift=5.0
        )
        
        config = monitor.get_config('cpu_percent')
        assert config is not None
        assert config.threshold == 30.0
        assert config.drift == 5.0
    
    def test_register_custom_metric(self):
        """Test registering custom metric"""
        monitor = DriftMonitor()
        
        def collector():
            return 42.0
        
        monitor.register_custom_metric(
            'custom_metric',
            collector,
            MetricConfig(algorithm='EWMA', threshold_sigma=3.0)
        )
        
        config = monitor.get_config('custom_metric')
        assert config is not None
        assert 'custom_metric' in monitor.custom_collectors
    
    def test_check_metrics(self):
        """Test checking metrics"""
        monitor = DriftMonitor()
        
        # Use test metrics
        test_metrics = {
            'cpu_percent': 30.0,
            'ram_percent': 50.0,
            'timestamp': '2025-01-01T12:00:00'
        }
        
        result = monitor.check_metrics(test_metrics)
        
        assert 'timestamp' in result
        assert 'has_anomalies' in result
        assert 'anomaly_count' in result
        assert 'anomalies' in result
        assert 'metrics' in result
        assert 'scores' in result
    
    def test_start_stop(self):
        """Test starting and stopping monitor"""
        monitor = DriftMonitor(check_interval=1)
        
        assert not monitor.monitoring_active
        
        monitor.start()
        assert monitor.monitoring_active
        
        time.sleep(0.1)  # Give thread time to start
        
        monitor.stop()
        time.sleep(0.1)  # Give thread time to stop
        
        assert not monitor.monitoring_active
    
    def test_reset(self):
        """Test resetting detectors"""
        monitor = DriftMonitor()
        
        # Add some history
        test_metrics = {'cpu_percent': 30.0, 'ram_percent': 50.0, 'timestamp': '2025-01-01T12:00:00'}
        monitor.check_metrics(test_metrics)
        
        monitor.reset()
        
        assert len(monitor.anomaly_history) == 0
        assert len(monitor.anomaly_counters) == 0
    
    def test_get_current_metrics(self):
        """Test getting current metrics"""
        monitor = DriftMonitor()
        
        # Start monitoring to populate metrics
        monitor.start()
        time.sleep(0.2)  # Give it time to collect
        
        metrics = monitor.get_current_metrics()
        
        # Should have metrics after collection
        if metrics:
            assert isinstance(metrics, dict)
        
        monitor.stop()
    
    def test_get_anomaly_history(self):
        """Test getting anomaly history"""
        monitor = DriftMonitor()
        
        history = monitor.get_anomaly_history()
        
        assert isinstance(history, list)
    
    def test_get_configuration(self):
        """Test getting configuration"""
        monitor = DriftMonitor()
        
        config = monitor.get_configuration()
        
        assert isinstance(config, dict)
        assert 'cpu_percent' in config
        assert 'ram_percent' in config

