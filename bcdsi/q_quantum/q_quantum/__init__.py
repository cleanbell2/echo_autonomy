# q_quantum package - core modules

from typing import Union, Dict, Optional, List
import numpy as np
from scipy.linalg import logm, expm
from scipy.sparse import issparse

class EBreachEngine:
    """
    Ultrawork E_break calculation engine.
    
    E_break^QBN = ΔS + γ·TΣ + ΔC + ℕ(ε)
    """
    
    def __init__(self, theta_integrity: float = 0.1, tolerance: float = 1e-12):
        """
        Initialize E_break calculation engine.
        
        Args:
            theta_integrity: θ_integrity threshold for BCDSI detection
            tolerance: Numerical tolerance for calculations
        """
        self.theta_integrity = theta_integrity
        self.tolerance = tolerance
        self.kb = 1.380649e-23  # Boltzmann constant in J/K
    
    def calculate_ebreak(self, density_matrix: Union[np.ndarray, list], 
                          work: float = 0.0,
                          free_energy_change: float = 0.0,
                          coherence_matrix: Union[np.ndarray, list] = None,
                          channel_matrix: Union[np.ndarray, list] = None,
                          coherence_weight: float = 0.5) -> Dict:
        """
        Calculate comprehensive E_break metrics.
        
        Args:
            density_matrix: Current quantum state density matrix
            work: Work done (W)
            free_energy_change: Change in free energy (ΔF)
            coherence_matrix: Optional coherence matrix for state
            channel_matrix: Optional quantum channel matrix
            coherence_weight: Weight for coherence in final calculation (0-1)
            
        Returns:
            Dictionary containing all calculated metrics
        """
        # Convert inputs to numpy arrays
        rho = np.asarray(density_matrix, dtype=complex)
        
        # Calculate components
        delta_s = self.von_neumann_entropy(rho)
        
        # Thermodynamic entropy component
        gamma_ts = self.thermodynamic_entropy(work, free_energy_change)
        
        # Quantum coherence components
        if coherence_matrix is not None:
            coherence_l1 = self.quantum_coherence_l1(coherence_matrix)
            coherence_re = self.quantum_coherence_relative_entropy(coherence_matrix)
            
            # Use weighted combination
            delta_c = (1 - coherence_weight) * coherence_l1 + coherence_weight * coherence_re
        else:
            coherence_l1 = self.quantum_coherence_l1(rho)
            coherence_re = self.quantum_coherence_relative_entropy(rho)
            delta_c = (1 - coherence_weight) * coherence_l1 + coherence_weight * coherence_re
        
        # Non-unitarity components
        if channel_matrix is not None:
            non_unity = self.non_unitarity(channel_matrix, 'trace_distance', self.tolerance)
            bias = self.bias_induction(channel_matrix, 'operator_norm')
            n_epsilon = non_unity + bias
        else:
            non_unity = 0.0
            bias = 0.0
            n_epsilon = 0.0
        
        # Combined E_break value
        e_break_qbn = delta_s + gamma_ts + delta_c + n_epsilon
        
        # BCDSI detection
        theta_integrity = self._calculate_theta_integrity(delta_s, gamma_ts, delta_c, n_epsilon)
        bcdsi_detected = theta_integrity < self.theta_integrity
        
        return {
            'von_neumann_entropy': delta_s,
            'thermodynamic_entropy': gamma_ts,
            'coherence_l1_norm': coherence_l1 if coherence_matrix is not None else self.quantum_coherence_l1(rho),
            'coherence_relative_entropy': coherence_re if coherence_matrix is not None else self.quantum_coherence_relative_entropy(rho),
            'coherence_combined': delta_c,
            'non_unitarity': non_unity,
            'bias_induction': bias,
            'n_epsilon': n_epsilon,
            'e_break_qbn': e_break_qbn,
            'theta_integrity': theta_integrity,
            'bcdsi_detected': bcdsi_detected,
            'coherence_weight': coherence_weight,
            'work': work,
            'free_energy_change': free_energy_change,
            'gamma': self.theta_integrity
        }
    
    def _calculate_theta_integrity(self, delta_s: float, gamma_ts: float, 
                             delta_c: float, n_epsilon: float) -> float:
        """
        Calculate θ_integrity metric for BCDSI detection.
        
        Args:
            delta_s: von Neumann entropy change
            gamma_ts: Thermodynamic entropy contribution
            delta_c: Quantum coherence change
            n_epsilon: Non-unitarity measure
            
        Returns:
            θ_integrity metric (0-1 range)
        """
        # Normalize components to [0, 1] range
        entropy_score = min(1.0, delta_s)  # Typical range [0, ln(d)]
        coherence_score = min(1.0, delta_c)  # Range [0, 1]
        non_unity_score = 1.0 - min(1.0, n_epsilon)  # Lower is better
        
        # Weighted combination
        theta_integrity = (0.3 * entropy_score + 
                          0.4 * coherence_score + 
                          0.3 * non_unity_score)
        
        return theta_integrity
    
    # Aliases for backward compatibility
    von_neumann_entropy = von_neumann_entropy
    thermodynamic_entropy = thermodynamic_entropy
    quantum_coherence_l1 = quantum_coherence_l1
    quantum_coherence_relative_entropy = quantum_coherence_relative_entropy
    quantum_coherence = quantum_coherence
    coherence_measures = coherence_measures
    non_unitarity = non_unitarity
    bias_induction = bias_induction