"""
EWMA (Exponentially Weighted Moving Average) for adaptive detection
"""

from typing import Tuple, Optional


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
        self.ewma: Optional[float] = None
        self.ewmvar: Optional[float] = None
        
    def update(self, value: float) -> Tuple[bool, float]:
        """
        Update with new value and check for anomaly
        
        Returns:
            (is_anomaly, deviation_score)
        """
        if self.ewma is None:
            self.ewma = value
            self.ewmvar = 0.0
            return False, 0.0
            
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
    
    def reset(self) -> None:
        """Reset the detector"""
        self.ewma = None
        self.ewmvar = None

