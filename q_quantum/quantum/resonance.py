"""Resonance Module"""
import numpy as np
from scipy.linalg import norm

def resonance_score(state: np.ndarray, target: np.ndarray) -> float:
    """Calculate resonance score."""
    state_norm = state / norm(state) if norm(state) > 0 else state
    target_norm = target / norm(target) if norm(target) > 0 else target
    return abs(np.vdot(state_norm, target_norm))


def noise_decay(sigma: float, e_break: float) -> float:
    """Calculate noise decay factor."""
    effective_sigma = sigma * (1 + e_break)
    return np.exp(-effective_sigma**2 / 2)


def inner_product_resonance(psi: np.ndarray, chi: np.ndarray) -> float:
    """Calculate inner product resonance."""
    psi_norm = psi / norm(psi) if norm(psi) > 0 else psi
    chi_norm = chi / norm(chi) if norm(chi) > 0 else chi
    return float(np.real(np.vdot(psi_norm, chi_norm)))


if __name__ == "__main__":
    psi = np.array([0.8, 0.6])
    chi = np.array([0.7, 0.7])
    
    res_score = resonance_score(psi, chi)
    decay = noise_decay(0.3, 0.5)
    inner_prod = inner_product_resonance(psi, chi)
    
    print(f"Resonance score: {res_score:.6f}")
    print(f"Noise decay: {decay:.6f}")
    print(f"Inner product: {inner_prod:.6f}")
