"""
Tests for anomaly detection algorithms
"""

import pytest
from drift.algorithms.cumsum import CUMSUM
from drift.algorithms.ewma import EWMA


class TestCUMSUM:
    """Tests for CUMSUM algorithm"""
    
    def test_initialization(self):
        """Test CUMSUM initialization"""
        detector = CUMSUM(threshold=5.0, drift=0.5)
        assert detector.threshold == 5.0
        assert detector.drift == 0.5
        assert detector.reference_mean is None
    
    def test_set_reference(self):
        """Test setting reference mean"""
        detector = CUMSUM()
        detector.set_reference(30.0)
        assert detector.reference_mean == 30.0
    
    def test_first_value_sets_reference(self):
        """Test that first value becomes reference"""
        detector = CUMSUM()
        is_anomaly, score = detector.update(25.0)
        assert not is_anomaly
        assert detector.reference_mean == 25.0
    
    def test_normal_behavior_no_anomaly(self):
        """Test that normal values don't trigger anomalies"""
        detector = CUMSUM(threshold=10.0, drift=2.0)
        detector.set_reference(30.0)
        
        # Values close to reference shouldn't trigger
        for value in [29.0, 30.0, 31.0, 32.0]:
            is_anomaly, score = detector.update(value)
            assert not is_anomaly
    
    def test_sustained_shift_detects_anomaly(self):
        """Test that sustained shift is detected"""
        detector = CUMSUM(threshold=10.0, drift=2.0)
        detector.set_reference(30.0)
        
        # Small deviations shouldn't trigger immediately
        for _ in range(5):
            is_anomaly, _ = detector.update(35.0)
            if is_anomaly:
                break
        
        # After sustained deviation, should detect
        is_anomaly, score = detector.update(35.0)
        assert is_anomaly
        assert score > detector.threshold
    
    def test_reset(self):
        """Test reset functionality"""
        detector = CUMSUM()
        detector.set_reference(30.0)
        detector.update(35.0)
        
        detector.reset()
        assert detector.cumsum_pos == 0.0
        assert detector.cumsum_neg == 0.0
        assert detector.reference_mean is None


class TestEWMA:
    """Tests for EWMA algorithm"""
    
    def test_initialization(self):
        """Test EWMA initialization"""
        detector = EWMA(alpha=0.3, threshold_sigma=3.0)
        assert detector.alpha == 0.3
        assert detector.threshold_sigma == 3.0
        assert detector.ewma is None
    
    def test_first_value_initializes(self):
        """Test that first value initializes EWMA"""
        detector = EWMA()
        is_anomaly, score = detector.update(25.0)
        assert not is_anomaly
        assert detector.ewma == 25.0
    
    def test_normal_behavior_no_anomaly(self):
        """Test that normal values don't trigger anomalies"""
        detector = EWMA(alpha=0.3, threshold_sigma=3.0)
        
        # Values around the mean shouldn't trigger
        values = [25.0, 26.0, 24.0, 25.5, 24.5]
        for value in values:
            is_anomaly, score = detector.update(value)
            # Early values might have high scores due to low variance
            if detector.ewmvar and detector.ewmvar > 0.01:
                assert not is_anomaly or score < detector.threshold_sigma
    
    def test_large_deviation_detects_anomaly(self):
        """Test that large deviation is detected"""
        detector = EWMA(alpha=0.3, threshold_sigma=3.0)
        
        # Establish baseline
        for _ in range(10):
            detector.update(25.0)
        
        # Large deviation should trigger
        is_anomaly, score = detector.update(100.0)
        assert is_anomaly
        assert score > detector.threshold_sigma
    
    def test_adaptive_behavior(self):
        """Test that EWMA adapts to changing patterns"""
        detector = EWMA(alpha=0.5, threshold_sigma=3.0)
        
        # Establish baseline at 25
        for _ in range(5):
            detector.update(25.0)
        
        baseline_ewma = detector.ewma
        
        # Shift to new level
        for _ in range(10):
            detector.update(50.0)
        
        # EWMA should have adapted
        assert detector.ewma > baseline_ewma
    
    def test_reset(self):
        """Test reset functionality"""
        detector = EWMA()
        detector.update(25.0)
        detector.update(30.0)
        
        detector.reset()
        assert detector.ewma is None
        assert detector.ewmvar is None

