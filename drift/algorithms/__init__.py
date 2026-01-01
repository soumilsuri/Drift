"""
Anomaly detection algorithms
"""

from drift.algorithms.cumsum import CUMSUM
from drift.algorithms.ewma import EWMA

__all__ = ['CUMSUM', 'EWMA']

