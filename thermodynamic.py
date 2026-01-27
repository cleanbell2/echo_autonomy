"""
Thermodynamic entropy calculation module for ultrawork E_break engine.

Implements the thermodynamic entropy component: γ·TΣ = γ·(W - ΔF)
"""

import numpy as np
from typing import Union, Optional


def thermodynamic_entropy(work: Union[float, np.ndarray], 
                          free_energy_change: Union[float, np.ndarray], 
                          gamma: float = 1.0) -> Union[float, np.ndarray]:
    """
    Calculate thermodynamic entropy: γ·TΣ = γ·(W - ΔF)
    
    Args:
        work: Work done (W) - can be scalar or array
        free_energy_change: Change in free energy (ΔF) - can be scalar or array
        gamma: Thermodynamic coupling coefficient (default: 1.0)
        
    Returns:
        Thermodynamic entropy γ·TΣ
        
    Raises:
        ValueError: If inputs are invalid
        TypeError: If input types are not supported
    """
    # Input validation
    if not isinstance(gamma, (int, float)):
        raise TypeError("gamma must be a numeric value")
    
    if gamma < 0:
        raise ValueError("gamma must be non-negative")
    
    # Convert to numpy arrays for consistent handling
    work_array = np.asarray(work, dtype=float)
    free_energy_array = np.asarray(free_energy_change, dtype=float)
    
    # Check array compatibility
    if work_array.shape != free_energy_array.shape:
        raise ValueError(f"Work and free_energy_change must have same shape. "
                        f"Got {work_array.shape} and {free_energy_array.shape}")
    
    # Check for NaN or infinite values
    if np.any(np.isnan(work_array)) or np.any(np.isnan(free_energy_array)):
        raise ValueError("Inputs contain NaN values")
    
    if np.any(np.isinf(work_array)) or np.any(np.isinf(free_energy_array)):
        raise ValueError("Inputs contain infinite values")
    
    # Calculate thermodynamic entropy: γ·TΣ = γ·(W - ΔF)
    entropy = gamma * (work_array - free_energy_array)
    
    # Return scalar if input was scalar
    if np.isscalar(work) and np.isscalar(free_energy_change):
        return float(entropy)
    
    return entropy


def thermodynamic_entropy_from_temperature(temperature: float,
                                          entropy_change: float,
                                          gamma: float = 1.0) -> float:
    """
    Calculate thermodynamic entropy from temperature and entropy change.
    
    Alternative formulation: γ·TΣ = γ·T·ΔS
    
    Args:
        temperature: Temperature in Kelvin
        entropy_change: Change in entropy (ΔS)
        gamma: Thermodynamic coupling coefficient (default: 1.0)
        
    Returns:
        Thermodynamic entropy γ·TΣ
        
    Raises:
        ValueError: If temperature is not positive
    """
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    
    if not isinstance(gamma, (int, float)):
        raise TypeError("gamma must be a numeric value")
    
    if gamma < 0:
        raise ValueError("gamma must be non-negative")
    
    return gamma * temperature * entropy_change


def validate_thermodynamic_parameters(work: float, 
                                    free_energy_change: float,
                                    gamma: float = 1.0) -> bool:
    """
    Validate thermodynamic parameters for physical consistency.
    
    Args:
        work: Work done
        free_energy_change: Change in free energy
        gamma: Thermodynamic coupling coefficient
        
    Returns:
        True if parameters are physically valid
        
    Raises:
        ValueError: If parameters are invalid
    """
    # Check numeric types
    if not all(isinstance(x, (int, float)) for x in [work, free_energy_change, gamma]):
        raise TypeError("All parameters must be numeric")
    
    # Check gamma
    if gamma < 0:
        raise ValueError("gamma must be non-negative")
    
    # Check for NaN or infinite values
    if any(np.isnan([work, free_energy_change, gamma])):
        raise ValueError("Parameters contain NaN values")
    
    if any(np.isinf([work, free_energy_change, gamma])):
        raise ValueError("Parameters contain infinite values")
    
    # Physical consistency check (optional - can be relaxed for theoretical work)
    # In many systems, work should be >= -ΔF (second law)
    if work + free_energy_change < -1e-12:  # Allow small numerical tolerance
        import warnings
        warnings.warn("Work + ΔF is negative, which may violate the second law of thermodynamics")
    
    return True


class ThermodynamicSystem:
    """
    Class for modeling thermodynamic systems with entropy calculations.
    """
    
    def __init__(self, gamma: float = 1.0):
        """
        Initialize thermodynamic system.
        
        Args:
            gamma: Thermodynamic coupling coefficient
        """
        self.gamma = gamma
        self.work_history = []
        self.free_energy_history = []
    
    def add_process(self, work: float, free_energy_change: float) -> float:
        """
        Add a thermodynamic process and calculate entropy.
        
        Args:
            work: Work done in the process
            free_energy_change: Change in free energy
            
        Returns:
            Thermodynamic entropy for this process
        """
        if self.gamma < 0:
            raise ValueError("gamma must be non-negative")  # 메시지 오타 없이!

        validate_thermodynamic_parameters(work, free_energy_change, self.gamma)
        entropy = thermodynamic_entropy(work, free_energy_change, self.gamma)
        
        self.work_history.append(work)
        self.free_energy_history.append(free_energy_change)
        
        return entropy
    
    def total_entropy(self) -> float:
        """
        Calculate total entropy for all processes.
        
        Returns:
            Total thermodynamic entropy
        """
        if not self.work_history:
            return 0.0
        
        total_work = np.sum(self.work_history)
        total_free_energy = np.sum(self.free_energy_history)
        
        return thermodynamic_entropy(total_work, total_free_energy, self.gamma)
    
    def reset(self) -> None:
        """Reset the system history."""
        self.work_history.clear()
        self.free_energy_history.clear()
    
    def __str__(self) -> str:
        """String representation of the system."""
        return f"ThermodynamicSystem(gamma={self.gamma}, processes={len(self.work_history)})"