"""
CUMSUM (Cumulative Sum) algorithm for detecting sustained shifts
"""

from typing import Tuple, Optional


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
        self.cumsum_pos = 0.0
        self.cumsum_neg = 0.0
        self.reference_mean: Optional[float] = None
        
    def set_reference(self, mean: float) -> None:
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
            return False, 0.0
            
        deviation = value - self.reference_mean - self.drift
        
        self.cumsum_pos = max(0.0, self.cumsum_pos + deviation)
        self.cumsum_neg = max(0.0, self.cumsum_neg - deviation)
        
        max_cumsum = max(self.cumsum_pos, self.cumsum_neg)
        
        if max_cumsum > self.threshold:
            # Reset after detection
            self.cumsum_pos = 0.0
            self.cumsum_neg = 0.0
            return True, max_cumsum
            
        return False, max_cumsum
    
    def reset(self) -> None:
        """Reset the detector"""
        self.cumsum_pos = 0.0
        self.cumsum_neg = 0.0
        self.reference_mean = None

