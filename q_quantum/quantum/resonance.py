"""
Resonance Engine for Q_Quantum System

Implements advanced resonance calculations including noise decay,
inner product resonance, and comprehensive resonance scoring.
"""

import numpy as np
from scipy import signal, integrate, optimize, linalg
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import warnings


class ResonanceType(Enum):
    """Types of resonance calculations."""
    HARMONIC = "harmonic"
    COHERENT = "coherent"
    ENTANGLED = "entangled"
    DECOHERENT = "decoherent"


@dataclass
class ResonanceState:
    """Represents a resonance state with quantum parameters."""
    amplitude: complex
    frequency: float
    phase: float
    coherence: float
    noise_level: float
    e_break: float = 0.0
    timestamp: float = field(default_factory=lambda: np.random.uniform(0, 100))


@dataclass
class ResonanceMetrics:
    """Metrics for resonance evaluation."""
    resonance_score: float
    coherence_factor: float
    noise_suppression: float
    frequency_matching: float
    phase_alignment: float
    quality_factor: float


class ResonanceEngine:
    """
    Advanced resonance engine for quantum systems.
    
    Calculates resonance between quantum states with noise modeling
    and comprehensive quality metrics.
    """
    
    def __init__(self,
                 resonance_type: ResonanceType = ResonanceType.COHERENT,
                 quality_threshold: float = 0.7,
                 noise_tolerance: float = 0.3):
        """
        Initialize resonance engine.
        
        Args:
            resonance_type: Type of resonance calculation
            quality_threshold: Minimum quality for resonance
            noise_tolerance: Maximum acceptable noise level
        """
        self.resonance_type = resonance_type
        self.quality_threshold = quality_threshold
        self.noise_tolerance = noise_tolerance
        
        # Performance tracking
        self.total_calculations = 0
        self.successful_resonances = 0
        self.quality_history: List[float] = []
        
    def resonance_score(self, 
                        state: Union[ResonanceState, np.ndarray], 
                        target: Union[ResonanceState, np.ndarray]) -> float:
        """
        Calculate comprehensive resonance score between states.
        
        Args:
            state: Current resonance state or vector
            target: Target resonance state or vector
            
        Returns:
            Resonance score (0.0 to 1.0)
        """
        # Handle both ResonanceState and numpy array inputs
        if isinstance(state, np.ndarray) and isinstance(target, np.ndarray):
            # Legacy compatibility mode
            return self._legacy_resonance_score(state, target)
        
        # Full ResonanceState calculation
        if not isinstance(state, ResonanceState) or not isinstance(target, ResonanceState):
            raise TypeError("Both inputs must be ResonanceState or numpy arrays")
        
        # Amplitude resonance (inner product)
        amplitude_resonance = self.inner_product_resonance(
            state.amplitude, target.amplitude
        )
        
        # Frequency matching
        freq_ratio = state.frequency / target.frequency if target.frequency > 0 else 1.0
        freq_resonance = np.exp(-abs(np.log(freq_ratio)) ** 2)
        
        # Phase alignment
        phase_diff = abs(state.phase - target.phase)
        phase_diff = min(phase_diff, 2*np.pi - phase_diff)
        phase_resonance = np.cos(phase_diff / 2) ** 2
        
        # Coherence matching
        coherence_resonance = min(state.coherence, target.coherence)
        
        # Noise penalty
        noise_penalty = np.exp(-(state.noise_level + target.noise_level) / 2)
        
        # Combined resonance based on type
        if self.resonance_type == ResonanceType.COHERENT:
            # All components must be coherent
            resonance = (
                amplitude_resonance * 
                freq_resonance * 
                phase_resonance * 
                coherence_resonance * 
                noise_penalty
            )
            
        elif self.resonance_type == ResonanceType.HARMONIC:
            # Emphasize frequency and phase matching
            resonance = (
                0.3 * amplitude_resonance +
                0.3 * freq_resonance +
                0.3 * phase_resonance +
                0.1 * coherence_resonance
            ) * noise_penalty
            
        elif self.resonance_type == ResonanceType.ENTANGLED:
            # Quantum entanglement-inspired correlation
            resonance = self._calculate_entangled_resonance(state, target)
            
        else:  # DECOHERENT
            # Allow some decoherence
            resonance = (
                amplitude_resonance * 
                freq_resonance * 
                0.5 * phase_resonance +  # Reduced phase importance
                0.5 * coherence_resonance
            ) * noise_penalty
        
        self.total_calculations += 1
        
        if resonance >= self.quality_threshold:
            self.successful_resonances += 1
        
        self.quality_history.append(resonance)
        
        return min(1.0, max(0.0, resonance))
    
    def _legacy_resonance_score(self, state: np.ndarray, target: np.ndarray) -> float:
        """Legacy resonance score for numpy array compatibility."""
        state_norm = state / linalg.norm(state) if linalg.norm(state) > 0 else state
        target_norm = target / linalg.norm(target) if linalg.norm(target) > 0 else target
        return abs(np.vdot(state_norm, target_norm))
    
    def noise_decay(self, sigma: float, e_break: float) -> float:
        """
        Calculate noise decay factor using E_break parameter.
        
        Args:
            sigma: Noise parameter (standard deviation)
            e_break: Energy break parameter
            
        Returns:
            Noise decay factor (0.0 to 1.0)
        """
        # Gaussian noise decay: e^(-σ²/2)
        gaussian_decay = np.exp(-sigma**2 / 2)
        
        # E_break modulation (higher E_break = less decay)
        if e_break > 0:
            e_break_modulation = 1.0 / (1.0 + e_break)
        else:
            e_break_modulation = 1.0
        
        # Combined decay
        total_decay = gaussian_decay * e_break_modulation
        
        # Ensure physical bounds
        return min(1.0, max(0.0, total_decay))
    
    def inner_product_resonance(self, 
                                psi: Union[complex, np.ndarray], 
                                chi: Union[complex, np.ndarray]) -> float:
        """
        Calculate inner product resonance between quantum amplitudes.
        
        Args:
            psi: First quantum amplitude or vector
            chi: Second quantum amplitude or vector
            
        Returns:
            Inner product resonance (0.0 to 1.0)
        """
        # Handle both complex and numpy array inputs
        if isinstance(psi, np.ndarray) and isinstance(chi, np.ndarray):
            # Legacy compatibility mode
            return self._legacy_inner_product_resonance(psi, chi)
        
        # Complex number calculation
        if not isinstance(psi, complex) or not isinstance(chi, complex):
            raise TypeError("Both inputs must be complex numbers or numpy arrays")
        
        # Complex inner product: ⟨ψ|χ⟩
        inner_product = np.conj(psi) * chi
        
        # Normalized resonance (magnitude)
        resonance_magnitude = abs(inner_product)
        
        # Normalize by individual amplitudes
        psi_magnitude = abs(psi)
        chi_magnitude = abs(chi)
        
        if psi_magnitude > 0 and chi_magnitude > 0:
            normalized_resonance = resonance_magnitude / (psi_magnitude * chi_magnitude)
        else:
            normalized_resonance = 0.0
        
        return min(1.0, max(0.0, normalized_resonance))
    
    def _legacy_inner_product_resonance(self, psi: np.ndarray, chi: np.ndarray) -> float:
        """Legacy inner product resonance for numpy array compatibility."""
        psi_norm = psi / linalg.norm(psi) if linalg.norm(psi) > 0 else psi
        chi_norm = chi / linalg.norm(chi) if linalg.norm(chi) > 0 else chi
        return float(np.real(np.vdot(psi_norm, chi_norm)))
    
    def calculate_resonance_spectrum(self, 
                                    state: ResonanceState,
                                    frequency_range: Tuple[float, float],
                                    num_points: int = 100) -> np.ndarray:
        """
        Calculate resonance spectrum across frequency range.
        
        Args:
            state: Resonance state
            frequency_range: (min_freq, max_freq) range
            num_points: Number of frequency points
            
        Returns:
            Array of resonance values across frequencies
        """
        frequencies = np.linspace(frequency_range[0], frequency_range[1], num_points)
        spectrum = np.zeros(num_points)
        
        for i, freq in enumerate(frequencies):
            # Create target state at this frequency
            target = ResonanceState(
                amplitude=state.amplitude,
                frequency=freq,
                phase=state.phase,
                coherence=state.coherence,
                noise_level=state.noise_level,
                e_break=state.e_break
            )
            
            spectrum[i] = self.resonance_score(state, target)
        
        return spectrum
    
    def find_optimal_frequency(self, 
                               state: ResonanceState,
                               frequency_range: Tuple[float, float]) -> Tuple[float, float]:
        """
        Find optimal resonance frequency for given state.
        
        Args:
            state: Resonance state
            frequency_range: Search range for optimal frequency
            
        Returns:
            Tuple of (optimal_frequency, max_resonance)
        """
        def resonance_at_freq(freq):
            target = ResonanceState(
                amplitude=state.amplitude,
                frequency=freq,
                phase=state.phase,
                coherence=state.coherence,
                noise_level=state.noise_level,
                e_break=state.e_break
            )
            return -self.resonance_score(state, target)  # Negative for maximization
        
        # Optimize for maximum resonance
        result = optimize.minimize_scalar(
            resonance_at_freq,
            bounds=frequency_range,
            method='bounded'
        )
        
        optimal_freq = result.x
        max_resonance = -result.fun
        
        return optimal_freq, max_resonance
    
    def calculate_quality_factor(self, 
                                  state: ResonanceState,
                                  target: ResonanceState) -> float:
        """
        Calculate quality factor (Q) for resonance.
        
        Args:
            state: Current resonance state
            target: Target resonance state
            
        Returns:
            Quality factor (higher = better resonance)
        """
        # Get resonance score
        resonance = self.resonance_score(state, target)
        
        # Calculate bandwidth (frequency spread where resonance > 0.5)
        freq_range = (target.frequency * 0.5, target.frequency * 1.5)
        spectrum = self.calculate_resonance_spectrum(state, freq_range, 50)
        
        # Find bandwidth (full width at half maximum)
        half_max = resonance / 2
        above_half = spectrum > half_max
        
        if np.any(above_half):
            bandwidth = np.sum(above_half) * (freq_range[1] - freq_range[0]) / len(spectrum)
        else:
            bandwidth = 1.0  # Default bandwidth
        
        # Quality factor: Q = f_resonance / bandwidth
        if bandwidth > 0:
            quality_factor = target.frequency / bandwidth
        else:
            quality_factor = 1.0
        
        return quality_factor
    
    def _calculate_entangled_resonance(self, 
                                       state: ResonanceState,
                                       target: ResonanceState) -> float:
        """
        Calculate quantum entanglement-inspired resonance.
        
        Args:
            state: Current resonance state
            target: Target resonance state
            
        Returns:
            Entangled resonance score
        """
        # Bell state-inspired correlation
        psi1, psi2 = state.amplitude, target.amplitude
        chi1, chi2 = np.conj(state.amplitude), np.conj(target.amplitude)
        
        # Entangled amplitude calculation
        entangled_amplitude = (psi1 * chi2 + psi2 * chi1) / np.sqrt(2)
        
        # Phase entanglement
        phase_sum = state.phase + target.phase
        phase_entanglement = np.cos(phase_sum / 2) ** 2
        
        # Coherence entanglement
        coherence_entanglement = (state.coherence + target.coherence) / 2
        
        # Combined entangled resonance
        resonance = (
            abs(entangled_amplitude) * 
            phase_entanglement * 
            coherence_entanglement
        )
        
        return min(1.0, resonance)
    
    def get_resonance_statistics(self) -> Dict:
        """Get resonance engine statistics."""
        if self.total_calculations == 0:
            return {"message": "No resonance data available"}
        
        success_rate = self.successful_resonances / self.total_calculations
        avg_quality = np.mean(self.quality_history) if self.quality_history else 0.0
        
        return {
            'total_calculations': self.total_calculations,
            'successful_resonances': self.successful_resonances,
            'success_rate': success_rate,
            'average_quality': avg_quality,
            'quality_std': np.std(self.quality_history) if self.quality_history else 0.0,
            'resonance_type': self.resonance_type.value,
            'quality_threshold': self.quality_threshold
        }


# Convenience functions
def resonance_score(state: Union[ResonanceState, np.ndarray], 
                   target: Union[ResonanceState, np.ndarray]) -> float:
    """Convenience function for resonance score calculation."""
    engine = ResonanceEngine()
    return engine.resonance_score(state, target)


def noise_decay(sigma: float, e_break: float) -> float:
    """Convenience function for noise decay calculation."""
    engine = ResonanceEngine()
    return engine.noise_decay(sigma, e_break)


def inner_product_resonance(psi: Union[complex, np.ndarray], 
                           chi: Union[complex, np.ndarray]) -> float:
    """Convenience function for inner product resonance."""
    engine = ResonanceEngine()
    return engine.inner_product_resonance(psi, chi)


# Example usage
if __name__ == "__main__":
    print("=== Q_Quantum Resonance Engine Demo ===")
    
    # Example 1: Legacy numpy array mode (backward compatibility)
    print("\n1. Legacy Mode (numpy arrays):")
    psi = np.array([0.8, 0.6])
    chi = np.array([0.7, 0.7])
    
    res_score = resonance_score(psi, chi)
    decay = noise_decay(0.3, 0.5)
    inner_prod = inner_product_resonance(psi, chi)
    
    print(f"   Resonance score: {res_score:.6f}")
    print(f"   Noise decay: {decay:.6f}")
    print(f"   Inner product: {inner_prod:.6f}")
    
    # Example 2: Full ResonanceState mode
    print("\n2. Full ResonanceState Mode:")
    engine = ResonanceEngine(resonance_type=ResonanceType.COHERENT)
    
    current_state = ResonanceState(
        amplitude=complex(0.8, 0.3),
        frequency=1.0,
        phase=np.pi/4,
        coherence=0.9,
        noise_level=0.1,
        e_break=0.5
    )
    
    target_state = ResonanceState(
        amplitude=complex(0.7, 0.2),
        frequency=1.1,
        phase=np.pi/3,
        coherence=0.95,
        noise_level=0.05,
        e_break=0.3
    )
    
    score = resonance_score(current_state, target_state)
    print(f"   Resonance score: {score:.4f}")
    
    # Calculate resonance spectrum
    print(f"\n3. Resonance Spectrum:")
    freq_range = (0.5, 2.0)
    spectrum = engine.calculate_resonance_spectrum(current_state, freq_range, 10)
    
    print("   Frequency (Hz) -> Resonance")
    for i, freq in enumerate(np.linspace(freq_range[0], freq_range[1], 10)):
        print(f"   {freq:.2f} -> {spectrum[i]:.4f}")
    
    # Find optimal frequency
    optimal_freq, max_res = engine.find_optimal_frequency(current_state, freq_range)
    print(f"\n4. Optimal frequency: {optimal_freq:.4f} Hz")
    print(f"   Maximum resonance: {max_res:.4f}")
    
    # Test different resonance types
    print(f"\n5. Resonance Type Comparison:")
    for res_type in [ResonanceType.COHERENT, ResonanceType.HARMONIC, ResonanceType.ENTANGLED]:
        engine_type = ResonanceEngine(resonance_type=res_type)
        score_type = engine_type.resonance_score(current_state, target_state)
        print(f"   {res_type.value}: {score_type:.4f}")
    
    # Engine statistics
    print(f"\n6. Engine statistics: {engine.get_resonance_statistics()}")