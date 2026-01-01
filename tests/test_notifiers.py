"""
Tests for notification handlers
"""

import pytest
from unittest.mock import Mock, patch
from drift.notifiers.discord import DiscordNotifier


class TestDiscordNotifier:
    """Tests for DiscordNotifier"""
    
    def test_initialization(self):
        """Test DiscordNotifier initialization"""
        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/test",
            rate_limit_per_hour=10
        )
        assert notifier.webhook_url == "https://discord.com/api/webhooks/test"
        assert notifier.rate_limit_per_hour == 10
    
    @patch('drift.notifiers.discord.requests.post')
    def test_send_anomaly_alert(self, mock_post):
        """Test sending anomaly alert"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        notifier = DiscordNotifier(webhook_url="https://test.com")
        
        anomaly = {
            'metric': 'cpu_percent',
            'value': 95.0,
            'severity': 'high',
            'duration': 5,
            'algorithm': 'CUMSUM',
            'score': 15.0,
            'timestamp': '2025-01-01T12:00:00'
        }
        
        result = notifier.send_anomaly_alert(anomaly)
        
        assert result is True
        assert mock_post.called
        call_args = mock_post.call_args
        assert 'embeds' in call_args[1]['json']
    
    @patch('drift.notifiers.discord.requests.post')
    def test_rate_limiting(self, mock_post):
        """Test rate limiting"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        notifier = DiscordNotifier(
            webhook_url="https://test.com",
            rate_limit_per_hour=2
        )
        
        anomaly = {
            'metric': 'cpu_percent',
            'value': 95.0,
            'severity': 'medium',
            'duration': 3,
            'algorithm': 'CUMSUM',
            'score': 12.0,
            'timestamp': '2025-01-01T12:00:00'
        }
        
        # Send 2 alerts (should work)
        assert notifier.send_anomaly_alert(anomaly) is True
        assert notifier.send_anomaly_alert(anomaly) is True
        
        # Third should be rate limited
        assert notifier.send_anomaly_alert(anomaly) is False
    
    @patch('drift.notifiers.discord.requests.post')
    def test_recovery_notification(self, mock_post):
        """Test recovery notification"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        notifier = DiscordNotifier(
            webhook_url="https://test.com",
            enable_recovery=True
        )
        
        # Set metric to anomaly state
        notifier.alert_states['cpu_percent'] = True
        
        # Send recovery notification
        result = notifier.send_recovery_notification('cpu_percent', 95.0)
        
        assert result is True
        assert mock_post.called
        call_args = mock_post.call_args
        assert 'embeds' in call_args[1]['json']
        embed = call_args[1]['json']['embeds'][0]
        assert 'Metric Recovered' in embed['title']
    
    def test_update_metric_state(self):
        """Test updating metric state"""
        notifier = DiscordNotifier(webhook_url="https://test.com")
        
        # Update to anomaly
        notifier.update_metric_state('cpu_percent', True)
        assert notifier.alert_states['cpu_percent'] is True
        
        # Update to normal
        notifier.update_metric_state('cpu_percent', False)
        assert notifier.alert_states['cpu_percent'] is False

