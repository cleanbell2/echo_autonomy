"""
Quantum coherence calculation module for ultrawork E_break engine.

Implements l1-norm and relative entropy based coherence measures.
"""

import numpy as np
from typing import Union, Tuple, Optional
from scipy.linalg import logm


def quantum_coherence_l1(coherence_matrix: Union[np.ndarray, list]) -> float:
    """
    Calculate quantum coherence using l1-norm: C_l1 = ∑_{i≠j} |ρ_ij|
    
    Args:
        coherence_matrix: Density matrix or coherence matrix
        
    Returns:
        l1-norm coherence measure
        
    Raises:
        ValueError: If matrix is invalid
        TypeError: If input type is not supported
    """
    rho = np.asarray(coherence_matrix, dtype=complex)
    
    # Input validation
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("Coherence matrix must be square")
    
    if rho.size == 0:
        raise ValueError("Coherence matrix cannot be empty")
    
    if np.any(np.isnan(rho)) or np.any(np.isinf(rho)):
        raise ValueError("Coherence matrix contains invalid values")
    
    # Calculate l1-norm coherence: sum of absolute values of off-diagonal elements
    diagonal_elements = np.abs(np.diag(rho))
    total_sum = np.sum(np.abs(rho))
    
    coherence = total_sum - np.sum(diagonal_elements)
    
    return float(coherence.real)


def quantum_coherence_relative_entropy(coherence_matrix: Union[np.ndarray, list], 
                                      tolerance: float = 1e-12) -> float:
    """
    Calculate quantum coherence using relative entropy: C_re = S(ρ_diag) - S(ρ)
    
    Args:
        coherence_matrix: Density matrix or coherence matrix
        tolerance: Numerical tolerance for eigenvalue calculations
        
    Returns:
        Relative entropy coherence measure
        
    Raises:
        ValueError: If matrix is invalid
    """
    rho = np.asarray(coherence_matrix, dtype=complex)
    
    # Input validation
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("Coherence matrix must be square")
    
    if rho.size == 0:
        raise ValueError("Coherence matrix cannot be empty")
    
    if np.any(np.isnan(rho)) or np.any(np.isinf(rho)):
        raise ValueError("Coherence matrix contains invalid values")
    
    # Create diagonal version of the matrix
    rho_diag = np.diag(np.diag(rho))
    
    # Calculate von Neumann entropy
    s_rho = _von_neumann_entropy(rho, tolerance)
    s_rho_diag = _von_neumann_entropy(rho_diag, tolerance)
    
    coherence = s_rho_diag - s_rho
    
    # Ensure non-negative result (due to numerical errors)
    return max(0.0, float(coherence.real))


def quantum_coherence(coherence_matrix: Union[np.ndarray, list], 
                      method: str = 'l1',
                      tolerance: float = 1e-12) -> float:
    """
    Calculate quantum coherence using specified method.
    
    Args:
        coherence_matrix: Density matrix or coherence matrix
        method: Coherence calculation method ('l1' or 'relative_entropy')
        tolerance: Numerical tolerance for eigenvalue calculations
        
    Returns:
        Coherence measure
        
    Raises:
        ValueError: If method is not supported or matrix is invalid
    """
    if method not in ['l1', 'relative_entropy']:
        raise ValueError("Method must be 'l1' or 'relative_entropy'")
    
    if method == 'l1':
        return quantum_coherence_l1(coherence_matrix)
    else:
        return quantum_coherence_relative_entropy(coherence_matrix, tolerance)


def coherence_measures(coherence_matrix: Union[np.ndarray, list],
                        tolerance: float = 1e-12) -> dict:
    """
    Calculate both coherence measures and return comprehensive results.
    
    Args:
        coherence_matrix: Density matrix or coherence matrix
        tolerance: Numerical tolerance for eigenvalue calculations
        
    Returns:
        Dictionary containing both coherence measures
    """
    return {
        'l1_norm': quantum_coherence_l1(coherence_matrix),
        'relative_entropy': quantum_coherence_relative_entropy(coherence_matrix, tolerance)
    }


def _von_neumann_entropy(matrix: np.ndarray, tolerance: float = 1e-12) -> float:
    """
    Calculate von Neumann entropy: S = -Tr(ρ ln ρ)
    
    Args:
        matrix: Input matrix
        tolerance: Numerical tolerance for eigenvalue calculations
        
    Returns:
        von Neumann entropy
    """
    # Calculate eigenvalues (using eigh for Hermitian matrices)
    eigenvalues = np.linalg.eigvalsh(matrix)
    
    # Filter out very small eigenvalues to avoid numerical issues
    eigenvalues = eigenvalues[eigenvalues > tolerance]
    
    # Calculate S = -∑ λ_i ln(λ_i)
    entropy = -np.sum(eigenvalues * np.log(eigenvalues))
    
    return float(entropy.real)


class CoherenceAnalyzer:
    """
    Class for analyzing quantum coherence in different states and systems.
    """
    
    def __init__(self, tolerance: float = 1e-12):
        """
        Initialize coherence analyzer.
        
        Args:
            tolerance: Numerical tolerance for calculations
        """
        self.tolerance = tolerance
        self.analysis_history = []
    
    def analyze_state(self, state_matrix: Union[np.ndarray, list],
                       state_name: str = "unnamed") -> dict:
        """
        Analyze coherence of a quantum state.
        
        Args:
            state_matrix: Density matrix
            state_name: Name for this state
            
        Returns:
            Comprehensive coherence analysis
        """
        analysis = {
            'name': state_name,
            'l1_norm': quantum_coherence_l1(state_matrix),
            'relative_entropy': quantum_coherence_relative_entropy(state_matrix, self.tolerance)
        }
        
        # Additional metrics
        rho = np.asarray(state_matrix, dtype=complex)
        analysis['purity'] = float(np.trace(rho @ rho).real)
        analysis['trace'] = float(np.trace(rho).real)
        
        self.analysis_history.append(analysis)
        return analysis
    
    def compare_states(self, matrices: dict) -> dict:
        """
        Compare coherence of multiple states.
        
        Args:
            matrices: Dictionary of state_name -> matrix
            
        Returns:
            Comparison results
        """
        results = {}
        
        for name, matrix in matrices.items():
            results[name] = self.analyze_state(matrix, name)
        
        return results
    
    def coherence_spectrum(self, matrices: dict) -> dict:
        """
        Calculate coherence spectrum across multiple states.
        
        Args:
            matrices: Dictionary of state_name -> matrix
            
        Returns:
            Coherence spectrum data
        """
        spectrum = {
            'states': [],
            'l1_norm_values': [],
            'relative_entropy_values': [],
            'purity_values': []
        }
        
        for name, matrix in matrices.items():
            analysis = self.analyze_state(matrix, name)
            
            spectrum['states'].append(name)
            spectrum['l1_norm_values'].append(analysis['l1_norm'])
            spectrum['relative_entropy_values'].append(analysis['relative_entropy'])
            spectrum['purity_values'].append(analysis['purity'])
        
        return spectrum
    
    def reset_history(self) -> None:
        """Clear analysis history."""
        self.analysis_history.clear()
    
    def get_most_coherent(self, matrices: dict, method: str = 'l1') -> str:
        """
        Find most coherent state among given matrices.
        
        Args:
            matrices: Dictionary of state_name -> matrix
            method: Coherence measure to use ('l1' or 'relative_entropy')
            
        Returns:
            Name of most coherent state
        """
        if method not in ['l1', 'relative_entropy']:
            raise ValueError("Method must be 'l1' or 'relative_entropy'")
        
        max_coherence = -1
        most_coherent_state = ""
        
        for name, matrix in matrices.items():
            coherence = quantum_coherence(matrix, method)
            if coherence > max_coherence:
                max_coherence = coherence
                most_coherent_state = name
        
        return most_coherent_state


def create_pure_state_coherence_matrix(superposition_amplitude: complex,
                                      basis_dim: int = 2) -> np.ndarray:
    """
    Create a coherence matrix for a pure superposition state.
    
    Args:
        superposition_amplitude: Amplitude for |0⟩ state
        basis_dim: Dimension of the Hilbert space
        
    Returns:
        Coherence matrix
    """
    if basis_dim < 2:
        raise ValueError("Basis dimension must be at least 2")
    
    if abs(superposition_amplitude) > 1:
        raise ValueError("Amplitude magnitude cannot exceed 1")
    
    # Create normalized superposition: |ψ⟩ = α|0⟩ + β|1⟩
    alpha = superposition_amplitude
    beta = np.sqrt(1 - abs(alpha)**2)
    
    if basis_dim == 2:
        psi = np.array([alpha, beta], dtype=complex)
    else:
        # Extend to higher dimensions
        psi = np.zeros(basis_dim, dtype=complex)
        psi[0] = alpha
        psi[1] = beta
        # Rest are zeros
    
    return np.outer(psi, psi.conj())


def create_mixed_state_coherence_matrix(pure_state_weight: float,
                                       coherence_magnitude: float = 1.0,
                                       dim: int = 2) -> np.ndarray:
    """
    Create a mixed state with specified coherence properties.
    
    Args:
        pure_state_weight: Weight for coherent component (0 to 1)
        coherence_magnitude: Coherence strength (0 to 1)
        dim: Matrix dimension
        
    Returns:
        Mixed state coherence matrix
    """
    if not 0 <= pure_state_weight <= 1:
        raise ValueError("pure_state_weight must be between 0 and 1")
    
    if not 0 <= coherence_magnitude <= 1:
        raise ValueError("coherence_magnitude must be between 0 and 1")
    
    # Coherent component (pure superposition)
    coherent_matrix = create_pure_state_coherence_matrix(1/np.sqrt(2), dim)
    coherent_matrix *= coherence_magnitude
    
    # Incoherent component (maximally mixed)
    incoherent_matrix = np.eye(dim) / dim
    
    # Mix them
    return pure_state_weight * coherent_matrix + (1 - pure_state_weight) * incoherent_matrix