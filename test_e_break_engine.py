import unittest
import numpy as np
from e_break_engine import EBreachEngine


class TestEBreachEngine(unittest.TestCase):
    """Comprehensive unit tests for EBreachEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EBreachEngine(tolerance=1e-12)
        
        # Test density matrices
        self.maximally_mixed = np.eye(2) / 2
        self.pure_state = np.array([[1, 0], [0, 0]])
        self.coherent_state = np.array([[0.5, 0.3], [0.3, 0.5]])
        self.three_level_mixed = np.eye(3) / 3
        
    def test_init(self):
        """Test engine initialization."""
        engine = EBreachEngine()
        self.assertEqual(engine.tolerance, 1e-12)
        self.assertAlmostEqual(engine.kb, 1.380649e-23)
        
        engine_custom = EBreachEngine(tolerance=1e-8)
        self.assertEqual(engine_custom.tolerance, 1e-8)
    
    def test_validate_density_matrix_valid(self):
        """Test validation with valid density matrices."""
        # Should not raise exceptions
        self.engine._validate_density_matrix(self.maximally_mixed)
        self.engine._validate_density_matrix(self.pure_state)
        self.engine._validate_density_matrix(self.coherent_state)
        
    def test_validate_density_matrix_invalid(self):
        """Test validation with invalid density matrices."""
        # Non-square matrix
        with self.assertRaises(ValueError):
            self.engine._validate_density_matrix(np.array([[1, 2, 3]]))
            
        # Non-Hermitian matrix
        non_hermitian = np.array([[1, 1], [0, 0]])
        with self.assertRaises(ValueError):
            self.engine._validate_density_matrix(non_hermitian)
            
        # Wrong trace
        wrong_trace = np.array([[2, 0], [0, 0]])
        with self.assertRaises(ValueError):
            self.engine._validate_density_matrix(wrong_trace)
            
        # Not positive semidefinite
        negative_eval = np.array([[1, 2], [2, 1]])
        with self.assertRaises(ValueError):
            self.engine._validate_density_matrix(negative_eval)
    
    def test_von_neumann_entropy_maximally_mixed(self):
        """Test von Neumann entropy for maximally mixed state."""
        entropy = self.engine.von_neumann_entropy(self.maximally_mixed)
        expected = np.log(2)  # ln(2) for 2x2 maximally mixed state
        self.assertAlmostEqual(entropy, expected, places=10)
        
    def test_von_neumann_entropy_pure_state(self):
        """Test von Neumann entropy for pure state."""
        entropy = self.engine.von_neumann_entropy(self.pure_state)
        self.assertAlmostEqual(entropy, 0.0, places=10)
        
    def test_von_neumann_entropy_three_level(self):
        """Test von Neumann entropy for 3-level maximally mixed state."""
        entropy = self.engine.von_neumann_entropy(self.three_level_mixed)
        expected = np.log(3)
        self.assertAlmostEqual(entropy, expected, places=10)
    
    def test_thermodynamic_entropy(self):
        """Test thermodynamic entropy calculation."""
        temperature = 300.0  # Kelvin
        thermo_entropy = self.engine.thermodynamic_entropy(self.maximally_mixed, temperature)
        
        vn_entropy = self.engine.von_neumann_entropy(self.maximally_mixed)
        expected = self.engine.kb * vn_entropy
        
        self.assertAlmostEqual(thermo_entropy, expected, places=25)
        
    def test_thermodynamic_entropy_invalid_temperature(self):
        """Test thermodynamic entropy with invalid temperature."""
        with self.assertRaises(ValueError):
            self.engine.thermodynamic_entropy(self.maximally_mixed, 0)
        with self.assertRaises(ValueError):
            self.engine.thermodynamic_entropy(self.maximally_mixed, -100)
    
    def test_quantum_coherence_l1_norm(self):
        """Test l1-norm quantum coherence."""
        # Pure state should have zero coherence
        coherence = self.engine.quantum_coherence_l1_norm(self.pure_state)
        self.assertAlmostEqual(coherence, 0.0, places=10)
        
        # Maximally mixed state should have zero coherence
        coherence = self.engine.quantum_coherence_l1_norm(self.maximally_mixed)
        self.assertAlmostEqual(coherence, 0.0, places=10)
        
        # Coherent state should have non-zero coherence
        coherence = self.engine.quantum_coherence_l1_norm(self.coherent_state)
        self.assertGreater(coherence, 0.0)
        
    def test_quantum_coherence_relative_entropy(self):
        """Test relative entropy quantum coherence."""
        # Pure state should have zero coherence
        coherence = self.engine.quantum_coherence_relative_entropy(self.pure_state)
        self.assertAlmostEqual(coherence, 0.0, places=10)
        
        # Maximally mixed state should have zero coherence
        coherence = self.engine.quantum_coherence_relative_entropy(self.maximally_mixed)
        self.assertAlmostEqual(coherence, 0.0, places=10)
        
        # Coherent state should have non-zero coherence
        coherence = self.engine.quantum_coherence_relative_entropy(self.coherent_state)
        self.assertGreater(coherence, 0.0)
    
    def test_e_break_comprehensive(self):
        """Test comprehensive E_break calculation."""
        temperature = 300.0
        results = self.engine.e_break(self.coherent_state, temperature)
        
        # Check all required keys are present
        expected_keys = [
            'von_neumann_entropy', 'thermodynamic_entropy', 
            'coherence_l1_norm', 'coherence_relative_entropy',
            'e_break', 'temperature'
        ]
        for key in expected_keys:
            self.assertIn(key, results)
            
        # Check temperature is preserved
        self.assertEqual(results['temperature'], temperature)
        
        # Check relationships
        self.assertGreaterEqual(results['von_neumann_entropy'], 0)
        self.assertGreaterEqual(results['thermodynamic_entropy'], 0)
        self.assertGreaterEqual(results['coherence_l1_norm'], 0)
        self.assertGreaterEqual(results['coherence_relative_entropy'], 0)
        
    def test_e_break_invalid_coherence_weight(self):
        """Test E_break with invalid coherence weight."""
        with self.assertRaises(ValueError):
            self.engine.e_break(self.coherent_state, 300.0, coherence_weight=-0.1)
        with self.assertRaises(ValueError):
            self.engine.e_break(self.coherent_state, 300.0, coherence_weight=1.1)
    
    def test_create_pure_state(self):
        """Test pure state creation."""
        state_vector = np.array([1, 0])
        rho = self.engine.create_pure_state(state_vector)
        
        # Should match the pure state test matrix
        np.testing.assert_array_almost_equal(rho, self.pure_state)
        
        # Test normalization
        unnormalized = np.array([2, 1])
        rho_normalized = self.engine.create_pure_state(unnormalized)
        trace = np.trace(rho_normalized)
        self.assertAlmostEqual(trace.real, 1.0, places=10)
    
    def test_create_mixed_state(self):
        """Test mixed state creation."""
        probabilities = [0.7, 0.3]
        states = [
            np.array([1, 0]),  # |0⟩
            np.array([0, 1])   # |1⟩
        ]
        
        rho = self.engine.create_mixed_state(probabilities, states)
        expected = np.array([[0.7, 0], [0, 0.3]])
        
        np.testing.assert_array_almost_equal(rho, expected)
        
    def test_create_mixed_state_invalid(self):
        """Test mixed state creation with invalid inputs."""
        probabilities = [0.5, 0.3]  # Doesn't sum to 1
        states = [np.array([1, 0]), np.array([0, 1])]
        
        with self.assertRaises(ValueError):
            self.engine.create_mixed_state(probabilities, states)
            
        with self.assertRaises(ValueError):
            self.engine.create_mixed_state([0.5, 0.5], [np.array([1, 0])])  # Mismatched lengths
    
    def test_create_thermal_state(self):
        """Test thermal state creation."""
        # Simple 2x2 Hamiltonian
        H = np.array([[1, 0], [0, 2]])
        temperature = 300.0
        
        rho_thermal = self.engine.create_thermal_state(H, temperature)
        
        # Should be a valid density matrix
        self.engine._validate_density_matrix(rho_thermal)
        
        # Lower energy state should have higher population
        self.assertGreater(rho_thermal[0, 0], rho_thermal[1, 1])
        
    def test_create_thermal_state_invalid_temperature(self):
        """Test thermal state with invalid temperature."""
        H = np.array([[1, 0], [0, 2]])
        
        with self.assertRaises(ValueError):
            self.engine.create_thermal_state(H, 0)
        with self.assertRaises(ValueError):
            self.engine.create_thermal_state(H, -100)
    
    def test_known_quantum_states(self):
        """Test with known quantum states."""
        # Bell state (maximally entangled pure state)
        bell_state = 1/np.sqrt(2) * np.array([1, 0, 0, 1])
        rho_bell = self.engine.create_pure_state(bell_state)
        
        # Bell state should have zero entropy (pure state)
        entropy = self.engine.von_neumann_entropy(rho_bell)
        self.assertAlmostEqual(entropy, 0.0, places=10)
        
        # Reduced density matrix should have maximal entropy
        # For a 4x4 Bell state, trace out subsystem 2
        rho_reduced = np.array([[0.5, 0], [0, 0.5]])
        entropy_reduced = self.engine.von_neumann_entropy(rho_reduced)
        self.assertAlmostEqual(entropy_reduced, np.log(2), places=10)
    
    def test_numerical_stability(self):
        """Test numerical stability with edge cases."""
        # Very small eigenvalues
        small_eval_rho = np.array([[0.999999999, 0], [0, 1e-10]])
        entropy = self.engine.von_neumann_entropy(small_eval_rho)
        self.assertGreaterEqual(entropy, 0)
        
        # Nearly degenerate eigenvalues
        nearly_degenerate = np.array([[0.500000001, 0], [0, 0.499999999]])
        entropy = self.engine.von_neumann_entropy(nearly_degenerate)
        self.assertAlmostEqual(entropy, np.log(2), places=5)
    
    def test_matrix_size_consistency(self):
        """Test that calculations work for different matrix sizes."""
        for n in [2, 3, 4, 5]:
            # Create maximally mixed state
            rho = np.eye(n) / n
            entropy = self.engine.von_neumann_entropy(rho)
            expected = np.log(n)
            self.assertAlmostEqual(entropy, expected, places=10)


class TestEBreachEngineIntegration(unittest.TestCase):
    """Integration tests for realistic scenarios."""
    
    def setUp(self):
        self.engine = EBreachEngine()
    
    def test_thermal_state_analysis(self):
        """Test complete analysis of thermal states."""
        # Create a simple quantum system Hamiltonian
        H = np.array([
            [1.0, 0.1, 0.0],
            [0.1, 2.0, 0.1],
            [0.0, 0.1, 3.0]
        ])
        
        temperatures = [10.0, 100.0, 1000.0]
        
        for T in temperatures:
            rho_thermal = self.engine.create_thermal_state(H, T)
            results = self.engine.e_break(rho_thermal, T)
            
            # Verify physical consistency
            self.assertGreaterEqual(results['von_neumann_entropy'], 0)
            self.assertGreaterEqual(results['thermodynamic_entropy'], 0)
            self.assertGreaterEqual(results['e_break'], 0)
            
            # Higher temperature should generally increase entropy
            # (This is a simplified check - real behavior depends on energy gaps)
    
    def test_coherence_evolution(self):
        """Test coherence behavior in superposition states."""
        # Create coherent superposition
        theta = np.pi / 4  # Superposition angle
        
        for angle in [0, np.pi/8, np.pi/4, np.pi/2]:
            psi = np.array([
                np.cos(angle),
                np.sin(angle)
            ])
            rho = self.engine.create_pure_state(psi)
            
            results = self.engine.e_break(rho, 300.0)
            
            # Pure states should have zero von Neumann entropy
            self.assertAlmostEqual(results['von_neumann_entropy'], 0.0, places=10)
            
            # Coherence should vary with superposition
            if angle in [0, np.pi/2]:  # Computational basis states
                self.assertAlmostEqual(results['coherence_l1_norm'], 0.0, places=10)
            else:  # Superposition states
                self.assertGreater(results['coherence_l1_norm'], 0.0)


if __name__ == '__main__':
    unittest.main()