"""
Tests for metric collectors
"""

import pytest
from drift.collectors.system import SystemMetricsCollector


class TestSystemMetricsCollector:
    """Tests for SystemMetricsCollector"""
    
    def test_collect_returns_dict(self):
        """Test that collect returns a dictionary"""
        collector = SystemMetricsCollector()
        metrics = collector.collect()
        
        assert isinstance(metrics, dict)
        assert len(metrics) > 0
    
    def test_collect_has_required_metrics(self):
        """Test that collect returns required metrics"""
        collector = SystemMetricsCollector()
        metrics = collector.collect()
        
        required_metrics = [
            'cpu_percent',
            'ram_percent',
            'disk_read_mb',
            'disk_write_mb',
            'net_sent_mb',
            'net_recv_mb',
            'load_avg',
            'connections',
            'timestamp'
        ]
        
        for metric in required_metrics:
            assert metric in metrics
    
    def test_metric_values_are_numeric(self):
        """Test that metric values are numeric (except timestamp)"""
        collector = SystemMetricsCollector()
        metrics = collector.collect()
        
        for key, value in metrics.items():
            if key != 'timestamp':
                assert isinstance(value, (int, float))
                # Percentages should be 0-100
                if 'percent' in key:
                    assert 0 <= value <= 100
                # Other metrics should be non-negative
                else:
                    assert value >= 0
    
    def test_timestamp_is_string(self):
        """Test that timestamp is a string"""
        collector = SystemMetricsCollector()
        metrics = collector.collect()
        
        assert isinstance(metrics['timestamp'], str)
        assert 'T' in metrics['timestamp'] or '-' in metrics['timestamp']  # ISO format
    
    def test_collect_is_static(self):
        """Test that collect can be called as static method"""
        metrics = SystemMetricsCollector.collect()
        assert isinstance(metrics, dict)

