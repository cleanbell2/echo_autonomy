"""
Quantum Uncertainty Calculator
Measures system uncertainty/instability (0..1)

Components:
1. Entropy (Mixedness) - 섞일수록 높음
2. Purity (1-P) - 순수할수록 낮음  
3. Drift (Temporal) - 변화 클수록 높음

Q_uncertainty = clamp01(w_S·Ŝ + w_P·(1-P) + w_D·D)
"""

import numpy as np
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from scipy.stats import entropy


def clamp01(x: float) -> float:
    """Clamp value to [0, 1]."""
    return max(0.0, min(1.0, float(x)))


@dataclass(frozen=True)
class UncertaintyResult:
    """Result of uncertainty calculation."""
    value: float              # Total uncertainty (0..1)
    entropy_normalized: float  # Ŝ component
    impurity: float           # 1-P component
    drift: float              # D component
    explanation: str          # Why uncertainty is high/low
    components: Dict[str, float]


def shannon_entropy_normalized(p: np.ndarray) -> float:
    """
    Calculate normalized Shannon entropy (0..1).
    
    Args:
        p: Probability distribution (sums to 1)
    
    Returns:
        Normalized entropy Ŝ = H(p) / log(d)
    """
    p = np.array(p, dtype=float)
    # 안전장치: 합이 0이거나 음수가 있으면 처리
    if np.sum(p) <= 0:
        return 1.0 # 최대 불확실성으로 간주
        
    p = p / np.sum(p)  # Normalize
    
    d = len(p)
    if d <= 1:
        return 0.0
    
    h = entropy(p, base=2)  # Shannon entropy
    h_max = np.log2(d)      # Maximum entropy
    
    return clamp01(h / h_max) if h_max > 0 else 0.0


def purity_measure(rho: np.ndarray) -> float:
    """
    Calculate purity P = Tr(ρ²).
    
    Args:
        rho: Density matrix or probability vector
    
    Returns:
        Purity (0..1), where 1 = pure, 0 = maximally mixed
    """
    rho = np.array(rho, dtype=float)
    
    # If 1D array, treat as diagonal of density matrix
    if rho.ndim == 1:
        # P = Σ p_i²
        if np.sum(rho) > 0:
            rho = rho / np.sum(rho)  # Normalize
        purity = np.sum(rho ** 2)
    else:
        # P = Tr(ρ²)
        # 2D 행렬도 Trace가 1이 되도록 정규화 필요할 수 있음
        tr = np.trace(rho)
        if tr > 0:
            rho = rho / tr
        rho_squared = rho @ rho
        purity = np.real(np.trace(rho_squared))
    
    return clamp01(purity)


def jsd_distance(p: np.ndarray, q: np.ndarray) -> float:
    """
    Jensen-Shannon divergence (square root = distance).
    
    Args:
        p, q: Probability distributions
    
    Returns:
        JSD distance (0..1)
    """
    p = np.array(p, dtype=float)
    q = np.array(q, dtype=float)
    
    # Normalize & Safety check
    sum_p = np.sum(p)
    sum_q = np.sum(q)
    
    if sum_p > 0: p = p / sum_p
    else: p = np.ones_like(p) / len(p) # Fallback to uniform
        
    if sum_q > 0: q = q / sum_q
    else: q = np.ones_like(q) / len(q)
    
    # Ensure same length
    if len(p) != len(q):
        max_len = max(len(p), len(q))
        p_pad = np.zeros(max_len)
        q_pad = np.zeros(max_len)
        p_pad[:len(p)] = p
        q_pad[:len(q)] = q
        p, q = p_pad, q_pad
    
    # JSD calculation
    m = 0.5 * (p + q)
    jsd = 0.5 * (entropy(p, m, base=2) + entropy(q, m, base=2))
    
    # Distance (square root)
    jsd_dist = np.sqrt(max(0.0, jsd)) # max(0, ..) for numerical stability
    
    return clamp01(jsd_dist)


def calculate_uncertainty(
    state: np.ndarray,
    prev_state: Optional[np.ndarray] = None,
    weights: Optional[Tuple[float, float, float]] = None
) -> UncertaintyResult:
    """
    Calculate quantum uncertainty (0..1).
    
    Args:
        state: Current state (density matrix or probability vector)
        prev_state: Previous state for drift calculation
        weights: (w_S, w_P, w_D) for entropy, purity, drift
                 Default: (0.45, 0.35, 0.20)
    
    Returns:
        UncertaintyResult with value and explanation
    """
    if weights is None:
        weights = (0.45, 0.35, 0.20)
    
    w_s, w_p, w_d = weights
    
    state = np.array(state, dtype=float)
    
    # 1. Entropy (Mixedness)
    if state.ndim == 1:
        # Probability vector
        entropy_n = shannon_entropy_normalized(state)
    else:
        # Density matrix - use diagonal as probability for entropy approximation
        # (Von Neumann entropy is better but heavier, sticking to Shannon on diag for now)
        probs = np.real(np.diag(state))
        entropy_n = shannon_entropy_normalized(probs)
    
    # 2. Impurity (1 - Purity)
    purity = purity_measure(state)
    impurity = 1.0 - purity
    
    # 3. Drift (Temporal instability)
    if prev_state is not None:
        prev_state = np.array(prev_state, dtype=float)
        
        if state.ndim == 1 and prev_state.ndim == 1:
            drift = jsd_distance(state, prev_state)
        else:
            # Use diagonal elements for drift check if matrix
            p_curr = np.real(np.diag(state)) if state.ndim == 2 else state
            p_prev = np.real(np.diag(prev_state)) if prev_state.ndim == 2 else prev_state
            drift = jsd_distance(p_curr, p_prev)
    else:
        drift = 0.0
    
    # Total uncertainty
    uncertainty = clamp01(
        w_s * entropy_n + 
        w_p * impurity + 
        w_d * drift
    )
    
    # Generate explanation
    components_dict = {
        'entropy': entropy_n,
        'purity': purity,
        'impurity': impurity,
        'drift': drift
    }
    
    explanation = _generate_explanation(
        uncertainty, entropy_n, impurity, drift
    )
    
    return UncertaintyResult(
        value=uncertainty,
        entropy_normalized=entropy_n,
        impurity=impurity,
        drift=drift,
        explanation=explanation,
        components=components_dict
    )


def _generate_explanation(
    uncertainty: float,
    entropy_n: float,
    impurity: float, 
    drift: float
) -> str:
    """Generate human-readable explanation."""
    
    # Find dominant component
    components = [
        (entropy_n, "entropy/mixedness"),
        (impurity, "impurity/mixed state"),
        (drift, "temporal drift/instability")
    ]
    
    dominant_value, dominant_name = max(components, key=lambda x: x[0])
    
    if uncertainty > 0.7:
        level = "High"
    elif uncertainty > 0.4:
        level = "Moderate"
    else:
        level = "Low"
    
    return f"{level} uncertainty (Q={uncertainty:.3f}): {dominant_name} dominant ({dominant_value:.3f})"


class UncertaintyCalculator:
    """Stateful uncertainty calculator with history tracking."""
    
    def __init__(self, weights: Optional[Tuple[float, float, float]] = None):
        self.weights = weights or (0.45, 0.35, 0.20)
        self.history = []
        self.prev_state = None
    
    def calculate(self, state: np.ndarray) -> UncertaintyResult:
        """Calculate uncertainty with automatic drift tracking."""
        result = calculate_uncertainty(
            state=state,
            prev_state=self.prev_state,
            weights=self.weights
        )
        
        self.history.append(result)
        self.prev_state = state
        
        return result
    
    def reset(self):
        """Reset history and previous state."""
        self.history.clear()
        self.prev_state = None
