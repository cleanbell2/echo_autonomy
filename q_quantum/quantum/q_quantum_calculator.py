"""
Q_Quantum Calculator - Core resonance calculation engine
Implements: Q = Ψ(t)·χ(t)·cos(Δθ)·e^(-σ²/2)
"""

import numpy as np
from typing import Optional, Dict
from scipy.linalg import norm

def calculate_q_quantum(
    psi: np.ndarray,
    chi: np.ndarray,
    delta_theta: float,
    sigma: float,
    normalize: bool = True
) -> float:
    """Calculate Q_quantum resonance score."""
    if normalize:
        psi = psi / norm(psi) if norm(psi) > 0 else psi
        chi = chi / norm(chi) if norm(chi) > 0 else chi
    
    inner_product = np.real(np.vdot(psi, chi))
    phase_alignment = np.cos(delta_theta)
    noise_decay = np.exp(-sigma**2 / 2)
    
    q_quantum = inner_product * phase_alignment * noise_decay
    return float(np.clip(q_quantum, 0.0, 1.0))


class QQuantumCalculator:
    """High-level Q_quantum calculator with state tracking."""
    
    def __init__(self, sigma_baseline: float = 0.5):
        self.sigma_baseline = sigma_baseline
        self.history = []
        
    def calculate(self, psi, chi, delta_theta, sigma=None, context=None):
        """Calculate Q_quantum with full context."""
        if sigma is None:
            sigma = self.sigma_baseline
            
        psi_norm = psi / norm(psi) if norm(psi) > 0 else psi
        chi_norm = chi / norm(chi) if norm(chi) > 0 else chi
        
        inner_product = np.real(np.vdot(psi_norm, chi_norm))
        phase_alignment = np.cos(delta_theta)
        noise_decay = np.exp(-sigma**2 / 2)
        
        q_quantum = inner_product * phase_alignment * noise_decay
        q_quantum = float(np.clip(q_quantum, 0.0, 1.0))
        
        result = {
            'q_quantum': q_quantum,
            'components': {
                'inner_product': float(inner_product),
                'phase_alignment': float(phase_alignment),
                'noise_decay': float(noise_decay),
                'sigma': sigma,
                'delta_theta': delta_theta
            },
            'analysis': self._analyze_result(q_quantum, inner_product, phase_alignment)
        }
        
        self.history.append(result)
        return result
    
    def _analyze_result(self, q_quantum, inner_product, phase_alignment):
        """Generate analysis text."""
        if q_quantum > 0.8:
            return "Strong resonance - policy aligns well with anchor"
        elif q_quantum > 0.6:
            return "Moderate resonance - acceptable alignment"
        elif q_quantum > 0.4:
            return "Weak resonance - consider policy adjustment"
        else:
            return "Poor resonance - policy conflicts with anchor"


if __name__ == "__main__":
    psi = np.array([0.8, 0.6])
    chi = np.array([0.7, 0.7])
    delta_theta = np.pi / 6
    sigma = 0.3
    
    q = calculate_q_quantum(psi, chi, delta_theta, sigma)
    print(f"Q_quantum = {q:.6f}")
    
    calc = QQuantumCalculator()
    result = calc.calculate(psi, chi, delta_theta, sigma)
    print(f"Analysis: {result['analysis']}")
    print(f"Components: {result['components']}")