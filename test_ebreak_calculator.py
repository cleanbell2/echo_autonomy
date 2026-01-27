"""
Comprehensive unit tests for ebreak_calculator module.
"""

import pytest
import numpy as np
from ebreak_calculator import (
    EBreakCalculator,
    create_test_quantum_systems,
    create_test_channels,
    example_usage
)
from e_break_engine import EBreachEngine
from non_unitarity import create_unitary_channel, create_dephasing_channel


class TestEBreakCalculator:
    """Test EBreakCalculator class."""
    
    def test_calculator_initialization(self):
        """Test calculator initialization."""
        calc = EBreakCalculator(gamma=2.0, theta_integrity_threshold=0.2)
        
        assert calc.gamma == 2.0
        assert calc.theta_integrity_threshold == 0.2
        assert calc.tolerance == 1e-12
        assert isinstance(calc.ebreak_engine, EBreachEngine)
        assert calc.analysis_history == []
    
    def test_basic_ebreak_calculation(self):
        """Test basic E_break calculation."""
        calc = EBreakCalculator()
        
        # Pure state |0⟩
        rho = np.array([[1, 0], [0, 0]], dtype=complex)
        
        results = calc.calculate_ebreak(
            density_matrix=rho,
            work=5.0,
            free_energy_change=3.0
        )
        
        # Check required keys
        required_keys = [
            'von_neumann_entropy', 'delta_von_neumann_entropy',
            'thermodynamic_entropy', 'gamma_times_ts',
            'coherence_l1_norm', 'coherence_relative_entropy', 'delta_c',
            'non_unitarity', 'bias_induction', 'n_epsilon',
            'e_break_qbn', 'bcdsi_detected', 'theta_integrity',
            'analysis_summary'
        ]
        
        for key in required_keys:
            assert key in results
        
        # Check values are reasonable
        assert results['von_neumann_entropy'] >= 0
        assert results['coherence_l1_norm'] >= 0
        assert results['coherence_relative_entropy'] >= 0
        assert results['e_break_qbn'] >= 0
        assert 0 <= results['theta_integrity'] <= 1
    
    def test_thermodynamic_component(self):
        """Test thermodynamic entropy component."""
        calc = EBreakCalculator(gamma=2.0)
        
        rho = np.eye(2) / 2  # Maximally mixed state
        work = 10.0
        free_energy_change = 5.0
        
        results = calc.calculate_ebreak(rho, work, free_energy_change)
        
        # γ·TΣ = γ·(W - ΔF) = 2.0 * (10.0 - 5.0) = 10.0
        expected_thermo = 2.0 * (10.0 - 5.0)
        assert results['gamma_times_ts'] == pytest.approx(expected_thermo, rel=1e-10)
    
    def test_coherence_component(self):
        """Test coherence component."""
        calc = EBreakCalculator()
        
        # Superposition state should have coherence
        rho = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        
        results = calc.calculate_ebreak(rho)
        
        assert results['coherence_l1_norm'] > 0
        assert results['coherence_relative_entropy'] > 0
        assert results['delta_c'] > 0
    
    def test_non_unitarity_component(self):
        """Test non-unitarity component."""
        calc = EBreakCalculator()
        
        rho = np.eye(2) / 2
        unitary_channel = create_unitary_channel(np.pi/4)
        dephasing_channel = create_dephasing_channel(0.5)
        
        # Unitary channel should have zero non-unitarity
        results_unitary = calc.calculate_ebreak(rho, quantum_channel=unitary_channel)
        assert results_unitary['non_unitarity'] < 1e-10
        
        # Dephasing channel should have non-zero non-unitarity
        results_dephasing = calc.calculate_ebreak(rho, quantum_channel=dephasing_channel)
        assert results_dephasing['non_unitarity'] > 0
    
    def test_reference_state_comparison(self):
        """Test comparison with reference state."""
        calc = EBreakCalculator()
        
        # Current state: superposition
        rho_current = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        
        # Reference state: pure |0⟩
        rho_ref = np.array([[1, 0], [0, 0]], dtype=complex)
        
        results = calc.calculate_ebreak(
            density_matrix=rho_current,
            reference_density_matrix=rho_ref
        )
        
        # Should have non-zero entropy change
        assert results['delta_von_neumann_entropy'] > 0
        
        # Should have non-zero coherence change
        assert results['delta_c'] > 0
    
    def test_bcdsi_detection(self):
        """Test BCDSI detection."""
        # Low threshold should trigger detection
        calc_low = EBreakCalculator(theta_integrity_threshold=0.9)
        
        rho = np.eye(2) / 2
        results = calc_low.calculate_ebreak(rho)
        
        # Should detect BCDSI due to low threshold
        assert results['bcdsi_detected'] is True
        
        # High threshold should not trigger detection
        calc_high = EBreakCalculator(theta_integrity_threshold=0.1)
        results_high = calc_high.calculate_ebreak(rho)
        
        assert results_high['bcdsi_detected'] is False
    
    def test_coherence_weight_parameter(self):
        """Test coherence weight parameter."""
        calc = EBreakCalculator()
        
        rho = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        
        # Test different coherence weights
        for weight in [0.0, 0.5, 1.0]:
            results = calc.calculate_ebreak(rho, coherence_weight=weight)
            assert 0 <= results['delta_c'] <= 1
    
    def test_invalid_density_matrix(self):
        """Test invalid density matrix."""
        calc = EBreakCalculator()
        
        # Non-square matrix
        with pytest.raises(ValueError, match="must be square"):
            calc.calculate_ebreak(np.array([[1, 2, 3]]))
        
        # Non-Hermitian matrix
        with pytest.raises(ValueError, match="must be Hermitian"):
            calc.calculate_ebreak(np.array([[1, 1], [0, 0]]))
        
        # Wrong trace
        with pytest.raises(ValueError, match="trace must be 1"):
            calc.calculate_ebreak(np.array([[2, 0], [0, 0]]))
    
    def test_analysis_history(self):
        """Test analysis history tracking."""
        calc = EBreakCalculator()
        
        rho = np.eye(2) / 2
        
        # Perform multiple analyses
        calc.calculate_ebreak(rho)
        calc.calculate_ebreak(rho)
        
        assert len(calc.analysis_history) == 2
        
        # Reset history
        calc.reset_history()
        assert len(calc.analysis_history) == 0
    
    def test_compare_states(self):
        """Test state comparison functionality."""
        calc = EBreakCalculator()
        
        systems = create_test_quantum_systems()
        
        results = calc.compare_states(systems)
        
        assert len(results) == len(systems)
        
        for state_name, result in results.items():
            assert 'e_break_qbn' in result
            assert 'bcdsi_detected' in result
    
    def test_find_anomalous_state(self):
        """Test anomalous state detection."""
        calc = EBreakCalculator()
        
        systems = create_test_quantum_systems()
        comparison = calc.compare_states(systems)
        
        anomalous = calc.find_anomalous_state(comparison)
        
        assert anomalous in systems.keys()
        assert anomalous != ""
    
    def test_get_analysis_statistics(self):
        """Test analysis statistics."""
        calc = EBreakCalculator()
        
        # Empty history
        stats = calc.get_analysis_statistics()
        assert 'message' in stats
        
        # With history
        rho = np.eye(2) / 2
        calc.calculate_ebreak(rho)
        calc.calculate_ebreak(rho)
        
        stats = calc.get_analysis_statistics()
        
        assert stats['total_analyses'] == 2
        assert 'mean_ebreak' in stats
        assert 'std_ebreak' in stats
        assert 'bcdsi_rate' in stats


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_create_test_quantum_systems(self):
        """Test test quantum systems creation."""
        systems = create_test_quantum_systems()
        
        assert len(systems) == 4
        assert 'pure_0' in systems
        assert 'superposition_plus' in systems
        assert 'maximally_mixed' in systems
        assert 'partial_coherence' in systems
        
        # Check all are valid density matrices
        engine = EBreachEngine()
        for name, rho in systems.items():
            engine._validate_density_matrix(rho)
    
    def test_create_test_channels(self):
        """Test test channels creation."""
        channels = create_test_channels()
        
        assert len(channels) == 3
        assert 'unitary' in channels
        assert 'dephasing' in channels
        assert 'damping' in channels
        
        # Check all are valid matrices
        for name, channel in channels.items():
            assert channel is not None
            assert not np.any(np.isnan(channel))
            assert not np.any(np.isinf(channel))


class TestEBreakFormula:
    """Test E_break formula implementation."""
    
    def test_formula_components(self):
        """Test individual formula components."""
        calc = EBreakCalculator(gamma=1.0)
        
        # Known test case
        rho = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        work = 10.0
        free_energy_change = 5.0
        
        results = calc.calculate_ebreak(rho, work, free_energy_change)
        
        # Verify formula: E_break^QBN = ΔS + γ·TΣ + ΔC + ℕ(ε)
        expected = (results['delta_von_neumann_entropy'] + 
                   results['gamma_times_ts'] + 
                   results['delta_c'] + 
                   results['n_epsilon'])
        
        assert results['e_break_qbn'] == pytest.approx(expected, rel=1e-10)
    
    def test_formula_with_reference_state(self):
        """Test formula with reference state for ΔS and ΔC."""
        calc = EBreakCalculator()
        
        # Current: superposition
        rho_current = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        
        # Reference: pure state
        rho_ref = np.array([[1, 0], [0, 0]], dtype=complex)
        
        results = calc.calculate_ebreak(
            density_matrix=rho_current,
            reference_density_matrix=rho_ref,
            work=5.0,
            free_energy_change=3.0
        )
        
        # Should have positive changes
        assert results['delta_von_neumann_entropy'] > 0
        assert results['delta_c'] > 0
        
        # Formula should still hold
        expected = (results['delta_von_neumann_entropy'] + 
                   results['gamma_times_ts'] + 
                   results['delta_c'] + 
                   results['n_epsilon'])
        
        assert results['e_break_qbn'] == pytest.approx(expected, rel=1e-10)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_zero_work_and_free_energy(self):
        """Test with zero work and free energy."""
        calc = EBreakCalculator()
        
        rho = np.eye(2) / 2
        results = calc.calculate_ebreak(rho, work=0.0, free_energy_change=0.0)
        
        assert results['gamma_times_ts'] == 0.0
        assert results['e_break_qbn'] >= 0
    
    def test_negative_thermodynamic_contribution(self):
        """Test negative thermodynamic contribution."""
        calc = EBreakCalculator()
        
        rho = np.eye(2) / 2
        # W < ΔF should give negative γ·TΣ
        results = calc.calculate_ebreak(rho, work=3.0, free_energy_change=5.0)
        
        assert results['gamma_times_ts'] < 0
        # But total E_break should still be non-negative
        assert results['e_break_qbn'] >= 0
    
    def test_high_gamma_value(self):
        """Test with high gamma value."""
        calc = EBreakCalculator(gamma=10.0)
        
        rho = np.eye(2) / 2
        results = calc.calculate_ebreak(rho, work=5.0, free_energy_change=3.0)
        
        # Should scale with gamma
        expected_thermo = 10.0 * (5.0 - 3.0)
        assert results['gamma_times_ts'] == pytest.approx(expected_thermo, rel=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])