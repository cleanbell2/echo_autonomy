"""Q_Quantum Resonance Engine"""

from .anchor import Anchor, EthicalAnchor, AnchorType, AnchorState
from .q_quantum_calculator import calculate_q_quantum, QQuantumCalculator
from .phase_alignment import calculate_phase_difference, alignment_score, drift_detection
from .resonance import resonance_score, noise_decay, inner_product_resonance

__version__ = '0.1.0'

__all__ = [
    # Anchor system
    'Anchor',
    'EthicalAnchor',
    'AnchorType',
    'AnchorState',
    # Q_quantum calculator
    'calculate_q_quantum',
    'QQuantumCalculator',
    # Phase alignment
    'calculate_phase_difference',
    'alignment_score',
    'drift_detection',
    # Resonance
    'resonance_score',
    'noise_decay',
    'inner_product_resonance',
]