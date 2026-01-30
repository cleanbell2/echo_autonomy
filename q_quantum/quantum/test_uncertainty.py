"""Tests for quantum uncertainty calculator."""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path to allow import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantum.uncertainty import (
    calculate_uncertainty,
    UncertaintyCalculator,
    shannon_entropy_normalized,
    purity_measure,
    jsd_distance
)


class TestUncertaintyCalculation:
    """Test uncertainty calculation."""
    
    def test_pure_state_low_uncertainty(self):
        """Pure state should have low uncertainty."""
        pure = np.array([1.0, 0.0, 0.0])
        result = calculate_uncertainty(pure)
        
        assert result.value < 0.3
        assert result.entropy_normalized < 0.1
        assert result.impurity < 0.1
    
    def test_mixed_state_high_uncertainty(self):
        """Maximally mixed state should have high uncertainty."""
        mixed = np.array([0.33, 0.33, 0.34])
        result = calculate_uncertainty(mixed)
        
        assert result.value > 0.6
        assert result.entropy_normalized > 0.9
    
    def test_entropy_monotonic(self):
        """Increasing entropy should increase uncertainty."""
        state1 = np.array([0.9, 0.1])
        state2 = np.array([0.7, 0.3])
        state3 = np.array([0.5, 0.5])
        
        r1 = calculate_uncertainty(state1)
        r2 = calculate_uncertainty(state2)
        r3 = calculate_uncertainty(state3)
        
        assert r1.value < r2.value < r3.value
    
    def test_purity_decrease_increases_uncertainty(self):
        """Decreasing purity should increase uncertainty."""
        pure = np.array([1.0, 0.0])
        mixed = np.array([0.5, 0.5])
        
        r_pure = calculate_uncertainty(pure)
        r_mixed = calculate_uncertainty(mixed)
        
        assert r_pure.value < r_mixed.value
        assert r_pure.impurity < r_mixed.impurity
    
    def test_drift_increases_uncertainty(self):
        """Temporal drift should increase uncertainty."""
        state1 = np.array([0.7, 0.3])
        state2 = np.array([0.3, 0.7])
        
        # Without drift
        r_no_drift = calculate_uncertainty(state1, prev_state=None)
        
        # With drift
        r_with_drift = calculate_uncertainty(state2, prev_state=state1)
        
        assert r_with_drift.value > r_no_drift.value
        assert r_with_drift.drift > 0.3
    
    def test_clamp_to_zero_one(self):
        """All values should be clamped to [0, 1]."""
        # Extreme cases
        extreme_states = [
            np.array([1.0, 0.0]),
            np.array([0.0, 1.0]),
            np.array([0.5, 0.5]),
            np.array([0.1, 0.9]),
            np.array([0.33, 0.33, 0.34])
        ]
        
        for state in extreme_states:
            result = calculate_uncertainty(state)
            assert 0.0 <= result.value <= 1.0
            assert 0.0 <= result.entropy_normalized <= 1.0
            assert 0.0 <= result.impurity <= 1.0
            assert 0.0 <= result.drift <= 1.0
    
    def test_dimension_invariance(self):
        """Normalization should work across dimensions."""
        state_2d = np.array([0.5, 0.5])
        state_3d = np.array([0.33, 0.33, 0.34])
        state_4d = np.array([0.25, 0.25, 0.25, 0.25])
        
        r2 = calculate_uncertainty(state_2d)
        r3 = calculate_uncertainty(state_3d)
        r4 = calculate_uncertainty(state_4d)
        
        # All should be high (maximally mixed)
        # Dimensions increase, but normalized entropy should keep Q high
        assert r2.value > 0.6
        assert r3.value > 0.6
        assert r4.value > 0.6


class TestUncertaintyCalculator:
    """Test stateful calculator."""
    
    def test_automatic_drift_tracking(self):
        """Calculator should track drift automatically."""
        calc = UncertaintyCalculator()
        
        r1 = calc.calculate(np.array([0.7, 0.3]))
        assert r1.drift == 0.0  # No previous state
        
        r2 = calc.calculate(np.array([0.3, 0.7]))
        assert r2.drift > 0.3  # Large drift
    
    def test_history_tracking(self):
        """Calculator should maintain history."""
        calc = UncertaintyCalculator()
        
        calc.calculate(np.array([0.7, 0.3]))
        calc.calculate(np.array([0.5, 0.5]))
        calc.calculate(np.array([0.3, 0.7]))
        
        assert len(calc.history) == 3
    
    def test_reset(self):
        """Reset should clear history and state."""
        calc = UncertaintyCalculator()
        
        calc.calculate(np.array([0.7, 0.3]))
        calc.calculate(np.array([0.5, 0.5]))
        
        calc.reset()
        
        assert len(calc.history) == 0
        assert calc.prev_state is None
