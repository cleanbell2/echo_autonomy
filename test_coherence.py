"""
Unit tests for coherence module.
"""

import pytest
import numpy as np
from coherence import (
    quantum_coherence_l1,
    quantum_coherence_relative_entropy,
    quantum_coherence,
    coherence_measures,
    CoherenceAnalyzer,
    create_pure_state_coherence_matrix,
    create_mixed_state_coherence_matrix
)


class TestQuantumCoherenceL1:
    """Test l1-norm quantum coherence calculations."""
    
    def test_pure_state_zero_coherence(self):
        """Test that pure computational basis states have zero coherence."""
        # |0⟩ state
        rho_0 = np.array([[1, 0], [0, 0]], dtype=complex)
        coherence = quantum_coherence_l1(rho_0)
        assert coherence == 0.0
        
        # |1⟩ state
        rho_1 = np.array([[0, 0], [0, 1]], dtype=complex)
        coherence = quantum_coherence_l1(rho_1)
        assert coherence == 0.0
    
    def test_superposition_state_coherence(self):
        """Test that superposition states have non-zero coherence."""
        # |+⟩ = (|0⟩ + |1⟩)/√2
        rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        coherence = quantum_coherence_l1(rho_plus)
        assert coherence == 1.0  # |ρ_01| + |ρ_10| = 0.5 + 0.5 = 1.0
        
        # |−⟩ = (|0⟩ - |1⟩)/√2
        rho_minus = np.array([[0.5, -0.5], [-0.5, 0.5]], dtype=complex)
        coherence = quantum_coherence_l1(rho_minus)
        assert coherence == 1.0  # |ρ_01| + |ρ_10| = 0.5 + 0.5 = 1.0
    
    def test_maximally_mixed_state_zero_coherence(self):
        """Test that maximally mixed state has zero coherence."""
        rho_mixed = np.eye(2) / 2
        coherence = quantum_coherence_l1(rho_mixed)
        assert coherence == 0.0
    
    def test_partial_coherence(self):
        """Test partially coherent state."""
        # Mixed state with some coherence
        rho_partial = 0.7 * np.array([[1, 0], [0, 0]], dtype=complex) + \
                     0.3 * np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        
        coherence = quantum_coherence_l1(rho_partial)
        expected = 0.3  # 0.3 * (0.5 + 0.5) = 0.3
        assert coherence == pytest.approx(expected, rel=1e-10)
    
    def test_higher_dimensional_state(self):
        """Test 3x3 state."""
        # Superposition in 3D: (|0⟩ + |1⟩)/√2
        rho_3d = np.zeros((3, 3), dtype=complex)
        rho_3d[0, 0] = 0.5
        rho_3d[0, 1] = 0.5
        rho_3d[1, 0] = 0.5
        rho_3d[1, 1] = 0.5
        
        coherence = quantum_coherence_l1(rho_3d)
        expected = 1.0  # |ρ_01| + |ρ_10| = 0.5 + 0.5 = 1.0
        assert coherence == pytest.approx(expected, rel=1e-10)
    
    def test_complex_off_diagonal_elements(self):
        """Test state with complex off-diagonal elements."""
        # State with phase: (|0⟩ + i|1⟩)/√2
        rho_complex = np.array([[0.5, -0.5j], [0.5j, 0.5]], dtype=complex)
        coherence = quantum_coherence_l1(rho_complex)
        expected = 1.0  # |ρ_01| + |ρ_10| = 0.5 + 0.5 = 1.0
        assert coherence == pytest.approx(expected, rel=1e-10)
    
    def test_invalid_matrix(self):
        """Test invalid matrix inputs."""
        # Non-square matrix
        with pytest.raises(ValueError, match="must be square"):
            quantum_coherence_l1(np.array([[1, 2, 3]]))
        
        # Empty matrix
        with pytest.raises(ValueError, match="cannot be empty"):
            quantum_coherence_l1(np.array([]))
        
        # NaN values
        with pytest.raises(ValueError, match="contains invalid values"):
            quantum_coherence_l1(np.array([[1, np.nan], [0, 1]]))
        
        # Infinite values
        with pytest.raises(ValueError, match="contains invalid values"):
            quantum_coherence_l1(np.array([[1, np.inf], [0, 1]]))


class TestQuantumCoherenceRelativeEntropy:
    """Test relative entropy quantum coherence calculations."""
    
    def test_pure_state_zero_coherence(self):
        """Test that pure states have zero relative entropy coherence."""
        rho_0 = np.array([[1, 0], [0, 0]], dtype=complex)
        coherence = quantum_coherence_relative_entropy(rho_0)
        assert coherence == 0.0
    
    def test_superposition_state_coherence(self):
        """Test that superposition states have non-zero coherence."""
        rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        coherence = quantum_coherence_relative_entropy(rho_plus)
        assert coherence > 0
        # Should be ln(2) for this state
        expected = np.log(2)
        assert coherence == pytest.approx(expected, rel=1e-10)
    
    def test_maximally_mixed_state_zero_coherence(self):
        """Test that maximally mixed state has zero coherence."""
        rho_mixed = np.eye(2) / 2
        coherence = quantum_coherence_relative_entropy(rho_mixed)
        assert coherence == 0.0
    
    def test_diagonal_state_zero_coherence(self):
        """Test that any diagonal state has zero coherence."""
        rho_diagonal = np.array([[0.7, 0], [0, 0.3]], dtype=complex)
        coherence = quantum_coherence_relative_entropy(rho_diagonal)
        assert coherence == 0.0


class TestQuantumCoherence:
    """Test unified quantum coherence function."""
    
    def test_l1_method(self):
        """Test l1 method through unified function."""
        rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        coherence = quantum_coherence(rho_plus, method='l1')
        assert coherence == 1.0
    
    def test_relative_entropy_method(self):
        """Test relative entropy method through unified function."""
        rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        coherence = quantum_coherence(rho_plus, method='relative_entropy')
        expected = np.log(2)
        assert coherence == pytest.approx(expected, rel=1e-10)
    
    def test_invalid_method(self):
        """Test invalid method raises error."""
        rho = np.eye(2) / 2
        with pytest.raises(ValueError, match="Method must be 'l1' or 'relative_entropy'"):
            quantum_coherence(rho, method='invalid')


class TestCoherenceMeasures:
    """Test coherence measures function."""
    
    def test_both_measures(self):
        """Test that both measures are calculated correctly."""
        rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        measures = coherence_measures(rho_plus)
        
        assert 'l1_norm' in measures
        assert 'relative_entropy' in measures
        assert measures['l1_norm'] == 1.0
        assert measures['relative_entropy'] == pytest.approx(np.log(2), rel=1e-10)
    
    def test_zero_coherence_state(self):
        """Test measures for zero coherence state."""
        rho_0 = np.array([[1, 0], [0, 0]], dtype=complex)
        measures = coherence_measures(rho_0)
        
        assert measures['l1_norm'] == 0.0
        assert measures['relative_entropy'] == 0.0


class TestCoherenceAnalyzer:
    """Test CoherenceAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = CoherenceAnalyzer(tolerance=1e-10)
        assert analyzer.tolerance == 1e-10
        assert analyzer.analysis_history == []
    
    def test_analyze_pure_state(self):
        """Test analysis of pure state."""
        analyzer = CoherenceAnalyzer()
        rho_0 = np.array([[1, 0], [0, 0]], dtype=complex)
        
        result = analyzer.analyze_state(rho_0, "pure_0")
        
        assert result['name'] == "pure_0"
        assert result['l1_norm'] == 0.0
        assert result['relative_entropy'] == 0.0
        assert result['purity'] == 1.0  # Pure state has purity 1
        assert result['trace'] == 1.0
    
    def test_analyze_superposition_state(self):
        """Test analysis of superposition state."""
        analyzer = CoherenceAnalyzer()
        rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        
        result = analyzer.analyze_state(rho_plus, "superposition")
        
        assert result['name'] == "superposition"
        assert result['l1_norm'] == 1.0
        assert result['relative_entropy'] == pytest.approx(np.log(2), rel=1e-10)
        assert result['purity'] == 1.0  # Pure state
        assert result['trace'] == 1.0
    
    def test_analyze_mixed_state(self):
        """Test analysis of mixed state."""
        analyzer = CoherenceAnalyzer()
        rho_mixed = np.eye(2) / 2
        
        result = analyzer.analyze_state(rho_mixed, "mixed")
        
        assert result['name'] == "mixed"
        assert result['l1_norm'] == 0.0
        assert result['relative_entropy'] == 0.0
        assert result['purity'] == 0.5  # Tr(ρ²) = 0.5 for maximally mixed 2x2
        assert result['trace'] == 1.0
    
    def test_compare_states(self):
        """Test state comparison."""
        analyzer = CoherenceAnalyzer()
        
        states = {
            'pure_0': np.array([[1, 0], [0, 0]], dtype=complex),
            'superposition': np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex),
            'mixed': np.eye(2) / 2
        }
        
        results = analyzer.compare_states(states)
        
        assert len(results) == 3
        assert 'pure_0' in results
        assert 'superposition' in results
        assert 'mixed' in results
        
        # Check that superposition has highest coherence
        assert results['superposition']['l1_norm'] > results['pure_0']['l1_norm']
        assert results['superposition']['l1_norm'] > results['mixed']['l1_norm']
    
    def test_coherence_spectrum(self):
        """Test coherence spectrum calculation."""
        analyzer = CoherenceAnalyzer()
        
        states = {
            'pure': np.array([[1, 0], [0, 0]], dtype=complex),
            'coherent': np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        }
        
        spectrum = analyzer.coherence_spectrum(states)
        
        assert 'states' in spectrum
        assert 'l1_norm_values' in spectrum
        assert 'relative_entropy_values' in spectrum
        assert 'purity_values' in spectrum
        
        assert len(spectrum['states']) == 2
        assert len(spectrum['l1_norm_values']) == 2
    
    def test_find_most_coherent(self):
        """Test finding most coherent state."""
        analyzer = CoherenceAnalyzer()
        
        states = {
            'pure': np.array([[1, 0], [0, 0]], dtype=complex),
            'coherent': np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex),
            'mixed': np.eye(2) / 2
        }
        
        most_coherent_l1 = analyzer.find_most_coherent(states, 'l1')
        most_coherent_re = analyzer.find_most_coherent(states, 'relative_entropy')
        
        assert most_coherent_l1 == 'coherent'
        assert most_coherent_re == 'coherent'
    
    def test_analysis_history(self):
        """Test analysis history tracking."""
        analyzer = CoherenceAnalyzer()
        
        rho_0 = np.array([[1, 0], [0, 0]], dtype=complex)
        rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        
        analyzer.analyze_state(rho_0, "state1")
        analyzer.analyze_state(rho_plus, "state2")
        
        assert len(analyzer.analysis_history) == 2
        assert analyzer.analysis_history[0]['name'] == "state1"
        assert analyzer.analysis_history[1]['name'] == "state2"
        
        # Reset history
        analyzer.reset_history()
        assert len(analyzer.analysis_history) == 0


class TestStateCreation:
    """Test state creation functions."""
    
    def test_create_pure_state_coherence_matrix(self):
        """Test pure state coherence matrix creation."""
        # Create |+⟩ state
        rho = create_pure_state_coherence_matrix(1/np.sqrt(2))
        
        expected = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        np.testing.assert_array_almost_equal(rho, expected)
        
        # Check it's a valid density matrix
        engine = __import__('e_break_engine').EBreachEngine()
        engine._validate_density_matrix(rho)
    
    def test_create_pure_state_higher_dimension(self):
        """Test pure state in higher dimension."""
        rho = create_pure_state_coherence_matrix(1/np.sqrt(2), basis_dim=3)
        
        assert rho.shape == (3, 3)
        assert np.isclose(np.trace(rho), 1.0)
        
        # Should be |ψ⟩ = (1/√2)|0⟩ + (1/√2)|1⟩ + 0|2⟩
        expected = np.zeros((3, 3), dtype=complex)
        expected[0, 0] = 0.5
        expected[0, 1] = 0.5
        expected[1, 0] = 0.5
        expected[1, 1] = 0.5
        
        np.testing.assert_array_almost_equal(rho, expected)
    
    def test_create_pure_state_invalid_amplitude(self):
        """Test invalid amplitude."""
        with pytest.raises(ValueError, match="Amplitude magnitude cannot exceed 1"):
            create_pure_state_coherence_matrix(2.0)
        
        with pytest.raises(ValueError, match="Basis dimension must be at least 2"):
            create_pure_state_coherence_matrix(1.0, basis_dim=1)
    
    def test_create_mixed_state_coherence_matrix(self):
        """Test mixed state coherence matrix creation."""
        rho = create_mixed_state_coherence_matrix(pure_state_weight=0.5, coherence_magnitude=1.0)
        
        assert rho.shape == (2, 2)
        assert np.isclose(np.trace(rho), 1.0)
        
        # Should be 0.5 * coherent + 0.5 * incoherent
        coherent = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        incoherent = np.eye(2) / 2
        expected = 0.5 * coherent + 0.5 * incoherent
        
        np.testing.assert_array_almost_equal(rho, expected)
    
    def test_create_mixed_state_invalid_parameters(self):
        """Test invalid parameters for mixed state."""
        with pytest.raises(ValueError, match="pure_state_weight must be between 0 and 1"):
            create_mixed_state_coherence_matrix(pure_state_weight=1.5)
        
        with pytest.raises(ValueError, match="coherence_magnitude must be between 0 and 1"):
            create_mixed_state_coherence_matrix(coherence_magnitude=1.5)


class TestEdgeCases:
    """Test edge cases and special conditions."""
    
    def test_very_small_coherence(self):
        """Test state with very small coherence."""
        # State with tiny off-diagonal elements
        rho = np.array([[0.5, 1e-15], [1e-15, 0.5]], dtype=complex)
        coherence = quantum_coherence_l1(rho)
        expected = 2e-15
        assert coherence == pytest.approx(expected, rel=1e-10)
    
    def test_numerical_stability(self):
        """Test numerical stability with tolerance."""
        analyzer = CoherenceAnalyzer(tolerance=1e-12)
        
        # State with very small eigenvalues
        rho = np.array([[0.999999999, 1e-10], [1e-10, 1e-9]], dtype=complex)
        
        # Should not raise errors
        result = analyzer.analyze_state(rho, "nearly_pure")
        assert result['trace'] == pytest.approx(1.0, rel=1e-10)
    
    def test_large_dimensional_state(self):
        """Test large dimensional state."""
        dim = 10
        # Create superposition of first two states
        rho = np.zeros((dim, dim), dtype=complex)
        rho[0, 0] = 0.5
        rho[0, 1] = 0.5
        rho[1, 0] = 0.5
        rho[1, 1] = 0.5
        
        coherence = quantum_coherence_l1(rho)
        assert coherence == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])