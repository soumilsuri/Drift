"""
Online Anomaly Detection Library
Implements CUMSUM and EWMA algorithms for real-time server monitoring
"""

import psutil
import time
from datetime import datetime
from typing import Dict, List, Tuple


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


class AnomalyMonitor:
    """Main monitoring class combining multiple detectors"""
    
    def __init__(self, min_anomaly_duration=3):
        """
        Args:
            min_anomaly_duration: Minimum number of consecutive anomalies before alerting
        """
        # CUMSUM detectors for stable metrics (LESS SENSITIVE)
        self.detectors = {
            'cpu_percent': CUMSUM(threshold=25.0, drift=5.0),  # Increased - only sustained 5%+ changes
            'ram_percent': CUMSUM(threshold=20.0, drift=3.0),  # Increased - slower RAM leaks only
            'load_avg': CUMSUM(threshold=15.0, drift=1.0),     # Increased - real overload only
        }
        
        # EWMA detectors for variable metrics (LESS SENSITIVE)
        self.ewma_detectors = {
            'net_sent_mb': EWMA(alpha=0.1, threshold_sigma=5.0),    # Lower alpha = smoother, higher sigma = less alerts
            'net_recv_mb': EWMA(alpha=0.1, threshold_sigma=5.0),    # Same as above
            'disk_read_mb': EWMA(alpha=0.15, threshold_sigma=4.5),  # Reduced sensitivity
            'disk_write_mb': EWMA(alpha=0.15, threshold_sigma=4.5), # Reduced sensitivity
            'connections': EWMA(alpha=0.15, threshold_sigma=5.0),   # Higher threshold
        }
        
        # Set reasonable defaults for CUMSUM reference means (YOUR SERVER'S BASELINE)
        # TODO: Adjust these to YOUR server's normal values!
        self.detectors['cpu_percent'].set_reference(30.0)  # Change to your avg CPU%
        self.detectors['ram_percent'].set_reference(50.0)  # Change to your avg RAM%
        self.detectors['load_avg'].set_reference(2.0)      # Change to your avg load
        
        self.anomaly_history: List[Dict] = []
        
        # Sustained anomaly tracking
        self.min_anomaly_duration = min_anomaly_duration
        self.anomaly_counters = {}  # Track consecutive anomalies per metric
        
    def check_metrics(self, metrics: Dict[str, float]) -> Dict:
        """
        Check all metrics for anomalies
        
        Returns:
            Dictionary with anomaly detection results
        """
        detected_anomalies = []  # Temporary storage for this check
        scores = {}
        
        # Check CUMSUM detectors
        for metric_name, detector in self.detectors.items():
            if metric_name in metrics:
                is_anomaly, score = detector.update(metrics[metric_name])
                scores[metric_name] = score
                
                if is_anomaly:
                    detected_anomalies.append({
                        'metric': metric_name,
                        'value': metrics[metric_name],
                        'score': score,
                        'algorithm': 'CUMSUM'
                    })
        
        # Check EWMA detectors
        for metric_name, detector in self.ewma_detectors.items():
            if metric_name in metrics:
                is_anomaly, score = detector.update(metrics[metric_name])
                scores[metric_name] = score
                
                if is_anomaly:
                    detected_anomalies.append({
                        'metric': metric_name,
                        'value': metrics[metric_name],
                        'score': score,
                        'algorithm': 'EWMA'
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