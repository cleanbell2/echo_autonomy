"""
Unit tests for non_unitarity module.
"""

import pytest
import numpy as np
from non_unitarity import (
    non_unitarity,
    bias_induction,
    channel_completely_positive,
    channel_trace_preserving,
    NonUnitarityAnalyzer,
    create_unitary_channel,
    create_dephasing_channel,
    create_amplitude_damping_channel
)


class TestNonUnitarity:
    """Test non-unitarity calculations."""
    
    def test_unitary_channel_zero_non_unitarity(self):
        """Test that unitary channel has zero non-unitarity."""
        # Create unitary channel
        unitary = create_unitary_channel(np.pi/4)
        
        # All methods should return zero for unitary
        assert non_unitarity(unitary, 'trace_distance') == pytest.approx(0.0, abs=1e-10)
        assert non_unitarity(unitary, 'fidelity') == pytest.approx(0.0, abs=1e-10)
        assert non_unitarity(unitary, 'norm_difference') == pytest.approx(0.0, abs=1e-10)
    
    def test_dephasing_channel_non_unitarity(self):
        """Test non-unitarity of dephasing channel."""
        dephasing = create_dephasing_channel(0.5)
        
        # Should have non-zero non-unitarity
        for method in ['trace_distance', 'fidelity', 'norm_difference']:
            result = non_unitarity(dephasing, method)
            assert result > 0
    
    def test_amplitude_damping_channel_non_unitarity(self):
        """Test non-unitarity of amplitude damping channel."""
        damping = create_amplitude_damping_channel(0.3)
        
        # Should have non-zero non-unitarity
        for method in ['trace_distance', 'fidelity', 'norm_difference']:
            result = non_unitarity(damping, method)
            assert result > 0
    
    def test_invalid_method(self):
        """Test invalid method raises error."""
        channel = create_unitary_channel(np.pi/4)
        
        with pytest.raises(ValueError, match="Method 'invalid' not supported"):
            non_unitarity(channel, 'invalid')
    
    def test_invalid_channel(self):
        """Test invalid channel inputs."""
        # Empty matrix
        with pytest.raises(ValueError, match="cannot be empty"):
            non_unitarity(np.array([]))
        
        # 1D matrix
        with pytest.raises(ValueError, match="must be at least 2D"):
            non_unitarity(np.array([1, 2]))
        
        # NaN values
        with pytest.raises(ValueError, match="contains invalid values"):
            non_unitarity(np.array([[1, np.nan], [0, 1]]))
        
        # Infinite values
        with pytest.raises(ValueError, match="contains invalid values"):
            non_unitarity(np.array([[1, np.inf], [0, 1]]))


class TestBiasInduction:
    """Test bias induction calculations."""
    
    def test_unitary_channel_zero_bias(self):
        """Test that unitary channel has zero bias with identity reference."""
        unitary = create_unitary_channel(np.pi/6)
        
        # Should have zero bias with identity reference
        for method in ['operator_norm', 'trace_norm', 'fidelity']:
            result = bias_induction(unitary, method=method)
            assert result >= 0  # Should be non-negative
    
    def test_bias_with_custom_reference(self):
        """Test bias calculation with custom reference."""
        channel = create_unitary_channel(np.pi/4)
        reference = create_unitary_channel(np.pi/6)
        
        # Should have non-zero bias
        for method in ['operator_norm', 'trace_norm', 'fidelity']:
            result = bias_induction(channel, reference, method)
            assert result > 0
    
    def test_dephasing_channel_bias(self):
        """Test bias of dephasing channel."""
        dephasing = create_dephasing_channel(0.5)
        
        # Should have non-zero bias
        for method in ['operator_norm', 'trace_norm', 'fidelity']:
            result = bias_induction(dephasing, method=method)
            assert result > 0
    
    def test_invalid_bias_method(self):
        """Test invalid bias method."""
        channel = create_unitary_channel(np.pi/4)
        
        with pytest.raises(ValueError, match="Method 'invalid' not supported"):
            bias_induction(channel, method='invalid')


class TestChannelProperties:
    """Test channel property checks."""
    
    def test_unitary_channel_properties(self):
        """Test properties of unitary channel."""
        unitary = create_unitary_channel(np.pi/4)
        
        assert channel_trace_preserving(unitary)
        assert channel_completely_positive(unitary)
    
    def test_dephasing_channel_properties(self):
        """Test properties of dephasing channel."""
        dephasing = create_dephasing_channel(0.5)
        
        assert channel_trace_preserving(dephasing)
        assert channel_completely_positive(dephasing)
    
    def test_amplitude_damping_channel_properties(self):
        """Test properties of amplitude damping channel."""
        damping = create_amplitude_damping_channel(0.3)
        
        assert channel_trace_preserving(damping)
        assert channel_completely_positive(damping)


class TestNonUnitarityAnalyzer:
    """Test NonUnitarityAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = NonUnitarityAnalyzer(tolerance=1e-10)
        assert analyzer.tolerance == 1e-10
        assert analyzer.analysis_history == []
    
    def test_analyze_unitary_channel(self):
        """Test analysis of unitary channel."""
        analyzer = NonUnitarityAnalyzer()
        unitary = create_unitary_channel(np.pi/4)
        
        result = analyzer.analyze_channel(unitary, "test_unitary")
        
        assert result['name'] == "test_unitary"
        assert result['is_unitary'] is True
        assert result['is_completely_positive'] is True
        assert result['is_trace_preserving'] is True
        
        # Non-unitarity measures should be very small
        for key in ['non_unitarity_trace_distance', 'non_unitarity_fidelity', 'non_unitarity_norm_difference']:
            assert result[key] < 1e-10
    
    def test_analyze_dephasing_channel(self):
        """Test analysis of dephasing channel."""
        analyzer = NonUnitarityAnalyzer()
        dephasing = create_dephasing_channel(0.5)
        
        result = analyzer.analyze_channel(dephasing, "test_dephasing")
        
        assert result['name'] == "test_dephasing"
        assert result['is_unitary'] is False
        assert result['is_completely_positive'] is True
        assert result['is_trace_preserving'] is True
        
        # Should have non-zero non-unitarity
        for key in ['non_unitarity_trace_distance', 'non_unitarity_fidelity', 'non_unitarity_norm_difference']:
            assert result[key] > 0
    
    def test_compare_channels(self):
        """Test channel comparison."""
        analyzer = NonUnitarityAnalyzer()
        
        channels = {
            'unitary': create_unitary_channel(np.pi/4),
            'dephasing': create_dephasing_channel(0.3),
            'damping': create_amplitude_damping_channel(0.2)
        }
        
        results = analyzer.compare_channels(channels)
        
        assert len(results) == 3
        assert 'unitary' in results
        assert 'dephasing' in results
        assert 'damping' in results
        
        # Unitary should have lowest non-unitarity
        assert results['unitary']['is_unitary'] is True
        assert results['dephasing']['is_unitary'] is False
        assert results['damping']['is_unitary'] is False
    
    def test_find_most_biased(self):
        """Test finding most biased channel."""
        analyzer = NonUnitarityAnalyzer()
        
        channels = {
            'unitary': create_unitary_channel(np.pi/4),
            'dephasing': create_dephasing_channel(0.8),  # High dephasing
            'damping': create_amplitude_damping_channel(0.1)  # Low damping
        }
        
        most_biased = analyzer.find_most_biased(channels, 'operator_norm')
        
        # Should be the dephasing channel (highest bias)
        assert most_biased == 'dephasing'
    
    def test_analysis_history(self):
        """Test analysis history tracking."""
        analyzer = NonUnitarityAnalyzer()
        
        # Analyze multiple channels
        analyzer.analyze_channel(create_unitary_channel(np.pi/4), "channel1")
        analyzer.analyze_channel(create_dephasing_channel(0.5), "channel2")
        
        assert len(analyzer.analysis_history) == 2
        assert analyzer.analysis_history[0]['name'] == "channel1"
        assert analyzer.analysis_history[1]['name'] == "channel2"
        
        # Reset history
        analyzer.reset_history()
        assert len(analyzer.analysis_history) == 0


class TestChannelCreation:
    """Test channel creation functions."""
    
    def test_create_unitary_channel(self):
        """Test unitary channel creation."""
        unitary = create_unitary_channel(np.pi/4, np.pi/6)
        
        assert unitary.shape == (2, 2)
        assert unitary.dtype == complex
        
        # Check if unitary
        product = unitary.conj().T @ unitary
        np.testing.assert_allclose(product, np.eye(2), atol=1e-10)
    
    def test_create_dephasing_channel(self):
        """Test dephasing channel creation."""
        dephasing = create_dephasing_channel(0.5)
        
        assert len(dephasing) == 2  # Two Kraus operators
        assert dephasing[0].shape == (2, 2)
        assert dephasing[1].shape == (2, 2)
    
    def test_create_amplitude_damping_channel(self):
        """Test amplitude damping channel creation."""
        damping = create_amplitude_damping_channel(0.3)
        
        assert len(damping) == 2  # Two Kraus operators
        assert damping[0].shape == (2, 2)
        assert damping[1].shape == (2, 2)
    
    def test_invalid_dephasing_rate(self):
        """Test invalid dephasing rate."""
        with pytest.raises(ValueError, match="Dephasing rate must be between 0 and 1"):
            create_dephasing_channel(-0.1)
        
        with pytest.raises(ValueError, match="Dephasing rate must be between 0 and 1"):
            create_dephasing_channel(1.1)
    
    def test_invalid_damping_rate(self):
        """Test invalid damping rate."""
        with pytest.raises(ValueError, match="Damping rate must be between 0 and 1"):
            create_amplitude_damping_channel(-0.1)
        
        with pytest.raises(ValueError, match="Damping rate must be between 0 and 1"):
            create_amplitude_damping_channel(1.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])