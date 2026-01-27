import numpy as np
from scipy.linalg import logm, expm
from scipy.sparse import issparse
from typing import Union, Optional, Tuple
import warnings


class EBreachEngine:
    """
    Ultrawork E_break calculation engine for quantum thermodynamic analysis.
    
    Calculates von Neumann entropy, thermodynamic entropy, and quantum coherence.
    """
    
    def __init__(self, tolerance: float = 1e-12):
        """
        Initialize the E_break calculation engine.
        
        Args:
            tolerance: Numerical tolerance for eigenvalue calculations
        """
        self.tolerance = tolerance
        self.kb = 1.380649e-23  # Boltzmann constant in J/K
        
    def von_neumann_entropy(self, rho: Union[np.ndarray, list]) -> float:
        """
        Calculate von Neumann entropy: S = -Tr(ρ ln ρ)
        
        Args:
            rho: Density matrix (2D numpy array or list)
            
        Returns:
            von Neumann entropy in natural units
        """
        rho = np.asarray(rho, dtype=complex)
        
        # Validate density matrix
        self._validate_density_matrix(rho)
        
        # Calculate eigenvalues
        eigenvalues = np.linalg.eigvalsh(rho)
        
        # Filter out very small eigenvalues to avoid numerical issues
        eigenvalues = eigenvalues[eigenvalues > self.tolerance]
        
        # Calculate S = -∑ λ_i ln(λ_i)
        entropy = -np.sum(eigenvalues * np.log(eigenvalues))
        
        return float(entropy.real)
    
    def thermodynamic_entropy(self, rho: Union[np.ndarray, list], 
                            temperature: float) -> float:
        """
        Calculate thermodynamic entropy: S_thermo = k_B * S_vN
        
        Args:
            rho: Density matrix
            temperature: Temperature in Kelvin
            
        Returns:
            Thermodynamic entropy in J/K
        """
        if temperature <= 0:
            raise ValueError("Temperature must be positive")
            
        vn_entropy = self.von_neumann_entropy(rho)
        
        return self.kb * vn_entropy
    
    def quantum_coherence_l1_norm(self, rho: Union[np.ndarray, list]) -> float:
        """
        Calculate quantum coherence using l1-norm: C_l1 = ∑_{i≠j} |ρ_ij|
        
        Args:
            rho: Density matrix
            
        Returns:
            Quantum coherence measure
        """
        rho = np.asarray(rho, dtype=complex)
        self._validate_density_matrix(rho)
        
        # Sum of absolute values of off-diagonal elements
        coherence = np.sum(np.abs(rho)) - np.sum(np.abs(np.diag(rho)))
        
        return float(coherence.real)
    
    def quantum_coherence_relative_entropy(self, rho: Union[np.ndarray, list]) -> float:
        """
        Calculate quantum coherence using relative entropy: 
        C_re = S(ρ_diag) - S(ρ)
        
        Args:
            rho: Density matrix
            
        Returns:
            Quantum coherence measure
        """
        rho = np.asarray(rho, dtype=complex)
        self._validate_density_matrix(rho)
        
        # Create diagonal version of density matrix
        rho_diag = np.diag(np.diag(rho))
        
        # Calculate entropies
        s_rho = self.von_neumann_entropy(rho)
        s_rho_diag = self.von_neumann_entropy(rho_diag)
        
        return s_rho_diag - s_rho
    
    def e_break(self, rho: Union[np.ndarray, list], 
               temperature: float, 
               coherence_weight: float = 0.5) -> dict:
        """
        Calculate comprehensive E_break metrics.
        
        Args:
            rho: Density matrix
            temperature: Temperature in Kelvin
            coherence_weight: Weight for coherence in E_break calculation (0-1)
            
        Returns:
            Dictionary containing all calculated metrics
        """
        if not 0 <= coherence_weight <= 1:
            raise ValueError("coherence_weight must be between 0 and 1")
            
        # Calculate all metrics
        vn_entropy = self.von_neumann_entropy(rho)
        thermo_entropy = self.thermodynamic_entropy(rho, temperature)
        coherence_l1 = self.quantum_coherence_l1_norm(rho)
        coherence_re = self.quantum_coherence_relative_entropy(rho)
        
        # Combined E_break metric
        e_break_value = (1 - coherence_weight) * vn_entropy + coherence_weight * coherence_re
        
        return {
            'von_neumann_entropy': vn_entropy,
            'thermodynamic_entropy': thermo_entropy,
            'coherence_l1_norm': coherence_l1,
            'coherence_relative_entropy': coherence_re,
            'e_break': e_break_value,
            'temperature': temperature
        }
    
    def _validate_density_matrix(self, rho: np.ndarray) -> None:
        """Validate that the input is a proper density matrix."""
        # Check if matrix is square
        if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
            raise ValueError("Density matrix must be square")
            
        # Check if Hermitian (ρ = ρ†)
        if not np.allclose(rho, rho.conj().T, atol=self.tolerance):
            raise ValueError("Density matrix must be Hermitian")
            
        # Check if trace = 1
        trace = np.trace(rho)
        if not np.isclose(trace.real, 1.0, atol=self.tolerance):
            raise ValueError(f"Density matrix trace must be 1, got {trace.real}")
            
        # Check if positive semidefinite (all eigenvalues >= 0)
        eigenvalues = np.linalg.eigvalsh(rho)
        if np.any(eigenvalues < -self.tolerance):
            raise ValueError("Density matrix must be positive semidefinite")
    
    def create_thermal_state(self, hamiltonian: Union[np.ndarray, list], 
                           temperature: float) -> np.ndarray:
        """
        Create thermal Gibbs state: ρ = exp(-H/k_B T) / Tr[exp(-H/k_B T)]
        
        Args:
            hamiltonian: Hamiltonian matrix
            temperature: Temperature in Kelvin
            
        Returns:
            Thermal density matrix
        """
        if temperature <= 0:
            raise ValueError("Temperature must be positive")
            
        H = np.asarray(hamiltonian, dtype=complex)
        
        # Diagonalize the Hamiltonian for numerical stability
        eigenvalues, eigenvectors = np.linalg.eigh(H)
        
        # Calculate exp(-βE_i) for each eigenvalue
        beta = 1.0 / (self.kb * temperature)
        
        # Handle potential overflow by shifting eigenvalues
        shifted_eigenvalues = eigenvalues - np.min(eigenvalues)
        exp_neg_beta_e = np.exp(-beta * shifted_eigenvalues)
        
        # Create thermal state in eigenbasis
        rho_thermal_eigenbasis = np.diag(exp_neg_beta_e / np.sum(exp_neg_beta_e))
        
        # Transform back to original basis
        rho_thermal = eigenvectors @ rho_thermal_eigenbasis @ eigenvectors.conj().T
        
        return rho_thermal
    
    def create_pure_state(self, state_vector: Union[np.ndarray, list]) -> np.ndarray:
        """
        Create pure state density matrix: ρ = |ψ⟩⟨ψ|
        
        Args:
            state_vector: Normalized state vector
            
        Returns:
            Pure state density matrix
        """
        psi = np.asarray(state_vector, dtype=complex)
        
        # Normalize the state vector
        psi = psi / np.linalg.norm(psi)
        
        # Create density matrix
        rho = np.outer(psi, psi.conj())
        
        return rho
    
    def create_mixed_state(self, probabilities: list, 
                          states: list) -> np.ndarray:
        """
        Create mixed state: ρ = ∑ p_i |ψ_i⟩⟨ψ_i|
        
        Args:
            probabilities: List of probabilities (must sum to 1)
            states: List of state vectors
            
        Returns:
            Mixed state density matrix
        """
        if len(probabilities) != len(states):
            raise ValueError("Number of probabilities must match number of states")
            
        if not np.isclose(np.sum(probabilities), 1.0, atol=self.tolerance):
            raise ValueError("Probabilities must sum to 1")
            
        if not states:
            raise ValueError("States list cannot be empty")
            
        # Validate first state and get dimension
        first_state = np.asarray(states[0], dtype=complex)
        dim = len(first_state)
        
        # Validate all states have same dimension
        for i, state in enumerate(states):
            state = np.asarray(state, dtype=complex)
            if len(state) != dim:
                raise ValueError(f"State {i} has dimension {len(state)}, expected {dim}")
            
        rho = np.zeros((dim, dim), dtype=complex)
        
        for p, state in zip(probabilities, states):
            state = np.asarray(state, dtype=complex)
            state = state / np.linalg.norm(state)  # Normalize
            rho += p * np.outer(state, state.conj())
            
        return rho