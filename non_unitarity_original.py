"""
Non-unitarity calculation module for ultrawork E_break engine.

Implements non-unitarity measurement for quantum channels and bias induction.
"""

import numpy as np
from typing import Union, Tuple, Optional, List
from scipy.linalg import sqrtm, expm


def non_unitarity(channel: Union[np.ndarray, list], 
                  method: str = 'trace_distance',
                  tolerance: float = 1e-12) -> float:
    """
    Calculate non-unitarity of a quantum channel.
    
    Args:
        channel: Quantum channel matrix (Kraus operators or superoperator)
        method: Calculation method ('trace_distance', 'fidelity', 'norm_difference')
        tolerance: Numerical tolerance for calculations
        
    Returns:
        Non-unitarity measure
        
    Raises:
        ValueError: If channel is invalid or method not supported
    """
    channel_matrix = np.asarray(channel, dtype=complex)
    
    # Input validation
    if channel_matrix.ndim < 2:
        raise ValueError("Channel must be at least 2D matrix")
    
    if channel_matrix.size == 0:
        raise ValueError("Channel matrix cannot be empty")
    
    if np.any(np.isnan(channel_matrix)) or np.any(np.isinf(channel_matrix)):
        raise ValueError("Channel matrix contains invalid values")
    
    if method == 'trace_distance':
        return _non_unitarity_trace_distance(channel_matrix, tolerance)
    elif method == 'fidelity':
        return _non_unitarity_fidelity(channel_matrix, tolerance)
    elif method == 'norm_difference':
        return _non_unitarity_norm_difference(channel_matrix, tolerance)
    else:
        raise ValueError(f"Method '{method}' not supported. Use 'trace_distance', 'fidelity', or 'norm_difference'")


def bias_induction(channel: Union[np.ndarray, list],
                  reference_unitary: Union[np.ndarray, list] = None,
                  method: str = 'operator_norm') -> float:
    """
    Calculate bias induction level of a quantum channel.
    
    Args:
        channel: Quantum channel matrix
        reference_unitary: Reference unitary for comparison (optional)
        method: Bias calculation method ('operator_norm', 'trace_norm', 'fidelity')
        
    Returns:
        Bias induction measure
        
    Raises:
        ValueError: If inputs are invalid
    """
    channel_matrix = np.asarray(channel, dtype=complex)
    
    # Input validation
    if channel_matrix.ndim < 2:
        raise ValueError("Channel must be at least 2D matrix")
    
    if np.any(np.isnan(channel_matrix)) or np.any(np.isinf(channel_matrix)):
        raise ValueError("Channel matrix contains invalid values")
    
    if reference_unitary is None:
        # Use identity as default reference
        dim = channel_matrix.shape[0]
        reference_unitary = np.eye(dim, dtype=complex)
    else:
        reference_unitary = np.asarray(reference_unitary, dtype=complex)
    
    if method == 'operator_norm':
        return _bias_operator_norm(channel_matrix, reference_unitary)
    elif method == 'trace_norm':
        return _bias_trace_norm(channel_matrix, reference_unitary)
    elif method == 'fidelity':
        return _bias_fidelity(channel_matrix, reference_unitary)
    else:
        raise ValueError(f"Method '{method}' not supported")


def channel_completely_positive(channel: Union[np.ndarray, list],
                                tolerance: float = 1e-12) -> bool:
    """
    Check if channel is completely positive.
    
    Args:
        channel: Channel matrix
        tolerance: Numerical tolerance
        
    Returns:
        True if channel is completely positive
    """
    channel_matrix = np.asarray(channel, dtype=complex)
    
    try:
        # Check if channel is trace-preserving and completely positive
        # This is a simplified check - full CP test requires Choi matrix
        return _is_completely_positive(channel_matrix, tolerance)
    except:
        return False


def channel_trace_preserving(channel: Union[np.ndarray, list],
                            tolerance: float = 1e-12) -> bool:
    """
    Check if channel is trace-preserving.
    
    Args:
        channel: Channel matrix
        tolerance: Numerical tolerance
        
    Returns:
        True if channel is trace-preserving
    """
    channel_matrix = np.asarray(channel, dtype=complex)
    
    # For superoperator representation: Tr_out[Φ(ρ)] = Tr[ρ]
    # Simplified check for Kraus operators
    if channel_matrix.ndim == 3:  # Kraus operators
        trace_sum = np.sum([np.conj(K).T @ K for K in channel_matrix], axis=0)
        return np.allclose(trace_sum, np.eye(channel_matrix.shape[1]), atol=tolerance)
    else:  # Superoperator
        # Check if channel preserves trace
        test_state = np.eye(channel_matrix.shape[0]) / channel_matrix.shape[0]
        output = channel_matrix @ test_state
        return np.isclose(np.trace(output), np.trace(test_state), atol=tolerance)


def _non_unitarity_trace_distance(channel: np.ndarray, tolerance: float) -> float:
    """Calculate non-unitarity using trace distance to nearest unitary."""
    # Find nearest unitary (simplified approach)
    nearest_unitary = _find_nearest_unitary(channel)
    
    # Calculate trace distance
    difference = channel - nearest_unitary
    trace_distance = 0.5 * np.linalg.norm(difference, 'nuc')
    
    return float(trace_distance.real)


def _non_unitarity_fidelity(channel: np.ndarray, tolerance: float) -> float:
    """Calculate non-unitarity using fidelity to nearest unitary."""
    nearest_unitary = _find_nearest_unitary(channel)
    
    # Calculate fidelity
    fidelity = _matrix_fidelity(channel, nearest_unitary)
    
    # Non-unitarity = 1 - fidelity
    return 1.0 - fidelity


def _non_unitarity_norm_difference(channel: np.ndarray, tolerance: float) -> float:
    """Calculate non-unitarity using norm difference."""
    # Check if channel is unitary
    is_unitary = _is_unitary(channel, tolerance)
    
    if is_unitary:
        return 0.0
    
    # Calculate deviation from unitarity
    channel_dagger = channel.conj().T
    unitarity_check = channel_dagger @ channel
    
    deviation = np.linalg.norm(unitarity_check - np.eye(channel.shape[0]), 'fro')
    
    return float(deviation.real)


def _bias_operator_norm(channel: np.ndarray, reference: np.ndarray) -> float:
    """Calculate bias using operator norm."""
    difference = channel - reference
    return np.linalg.norm(difference, 2)  # Spectral norm


def _bias_trace_norm(channel: np.ndarray, reference: np.ndarray) -> float:
    """Calculate bias using trace norm."""
    difference = channel - reference
    return np.linalg.norm(difference, 'nuc')  # Nuclear norm


def _bias_fidelity(channel: np.ndarray, reference: np.ndarray) -> float:
    """Calculate bias using fidelity."""
    fidelity = _matrix_fidelity(channel, reference)
    return 1.0 - fidelity


def _find_nearest_unitary(matrix: np.ndarray) -> np.ndarray:
    """Find nearest unitary matrix using polar decomposition."""
    # Simplified approach: use SVD
    U, s, Vh = np.linalg.svd(matrix)
    nearest_unitary = U @ Vh
    
    return nearest_unitary


def _is_unitary(matrix: np.ndarray, tolerance: float) -> bool:
    """Check if matrix is unitary."""
    if matrix.shape[0] != matrix.shape[1]:
        return False
    
    product = matrix.conj().T @ matrix
    return np.allclose(product, np.eye(matrix.shape[0]), atol=tolerance)


def _is_completely_positive(matrix: np.ndarray, tolerance: float) -> bool:
    """Check if channel is completely positive (simplified)."""
    # This is a simplified check - full CP test requires Choi matrix analysis
    try:
        eigenvalues = np.linalg.eigvals(matrix)
        return np.all(eigenvalues >= -tolerance)
    except:
        return False


def _matrix_fidelity(matrix1: np.ndarray, matrix2: np.ndarray) -> float:
    """Calculate fidelity between two matrices."""
    # Simplified fidelity calculation
    overlap = np.trace(matrix1.conj().T @ matrix2)
    norm1 = np.sqrt(np.trace(matrix1.conj().T @ matrix1))
    norm2 = np.sqrt(np.trace(matrix2.conj().T @ matrix2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    fidelity = abs(overlap) / (norm1 * norm2)
    return min(1.0, fidelity.real)


class NonUnitarityAnalyzer:
    """
    Class for analyzing non-unitarity in quantum channels.
    """
    
    def __init__(self, tolerance: float = 1e-12):
        """
        Initialize analyzer.
        
        Args:
            tolerance: Numerical tolerance
        """
        self.tolerance = tolerance
        self.analysis_history = []
    
    def analyze_channel(self, channel: Union[np.ndarray, list],
                        channel_name: str = "unnamed") -> dict:
        """
        Comprehensive analysis of quantum channel.
        
        Args:
            channel: Quantum channel matrix
            channel_name: Name for this channel
            
        Returns:
            Complete analysis results
        """
        channel_matrix = np.asarray(channel, dtype=complex)
        
        analysis = {
            'name': channel_name,
            'non_unitarity_trace_distance': non_unitarity(channel, 'trace_distance', self.tolerance),
            'non_unitarity_fidelity': non_unitarity(channel, 'fidelity', self.tolerance),
            'non_unitarity_norm_difference': non_unitarity(channel, 'norm_difference', self.tolerance),
            'bias_operator_norm': bias_induction(channel, method='operator_norm'),
            'bias_trace_norm': bias_induction(channel, method='trace_norm'),
            'bias_fidelity': bias_induction(channel, method='fidelity'),
            'is_completely_positive': channel_completely_positive(channel, self.tolerance),
            'is_trace_preserving': channel_trace_preserving(channel, self.tolerance),
            'is_unitary': _is_unitary(channel_matrix, self.tolerance)
        }
        
        self.analysis_history.append(analysis)
        return analysis
    
    def compare_channels(self, channels: dict) -> dict:
        """
        Compare multiple quantum channels.
        
        Args:
            channels: Dictionary of channel_name -> channel_matrix
            
        Returns:
            Comparison results
        """
        results = {}
        
        for name, channel in channels.items():
            results[name] = self.analyze_channel(channel, name)
        
        return results
    
    def find_most_biased(self, channels: dict, method: str = 'operator_norm') -> str:
        """
        Find most biased channel among given channels.
        
        Args:
            channels: Dictionary of channel_name -> channel_matrix
            method: Bias calculation method
            
        Returns:
            Name of most biased channel
        """
        max_bias = -1
        most_biased = ""
        
        for name, channel in channels.items():
            bias = bias_induction(channel, method=method)
            if bias > max_bias:
                max_bias = bias
                most_biased = name
        
        return most_biased
    
    def reset_history(self) -> None:
        """Clear analysis history."""
        self.analysis_history.clear()


def create_unitary_channel(theta: float, phi: float = 0.0) -> np.ndarray:
    """
    Create a unitary rotation channel.
    
    Args:
        theta: Rotation angle
        phi: Phase angle
        
    Returns:
        Unitary channel matrix
    """
    return np.array([
        [np.cos(theta), -np.exp(1j * phi) * np.sin(theta)],
        [np.exp(-1j * phi) * np.sin(theta), np.cos(theta)]
    ], dtype=complex)


def create_dephasing_channel(dephasing_rate: float) -> np.ndarray:
    """
    Create a dephasing channel (non-unitary).
    
    Args:
        dephasing_rate: Dephasing rate (0 to 1)
        
    Returns:
        Dephasing channel matrix
    """
    if not 0 <= dephasing_rate <= 1:
        raise ValueError("Dephasing rate must be between 0 and 1")
    
    # Kraus operators for dephasing
    K0 = np.sqrt(1 - dephasing_rate) * np.array([[1, 0], [0, 1]], dtype=complex)
    K1 = np.sqrt(dephasing_rate) * np.array([[1, 0], [0, -1]], dtype=complex)
    
    # Return as superoperator (simplified)
    return np.array([K0, K1])


def create_amplitude_damping_channel(damping_rate: float) -> np.ndarray:
    """
    Create an amplitude damping channel (non-unitary).
    
    Args:
        damping_rate: Damping rate (0 to 1)
        
    Returns:
        Amplitude damping channel matrix
    """
    if not 0 <= damping_rate <= 1:
        raise ValueError("Damping rate must be between 0 and 1")
    
    # Kraus operators for amplitude damping
    K0 = np.array([[1, 0], [0, np.sqrt(1 - damping_rate)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(damping_rate)], [0, 0]], dtype=complex)
    
    return np.array([K0, K1])