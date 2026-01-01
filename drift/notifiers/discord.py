"""
Discord webhook notifier
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
from drift.exceptions import NotificationError

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Discord webhook notifier with rate limiting and debouncing"""
    
    def __init__(
        self,
        webhook_url: str,
        rate_limit_per_hour: int = 10,
        enable_recovery: bool = True
    ):
        """
        Args:
            webhook_url: Discord webhook URL
            rate_limit_per_hour: Maximum alerts per hour per metric
            enable_recovery: Enable recovery notifications
        """
        self.webhook_url = webhook_url
        self.rate_limit_per_hour = rate_limit_per_hour
        self.enable_recovery = enable_recovery
        
        # Rate limiting: track timestamps per metric
        self.alert_timestamps: Dict[str, List[float]] = defaultdict(list)
        
        # Debouncing: track alert state per metric
        self.alert_states: Dict[str, bool] = {}  # True = in anomaly, False = normal
        
        # Recovery tracking: track if we've sent recovery notification
        self.recovery_sent: Dict[str, bool] = {}
    
    def _is_rate_limited(self, metric_name: str) -> bool:
        """Check if metric is rate limited"""
        now = datetime.now().timestamp()
        hour_ago = now - 3600
        
        # Clean old entries
        self.alert_timestamps[metric_name] = [
            ts for ts in self.alert_timestamps[metric_name] if ts > hour_ago
        ]
        
        return len(self.alert_timestamps[metric_name]) >= self.rate_limit_per_hour
    
    def _record_alert(self, metric_name: str) -> None:
        """Record that an alert was sent"""
        now = datetime.now().timestamp()
        self.alert_timestamps[metric_name].append(now)
    
    def _send_webhook(self, embed: Dict) -> bool:
        """Send webhook to Discord"""
        try:
            payload = {"embeds": [embed]}
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            raise NotificationError(f"Discord webhook failed: {e}")
    
    def send_anomaly_alert(self, anomaly: Dict) -> bool:
        """
        Send anomaly alert to Discord
        
        Args:
            anomaly: Anomaly dictionary with metric, value, severity, etc.
        
        Returns:
            True if sent, False if rate limited
        """
        metric_name = anomaly['metric']
        
        # Check rate limiting
        if self._is_rate_limited(metric_name):
            logger.warning(f"Rate limited for metric {metric_name}")
            return False
        
        # Check if we've already sent an alert for this episode
        if self.alert_states.get(metric_name, False):
            # Already in anomaly state, don't send duplicate
            return False
        
        # Build embed
        severity = anomaly.get('severity', 'medium')
        color = 16776960 if severity == 'medium' else 16711680  # Yellow or Red
        
        embed = {
            "title": "🚨 Anomaly Detected",
            "color": color,
            "fields": [
                {"name": "Metric", "value": metric_name, "inline": True},
                {"name": "Value", "value": f"{anomaly['value']:.2f}", "inline": True},
                {"name": "Severity", "value": severity.capitalize(), "inline": True},
                {"name": "Duration", "value": f"{anomaly.get('duration', 1)} checks", "inline": True},
                {"name": "Algorithm", "value": anomaly.get('algorithm', 'Unknown'), "inline": True},
                {"name": "Score", "value": f"{anomaly.get('score', 0):.2f}", "inline": True}
            ],
            "timestamp": anomaly.get('timestamp', datetime.now().isoformat())
        }
        
        try:
            self._send_webhook(embed)
            self._record_alert(metric_name)
            self.alert_states[metric_name] = True
            self.recovery_sent[metric_name] = False
            return True
        except NotificationError:
            return False
    
    def send_recovery_notification(self, metric_name: str, previous_value: float) -> bool:
        """
        Send recovery notification when metric returns to normal
        
        Args:
            metric_name: Name of the metric that recovered
            previous_value: Last anomalous value
        
        Returns:
            True if sent, False if rate limited or not needed
        """
        if not self.enable_recovery:
            return False
        
        # Only send if we were in anomaly state
        if not self.alert_states.get(metric_name, False):
            return False
        
        # Only send once per recovery
        if self.recovery_sent.get(metric_name, False):
            return False
        
        # Check rate limiting
        if self._is_rate_limited(metric_name):
            return False
        
        embed = {
            "title": "✅ Metric Recovered",
            "color": 3066993,  # Green
            "fields": [
                {"name": "Metric", "value": metric_name, "inline": True},
                {"name": "Previous Value", "value": f"{previous_value:.2f}", "inline": True},
                {"name": "Status", "value": "Normal", "inline": True}
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self._send_webhook(embed)
            self._record_alert(metric_name)
            self.alert_states[metric_name] = False
            self.recovery_sent[metric_name] = True
            return True
        except NotificationError:
            return False
    
    def update_metric_state(self, metric_name: str, is_anomaly: bool) -> None:
        """
        Update the state of a metric (for tracking recovery)
        
        Args:
            metric_name: Name of the metric
            is_anomaly: Whether metric is currently anomalous
        """
        was_anomaly = self.alert_states.get(metric_name, False)
        
        if was_anomaly and not is_anomaly:
            # Metric recovered - reset recovery flag so we can send notification
            self.recovery_sent[metric_name] = False
        elif not was_anomaly and is_anomaly:
            # Metric became anomalous - reset recovery flag
            self.recovery_sent[metric_name] = False
        
        self.alert_states[metric_name] = is_anomaly

