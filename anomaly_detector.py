"""
Online Anomaly Detection Library - Configurable Version
Implements CUMSUM and EWMA algorithms with per-metric tuning
"""

import psutil
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class CUMSUM:
    """CUMSUM (Cumulative Sum) algorithm for detecting sustained shifts"""
    
    def __init__(self, threshold: float = 5.0, drift: float = 0.5):
        """
        Args:
            threshold: Detection sensitivity (lower = more sensitive)
            drift: Minimum change to detect (helps ignore noise)
        """
        self.threshold = threshold
        self.drift = drift
        self.cumsum_pos = 0
        self.cumsum_neg = 0
        self.reference_mean = None
        
    def set_reference(self, mean: float):
        """Set the reference mean for normal behavior"""
        self.reference_mean = mean
        
    def update(self, value: float) -> Tuple[bool, float]:
        """
        Update with new value and check for anomaly
        
        Returns:
            (is_anomaly, cumsum_value)
        """
        if self.reference_mean is None:
            self.reference_mean = value
            return False, 0
            
        deviation = value - self.reference_mean - self.drift
        
        self.cumsum_pos = max(0, self.cumsum_pos + deviation)
        self.cumsum_neg = max(0, self.cumsum_neg - deviation)
        
        max_cumsum = max(self.cumsum_pos, self.cumsum_neg)
        
        if max_cumsum > self.threshold:
            # Reset after detection
            self.cumsum_pos = 0
            self.cumsum_neg = 0
            return True, max_cumsum
            
        return False, max_cumsum
    
    def reset(self):
        """Reset the detector"""
        self.cumsum_pos = 0
        self.cumsum_neg = 0


class EWMA:
    """EWMA (Exponentially Weighted Moving Average) for adaptive detection"""
    
    def __init__(self, alpha: float = 0.3, threshold_sigma: float = 3.0):
        """
        Args:
            alpha: Smoothing factor (0-1). Higher = more reactive to recent changes
            threshold_sigma: Number of standard deviations for anomaly threshold
        """
        self.alpha = alpha
        self.threshold_sigma = threshold_sigma
        self.ewma = None
        self.ewmvar = None
        
    def update(self, value: float) -> Tuple[bool, float]:
        """
        Update with new value and check for anomaly
        
        Returns:
            (is_anomaly, deviation_score)
        """
        if self.ewma is None:
            self.ewma = value
            self.ewmvar = 0
            return False, 0
            
        # Update EWMA
        prev_ewma = self.ewma
        self.ewma = self.alpha * value + (1 - self.alpha) * self.ewma
        
        # Update variance estimate
        diff = value - prev_ewma
        self.ewmvar = self.alpha * (diff ** 2) + (1 - self.alpha) * self.ewmvar
        
        # Calculate standard deviation
        std = max(self.ewmvar ** 0.5, 0.01)  # Avoid division by zero
        
        # Calculate deviation score
        deviation_score = abs(value - self.ewma) / std
        
        # Check if anomaly
        is_anomaly = deviation_score > self.threshold_sigma
        
        return is_anomaly, deviation_score
    
    def reset(self):
        """Reset the detector"""
        self.ewma = None
        self.ewmvar = None


class ServerMetrics:
    """Collect server metrics using psutil"""
    
    @staticmethod
    def get_all_metrics() -> Dict[str, float]:
        """Get all server metrics at once"""
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_mb = disk_io.read_bytes / (1024 * 1024)
        disk_write_mb = disk_io.write_bytes / (1024 * 1024)
        
        # Network metrics
        net_io = psutil.net_io_counters()
        net_sent_mb = net_io.bytes_sent / (1024 * 1024)
        net_recv_mb = net_io.bytes_recv / (1024 * 1024)
        
        # System load (1 minute average)
        try:
            load_avg = psutil.getloadavg()[0]  # 1-minute load average
        except (AttributeError, OSError):
            # Windows doesn't support getloadavg
            load_avg = cpu_percent / 100.0 * psutil.cpu_count()
        
        # Connection errors (approximation using connection count)
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, OSError):
            connections = 0
        
        return {
            'cpu_percent': cpu_percent,
            'ram_percent': ram_percent,
            'disk_read_mb': disk_read_mb,
            'disk_write_mb': disk_write_mb,
            'net_sent_mb': net_sent_mb,
            'net_recv_mb': net_recv_mb,
            'load_avg': load_avg,
            'connections': connections,
            'timestamp': datetime.now().isoformat()
        }


class MetricConfig:
    """Configuration for a single metric"""
    
    def __init__(
        self,
        algorithm: str = 'CUMSUM',  # 'CUMSUM' or 'EWMA'
        # CUMSUM parameters
        threshold: float = 5.0,
        drift: float = 0.5,
        reference_mean: Optional[float] = None,
        # EWMA parameters
        alpha: float = 0.3,
        threshold_sigma: float = 3.0,
        # Common parameters
        enabled: bool = True,
        description: str = ""
    ):
        self.algorithm = algorithm
        self.threshold = threshold
        self.drift = drift
        self.reference_mean = reference_mean
        self.alpha = alpha
        self.threshold_sigma = threshold_sigma
        self.enabled = enabled
        self.description = description


class AnomalyMonitor:
    """Main monitoring class with configurable per-metric settings"""
    
    # Default configurations for each metric
    DEFAULT_CONFIGS = {
        'cpu_percent': MetricConfig(
            algorithm='CUMSUM',
            threshold=25.0,
            drift=5.0,
            reference_mean=30.0,
            description='CPU usage - sustained changes only'
        ),
        'ram_percent': MetricConfig(
            algorithm='CUMSUM',
            threshold=10.0,  # MORE SENSITIVE - Lower threshold
            drift=2.0,       # MORE SENSITIVE - Smaller drift
            reference_mean=50.0,
            description='RAM usage - more sensitive to fluctuations'
        ),
        'load_avg': MetricConfig(
            algorithm='CUMSUM',
            threshold=15.0,
            drift=1.0,
            reference_mean=2.0,
            description='System load average'
        ),
        'net_sent_mb': MetricConfig(
            algorithm='EWMA',
            alpha=0.1,           # Smooth - less reactive
            threshold_sigma=5.0,  # Less sensitive
            description='Network bytes sent'
        ),
        'net_recv_mb': MetricConfig(
            algorithm='EWMA',
            alpha=0.1,
            threshold_sigma=5.0,
            description='Network bytes received'
        ),
        'disk_read_mb': MetricConfig(
            algorithm='EWMA',
            alpha=0.15,
            threshold_sigma=4.5,
            description='Disk read throughput'
        ),
        'disk_write_mb': MetricConfig(
            algorithm='EWMA',
            alpha=0.15,
            threshold_sigma=4.5,
            description='Disk write throughput'
        ),
        'connections': MetricConfig(
            algorithm='EWMA',
            alpha=0.15,
            threshold_sigma=5.0,
            description='Number of network connections'
        ),
    }
    
    def __init__(self, min_anomaly_duration=3, custom_configs: Optional[Dict[str, MetricConfig]] = None):
        """
        Args:
            min_anomaly_duration: Minimum number of consecutive anomalies before alerting
            custom_configs: Dictionary of custom MetricConfig objects to override defaults
        """
        # Merge custom configs with defaults
        self.configs = self.DEFAULT_CONFIGS.copy()
        if custom_configs:
            self.configs.update(custom_configs)
        
        # Initialize detectors based on configs
        self.detectors = {}
        self.ewma_detectors = {}
        
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
        
        self.anomaly_history: List[Dict] = []
        
        # Sustained anomaly tracking
        self.min_anomaly_duration = min_anomaly_duration
        self.anomaly_counters = {}
    
    def update_metric_config(self, metric_name: str, config: MetricConfig):
        """
        Update configuration for a specific metric at runtime
        
        Args:
            metric_name: Name of the metric to update
            config: New MetricConfig object
        """
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
    
    def get_config(self, metric_name: str) -> Optional[MetricConfig]:
        """Get configuration for a specific metric"""
        return self.configs.get(metric_name)
    
    def get_all_configs(self) -> Dict[str, MetricConfig]:
        """Get all metric configurations"""
        return self.configs.copy()
        
    def check_metrics(self, metrics: Dict[str, float]) -> Dict:
        """
        Check all metrics for anomalies
        
        Returns:
            Dictionary with anomaly detection results
        """
        detected_anomalies = []
        scores = {}
        
        # Check CUMSUM detectors
        for metric_name, detector in self.detectors.items():
            if metric_name in metrics:
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
        
        # Check EWMA detectors
        for metric_name, detector in self.ewma_detectors.items():
            if metric_name in metrics:
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
        
        # Filter for SUSTAINED anomalies only
        sustained_anomalies = []
        
        for anomaly in detected_anomalies:
            metric_name = anomaly['metric']
            
            # Increment counter for this metric
            if metric_name not in self.anomaly_counters:
                self.anomaly_counters[metric_name] = 0
            self.anomaly_counters[metric_name] += 1
            
            # Only report if sustained for min_anomaly_duration checks
            if self.anomaly_counters[metric_name] >= self.min_anomaly_duration:
                anomaly['severity'] = 'high' if self.anomaly_counters[metric_name] > self.min_anomaly_duration * 2 else 'medium'
                anomaly['duration'] = self.anomaly_counters[metric_name]
                sustained_anomalies.append(anomaly)
        
        # Reset counters for metrics that are now normal
        all_anomaly_metrics = {a['metric'] for a in detected_anomalies}
        for metric_name in list(self.anomaly_counters.keys()):
            if metric_name not in all_anomaly_metrics:
                self.anomaly_counters[metric_name] = 0
        
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
        
        return result
    
    def get_anomaly_history(self) -> List[Dict]:
        """Get history of detected anomalies"""
        return self.anomaly_history
    
    def reset_all(self):
        """Reset all detectors"""
        for detector in self.detectors.values():
            detector.reset()
        for detector in self.ewma_detectors.values():
            detector.reset()
        self.anomaly_history.clear()
        self.anomaly_counters.clear()


# Example usage with custom configurations
if __name__ == "__main__":
    # Example 1: Use default configs
    monitor = AnomalyMonitor()
    
    # Example 2: Customize specific metrics
    custom_configs = {
        'ram_percent': MetricConfig(
            algorithm='CUMSUM',
            threshold=5.0,      # Very sensitive
            drift=1.0,          # Catch small changes
            reference_mean=60.0,
            description='RAM - very sensitive to memory leaks'
        ),
        'cpu_percent': MetricConfig(
            algorithm='CUMSUM',
            threshold=30.0,     # Less sensitive
            drift=10.0,         # Only large sustained changes
            reference_mean=25.0,
            description='CPU - only major spikes'
        ),
    }
    
    monitor_custom = AnomalyMonitor(custom_configs=custom_configs)
    
    # Example 3: Update config at runtime
    monitor.update_metric_config(
        'net_sent_mb',
        MetricConfig(
            algorithm='EWMA',
            alpha=0.3,           # More reactive
            threshold_sigma=3.0,  # More sensitive
            description='Network - catch traffic spikes faster'
        )
    )
    
    print("Configurations loaded:")
    for metric, config in monitor.get_all_configs().items():
        if config.enabled:
            print(f"  {metric}: {config.algorithm} - {config.description}")