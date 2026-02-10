"""Phase Alignment Module"""
import numpy as np
from typing import Tuple, Optional, List

def calculate_phase_difference(state: np.ndarray, anchor: np.ndarray) -> float:
    """Calculate phase difference between state and anchor."""
    state_complex = state if np.iscomplexobj(state) else state.astype(complex)
    anchor_complex = anchor if np.iscomplexobj(anchor) else anchor.astype(complex)
    
    state_angle = np.angle(np.sum(state_complex))
    anchor_angle = np.angle(np.sum(anchor_complex))
    
    diff = abs(state_angle - anchor_angle)
    return min(diff, 2*np.pi - diff)


def alignment_score(state: np.ndarray, target: np.ndarray) -> float:
    """Calculate alignment score (0 to 1)."""
    phase_diff = calculate_phase_difference(state, target)
    return np.cos(phase_diff / 2) ** 2


def drift_detection(history: List, threshold: float = 0.2) -> Tuple[bool, float]:
    """Detect phase drift in history."""
    if len(history) < 2:
        return False, 0.0
    
    phases = [calculate_phase_difference(h['state'], h['anchor']) for h in history]
    drift = abs(phases[-1] - phases[0])
    return drift > threshold, drift


if __name__ == "__main__":
    state = np.array([0.8, 0.6])
    target = np.array([0.7, 0.7])
    
    phase_diff = calculate_phase_difference(state, target)
    score = alignment_score(state, target)
    
    print(f"Phase difference: {phase_diff:.6f} rad")
    print(f"Alignment score: {score:.6f}")