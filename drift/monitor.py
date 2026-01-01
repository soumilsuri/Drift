"""
Main DriftMonitor class for real-time anomaly detection
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

from drift.algorithms.cumsum import CUMSUM
from drift.algorithms.ewma import EWMA
from drift.collectors.system import SystemMetricsCollector
from drift.config import MetricConfig, DEFAULT_CONFIGS
from drift.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class DriftMonitor:
    """Main monitoring class with configurable per-metric settings and Discord notifications"""
    
    def __init__(
        self,
        discord_webhook: Optional[str] = None,
        check_interval: int = 5,
        min_anomaly_duration: int = 3,
        auto_start: bool = False,
        enable_recovery_notifications: bool = True,
        custom_configs: Optional[Dict[str, MetricConfig]] = None
    ):
        """
        Initialize DriftMonitor
        
        Args:
            discord_webhook: Discord webhook URL for notifications (optional)
            check_interval: Seconds between metric checks
            min_anomaly_duration: Minimum consecutive anomalies before alerting
            auto_start: Start monitoring immediately
            enable_recovery_notifications: Send notifications when metrics recover
            custom_configs: Dictionary of custom MetricConfig objects to override defaults
        """
        self.check_interval = check_interval
        self.min_anomaly_duration = min_anomaly_duration
        
        # Initialize Discord notifier if webhook provided
        self.notifier = None
        if discord_webhook:
            from drift.notifiers.discord import DiscordNotifier
            self.notifier = DiscordNotifier(
                webhook_url=discord_webhook,
                enable_recovery=enable_recovery_notifications
            )
        
        # Merge custom configs with defaults
        self.configs = DEFAULT_CONFIGS.copy()
        if custom_configs:
            self.configs.update(custom_configs)
        
        # Initialize detectors based on configs
        self.detectors: Dict[str, CUMSUM] = {}
        self.ewma_detectors: Dict[str, EWMA] = {}
        
        # Custom metric collectors
        self.custom_collectors: Dict[str, Callable[[], float]] = {}
        
        # System metrics collector
        self.system_collector = SystemMetricsCollector()
        
        # Initialize detectors
        self._initialize_detectors()
        
        # Anomaly tracking
        self.anomaly_history: List[Dict] = []
        self.anomaly_counters: Dict[str, int] = {}
        self.last_metric_values: Dict[str, float] = {}
        
        # Background monitoring
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        
        # Latest metrics and results (thread-safe access)
        self.latest_metrics: Dict[str, Any] = {}
        self.latest_result: Dict[str, Any] = {}
        
        if auto_start:
            self.start()
    
    def _initialize_detectors(self) -> None:
        """Initialize detectors based on configurations"""
        for metric_name, config in self.configs.items():
            if not config.enabled:
                continue
                
            if config.algorithm == 'CUMSUM':
                detector = CUMSUM(threshold=config.threshold, drift=config.drift)
                if config.reference_mean is not None:
                    detector.set_reference(config.reference_mean)
                self.detectors[metric_name] = detector
                
            elif config.algorithm == 'EWMA':
                detector = EWMA(alpha=config.alpha, threshold_sigma=config.threshold_sigma)
                self.ewma_detectors[metric_name] = detector
    
    def configure_metric(
        self,
        metric_name: str,
        algorithm: str = 'CUMSUM',
        threshold: Optional[float] = None,
        drift: Optional[float] = None,
        reference_mean: Optional[float] = None,
        alpha: Optional[float] = None,
        threshold_sigma: Optional[float] = None,
        enabled: bool = True
    ) -> None:
        """
        Configure a specific metric
        
        Args:
            metric_name: Name of the metric to configure
            algorithm: 'CUMSUM' or 'EWMA'
            threshold: CUMSUM threshold (lower = more sensitive)
            drift: CUMSUM drift parameter
            reference_mean: CUMSUM reference mean
            alpha: EWMA smoothing factor (0-1)
            threshold_sigma: EWMA threshold in standard deviations
            enabled: Whether to enable this metric
        """
        with self.lock:
            # Get existing config or create new one
            existing_config = self.configs.get(metric_name)
            if existing_config:
                config = MetricConfig(
                    algorithm=algorithm,
                    threshold=threshold if threshold is not None else existing_config.threshold,
                    drift=drift if drift is not None else existing_config.drift,
                    reference_mean=reference_mean if reference_mean is not None else existing_config.reference_mean,
                    alpha=alpha if alpha is not None else existing_config.alpha,
                    threshold_sigma=threshold_sigma if threshold_sigma is not None else existing_config.threshold_sigma,
                    enabled=enabled,
                    description=existing_config.description
                )
            else:
                config = MetricConfig(
                    algorithm=algorithm,
                    threshold=threshold or 5.0,
                    drift=drift or 0.5,
                    reference_mean=reference_mean,
                    alpha=alpha or 0.3,
                    threshold_sigma=threshold_sigma or 3.0,
                    enabled=enabled,
                    description=f"Custom metric: {metric_name}"
                )
            
            self.update_metric_config(metric_name, config)
    
    def update_metric_config(self, metric_name: str, config: MetricConfig) -> None:
        """
        Update configuration for a specific metric at runtime
        
        Args:
            metric_name: Name of the metric to update
            config: New MetricConfig object
        """
        with self.lock:
            self.configs[metric_name] = config
            
            # Remove old detector
            if metric_name in self.detectors:
                del self.detectors[metric_name]
            if metric_name in self.ewma_detectors:
                del self.ewma_detectors[metric_name]
            
            # Create new detector if enabled
            if config.enabled:
                if config.algorithm == 'CUMSUM':
                    detector = CUMSUM(threshold=config.threshold, drift=config.drift)
                    if config.reference_mean is not None:
                        detector.set_reference(config.reference_mean)
                    self.detectors[metric_name] = detector
                    
                elif config.algorithm == 'EWMA':
                    detector = EWMA(alpha=config.alpha, threshold_sigma=config.threshold_sigma)
                    self.ewma_detectors[metric_name] = detector
    
    def register_custom_metric(
        self,
        name: str,
        collector: Callable[[], float],
        config: MetricConfig
    ) -> None:
        """
        Register a custom metric with a collector function
        
        Args:
            name: Name of the custom metric
            collector: Callable that returns a float value
            config: MetricConfig for this custom metric
        """
        with self.lock:
            self.custom_collectors[name] = collector
            self.update_metric_config(name, config)
    
    def get_config(self, metric_name: str) -> Optional[MetricConfig]:
        """Get configuration for a specific metric"""
        with self.lock:
            return self.configs.get(metric_name)
    
    def get_configuration(self) -> Dict[str, Dict[str, Any]]:
        """Get all metric configurations as dictionary"""
        with self.lock:
            config_dict = {}
            for metric_name, config in self.configs.items():
                config_dict[metric_name] = {
                    'algorithm': config.algorithm,
                    'threshold': config.threshold,
                    'drift': config.drift,
                    'reference_mean': config.reference_mean,
                    'alpha': config.alpha,
                    'threshold_sigma': config.threshold_sigma,
                    'enabled': config.enabled,
                    'description': config.description
                }
            return config_dict
    
    def _collect_all_metrics(self) -> Dict[str, float]:
        """Collect all metrics (system + custom)"""
        metrics = self.system_collector.collect()
        
        # Add custom metrics
        for name, collector in self.custom_collectors.items():
            try:
                metrics[name] = collector()
            except Exception as e:
                logger.warning(f"Failed to collect custom metric {name}: {e}")
        
        return metrics
    
    def check_metrics(self, metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Check all metrics for anomalies
        
        Args:
            metrics: Optional metrics dict. If None, collects fresh metrics.
        
        Returns:
            Dictionary with anomaly detection results
        """
        if metrics is None:
            metrics = self._collect_all_metrics()
        
        with self.lock:
            detected_anomalies = []
            scores = {}
            
            # Check CUMSUM detectors
            for metric_name, detector in self.detectors.items():
                if metric_name in metrics and metric_name != 'timestamp':
                    try:
                        is_anomaly, score = detector.update(metrics[metric_name])
                        scores[metric_name] = score
                        
                        if is_anomaly:
                            config = self.configs[metric_name]
                            detected_anomalies.append({
                                'metric': metric_name,
                                'value': metrics[metric_name],
                                'score': score,
                                'algorithm': 'CUMSUM',
                                'config': {
                                    'threshold': config.threshold,
                                    'drift': config.drift
                                }
                            })
                    except Exception as e:
                        logger.error(f"Error checking metric {metric_name}: {e}")
            
            # Check EWMA detectors
            for metric_name, detector in self.ewma_detectors.items():
                if metric_name in metrics and metric_name != 'timestamp':
                    try:
                        is_anomaly, score = detector.update(metrics[metric_name])
                        scores[metric_name] = score
                        
                        if is_anomaly:
                            config = self.configs[metric_name]
                            detected_anomalies.append({
                                'metric': metric_name,
                                'value': metrics[metric_name],
                                'score': score,
                                'algorithm': 'EWMA',
                                'config': {
                                    'alpha': config.alpha,
                                    'threshold_sigma': config.threshold_sigma
                                }
                            })
                    except Exception as e:
                        logger.error(f"Error checking metric {metric_name}: {e}")
            
            # Filter for SUSTAINED anomalies only
            sustained_anomalies = []
            anomaly_metric_names = set()
            sustained_metric_names = set()
            
            for anomaly in detected_anomalies:
                metric_name = anomaly['metric']
                anomaly_metric_names.add(metric_name)
                
                # Increment counter for this metric
                if metric_name not in self.anomaly_counters:
                    self.anomaly_counters[metric_name] = 0
                self.anomaly_counters[metric_name] += 1
                
                # Only report if sustained for min_anomaly_duration checks
                if self.anomaly_counters[metric_name] >= self.min_anomaly_duration:
                    severity = 'high' if self.anomaly_counters[metric_name] > self.min_anomaly_duration * 2 else 'medium'
                    anomaly['severity'] = severity
                    anomaly['duration'] = self.anomaly_counters[metric_name]
                    anomaly['timestamp'] = metrics.get('timestamp', datetime.now().isoformat())
                    sustained_anomalies.append(anomaly)
                    sustained_metric_names.add(metric_name)
            
            # Track which metrics were in sustained anomaly state before this check
            previous_sustained = set()
            for metric_name, count in self.anomaly_counters.items():
                if count >= self.min_anomaly_duration:
                    previous_sustained.add(metric_name)
            
            # Reset counters for metrics that are now normal
            for metric_name in list(self.anomaly_counters.keys()):
                if metric_name not in anomaly_metric_names:
                    # Metric returned to normal - check if we need to send recovery notification
                    was_sustained = metric_name in previous_sustained
                    if was_sustained and self.notifier and metric_name in self.last_metric_values:
                        self.notifier.update_metric_state(metric_name, False)
                        self.notifier.send_recovery_notification(metric_name, self.last_metric_values[metric_name])
                    self.anomaly_counters[metric_name] = 0
            
            # Update metric states for notifier
            if self.notifier:
                for metric_name in sustained_metric_names:
                    self.notifier.update_metric_state(metric_name, True)
                    if metric_name in metrics:
                        self.last_metric_values[metric_name] = metrics[metric_name]
            
            result = {
                'timestamp': metrics.get('timestamp', datetime.now().isoformat()),
                'has_anomalies': len(sustained_anomalies) > 0,
                'anomaly_count': len(sustained_anomalies),
                'anomalies': sustained_anomalies,
                'metrics': metrics,
                'scores': scores
            }
            
            if sustained_anomalies:
                self.anomaly_history.append(result)
                # Keep only last 100 anomalies
                self.anomaly_history = self.anomaly_history[-100:]
                
                # Send Discord notifications
                if self.notifier:
                    for anomaly in sustained_anomalies:
                        try:
                            self.notifier.send_anomaly_alert(anomaly)
                        except Exception as e:
                            logger.error(f"Failed to send notification for {anomaly['metric']}: {e}")
            
            return result
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        logger.info("Monitoring started")
        
        while not self.stop_event.is_set():
            try:
                # Collect metrics
                metrics = self._collect_all_metrics()
                
                with self.lock:
                    self.latest_metrics = metrics
                
                # Check for anomalies
                result = self.check_metrics(metrics)
                
                with self.lock:
                    self.latest_result = result
                
                # Log anomalies
                if result['has_anomalies']:
                    logger.warning(
                        f"{result['anomaly_count']} anomalies detected at {result['timestamp']}"
                    )
                    for anomaly in result['anomalies']:
                        logger.warning(
                            f"  - {anomaly['metric']}: {anomaly['value']:.2f} "
                            f"(score: {anomaly['score']:.2f}, severity: {anomaly['severity']})"
                        )
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait for next check or stop event
            self.stop_event.wait(self.check_interval)
        
        logger.info("Monitoring stopped")
    
    def start(self) -> None:
        """Start background monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        with self.lock:
            self.monitoring_active = True
            self.stop_event.clear()
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop(self) -> None:
        """Stop background monitoring"""
        if not self.monitoring_active:
            return
        
        with self.lock:
            self.monitoring_active = False
            self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics (thread-safe)"""
        with self.lock:
            return self.latest_metrics.copy()
    
    def get_anomaly_history(self) -> List[Dict]:
        """Get history of detected anomalies"""
        with self.lock:
            return self.anomaly_history.copy()
    
    def reset(self) -> None:
        """Reset all detectors"""
        with self.lock:
            for detector in self.detectors.values():
                detector.reset()
            for detector in self.ewma_detectors.values():
                detector.reset()
            self.anomaly_history.clear()
            self.anomaly_counters.clear()
            self.last_metric_values.clear()
            if self.notifier:
                # Reset notifier state
                self.notifier.alert_states.clear()
                self.notifier.recovery_sent.clear()

