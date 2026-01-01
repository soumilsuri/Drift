"""
Configuration classes and default configurations
"""

from typing import Dict, Optional
from drift.algorithms.cumsum import CUMSUM
from drift.algorithms.ewma import EWMA


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


# Default configurations for each metric
DEFAULT_CONFIGS: Dict[str, MetricConfig] = {
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

