"""
Dynamic threshold calculation for BCDSI detection.

Implements adaptive threshold adjustment based on system state and policy requirements.
"""

from enum import Enum
from typing import List, Dict, Optional, Union
import numpy as np


class PolicyType(Enum):
    """Types of BCDSI intervention policies."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


class SystemCriticality(Enum):
    """Criticality levels of quantum systems."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Simplified dataclass replacement
class DynamicThreshold:
    """
    Dynamic threshold with adaptive adjustment capabilities.
    """
    base_threshold: float
    policy: PolicyType = PolicyType.MODERATE
    min_threshold: float = 0.05
    max_threshold: float = 0.5
    adaptation_rate: float = 0.1
    history_window: int = 50
    stability_factor: float = 0.1
    
    def __post_init__(self):
        """Initialize adaptive parameters."""
        self.current_threshold = self.base_threshold
        self.threshold_history: List[float] = []
        self.volatility_history: List[float] = []
        self.adjustment_history: List[Dict] = []
    
    def calculate_theta_integrity(self, e_break_value: float, 
                             vn_entropy: float,
                             coherence: float,
                             non_unitarity: float,
                             historical_theta: Optional[List[float]] = None) -> float:
        """
        Calculate θ_integrity with dynamic threshold adjustment.
        
        Args:
            e_break_value: E_break^QBN value
            vn_entropy: von Neumann entropy
            coherence: Quantum coherence
            non_unitarity: Non-unitarity measure
            historical_theta: Historical θ_integrity values
            
        Returns:
            θ_integrity metric
        """
        # Base integrity calculation
        base_integrity = self._calculate_base_integrity(
            e_break_value, vn_entropy, coherence, non_unitarity
        )
        
        # Apply dynamic adjustments
        adjusted_integrity = self._apply_dynamic_adjustments(
            base_integrity, historical_theta
        )
        
        # Update current threshold based on volatility
        self._update_threshold(adjusted_integrity)
        
        return adjusted_integrity
    
    def _calculate_base_integrity(self, e_break: float, vn_entropy: float,
                               coherence: float, non_unitarity: float) -> float:
        """Calculate base θ_integrity without dynamic adjustments."""
        
        # Normalize components to [0, 1] range
        entropy_score = min(1.0, vn_entropy)  # Typical range [0, ln(d)]
        coherence_score = min(1.0, coherence)  # Range [0, 1]
        non_unity_score = 1.0 - min(1.0, non_unitarity)  # Lower is better
        
        # Weighted combination
        base_integrity = (0.3 * entropy_score + 
                          0.4 * coherence_score + 
                          0.3 * non_unity_score)
        
        return base_integrity
    
    def _apply_dynamic_adjustments(self, base_integrity: float,
                                historical_theta: Optional[List[float]]) -> float:
        """Apply dynamic adjustments based on policy and history."""
        
        adjusted_integrity = base_integrity
        
        if historical_theta and len(historical_theta) >= 5:
            # Calculate volatility
            volatility = np.std(historical_theta[-10:])
            self.volatility_history.append(volatility)
            
            # Volatility adjustment
            if volatility > 0.2:
                # High volatility - lower threshold for faster response
                if self.policy == PolicyType.AGGRESSIVE:
                    adjusted_integrity *= 0.9
                elif self.policy == PolicyType.AGGRESSIVE:
                    adjusted_integrity *= 1.1
            
            # Trend adjustment
            if len(historical_theta) >= 10:
                recent_trend = np.mean(historical_theta[-3:]) - np.mean(historical_theta[-10:-3])
                if recent_trend < -0.05:  # Declining trend
                    adjusted_integrity *= 0.95
                elif recent_trend > 0.05:  # Improving trend
                    adjusted_integrity *= 1.05
        
        return adjusted_integrity
    
    def _update_threshold(self, current_integrity: float) -> None:
        """Update dynamic threshold based on current integrity."""
        
        # Calculate stability score
        if len(self.threshold_history) > 0:
            recent_thresholds = self.threshold_history[-5:]
            stability = 1.0 - (np.std(recent_thresholds) / np.mean(recent_thresholds) if np.mean(recent_thresholds) > 0 else 1.0)
        else:
            stability = 1.0
        
        # Policy-based adjustment
        if self.policy == PolicyType.CONSERVATIVE:
            target_adjustment = -0.05  # More conservative
        elif self.policy == PolicyType.AGGRESSIVE:
            target_adjustment = 0.05   # More aggressive
        else:
            target_adjustment = 0.0    # Neutral
        
        # Apply stability-based moderation
        adjustment = target_adjustment * stability * self.adaptation_rate
        new_threshold = self.current_threshold + adjustment
        
        # Enforce bounds
        new_threshold = np.clip(new_threshold, self.min_threshold, self.max_threshold)
        
        self.current_threshold = new_threshold
        self.threshold_history.append(new_threshold)
        
        # Log adjustment
        self.adjustment_history.append({
            'timestamp': self._get_timestamp(),
            'old_threshold': self.current_threshold - adjustment,
            'new_threshold': self.current_threshold,
            'integrity': current_integrity,
            'policy': self.policy.value
        })
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp for logging."""
        from datetime import datetime
        return datetime.now().strftime('%H:%M:%S')
    
    def set_policy(self, policy: PolicyType) -> None:
        """Change intervention policy."""
        self.policy = policy
        
        # Adjust base threshold based on policy
        if policy == PolicyType.CONSERVATIVE:
            self.base_threshold = 0.15
        elif policy == PolicyType.AGGRESSIVE:
            self.base_threshold = 0.05
        else:
            self.base_threshold = 0.1
    
    def get_system_criticality(self, system_metrics: Dict[str, float]) -> SystemCriticality:
        """
        Determine system criticality based on metrics.
        
        Args:
            system_metrics: Dictionary of system performance metrics
            
        Returns:
            System criticality level
        """
        # Simple heuristic based on error rates and performance
        error_rate = system_metrics.get('error_rate', 0.0)
        latency = system_metrics.get('latency', 0.0)
        resource_usage = system_metrics.get('resource_usage', 0.0)
        
        criticality_score = (error_rate * 0.4 + 
                           min(1.0, latency / 100.0) * 0.3 +
                           min(1.0, resource_usage) * 0.3)
        
        if criticality_score < 0.3:
            return SystemCriticality.LOW
        elif criticality_score < 0.6:
            return SystemCriticality.MEDIUM
        elif criticality_score < 0.8:
            return SystemCriticality.HIGH
        else:
            return SystemCriticality.CRITICAL
    
    def get_threshold_statistics(self) -> Dict[str, Union[float, str]]:
        """
        Get statistics about threshold adjustments.
        
        Returns:
            Dictionary with threshold statistics
        """
        if not self.threshold_history:
            return {"message": "No threshold history available"}
        
        return {
            "current_threshold": self.current_threshold,
            "base_threshold": self.base_threshold,
            "policy": self.policy.value,
            "adjustments_made": len(self.adjustment_history),
            "current_volatility": self.volatility_history[-1] if self.volatility_history else 0.0,
            "stability_score": 1.0 - (np.std(self.threshold_history[-10:]) / np.mean(self.threshold_history[-10:]) if len(self.threshold_history) >= 10 and np.mean(self.threshold_history[-10:]) > 0 else 1.0)
        }
    
    def reset_history(self) -> None:
        """Reset threshold and adjustment history."""
        self.current_threshold = self.base_threshold
        self.threshold_history.clear()
        self.volatility_history.clear()
        self.adjustment_history.clear()


def calculate_theta_integrity(e_break_value: float,
                           theta_history: List[float] = None,
                           policy: PolicyType = PolicyType.MODERATE,
                           system_criticality: SystemCriticality = SystemCriticality.MEDIUM,
                           adaptation_window: int = 50) -> float:
    """
    Calculate θ_integrity with dynamic threshold system.
    
    Args:
        e_break_value: Current E_break value
        theta_history: Historical θ_integrity values
        policy: Intervention policy type
        system_criticality: System criticality level
        adaptation_window: Window size for dynamic adaptation
        
    Returns:
            Current θ_integrity value
    """
    
    # Create dynamic threshold system
    threshold_system = DynamicThreshold(
        base_threshold=0.1,
        policy=policy,
        adaptation_rate=0.1,
        history_window=adaptation_window
    )
    
    # Calculate current integrity
    current_theta = threshold_system.calculate_theta_integrity(
        e_break_value, 
        vn_entropy=0.0,  # Would need actual calculation
        coherence=0.0,    # Would need actual calculation
        non_unitarity=0.0,  # Would need actual calculation
        historical_theta=theta_history
    )
    
    # Adjust based on system criticality
    criticality_multipliers = {
        SystemCriticality.LOW: 1.0,
        SystemCriticality.MEDIUM: 1.0,
        SystemCriticality.HIGH: 0.9,
        SystemCriticality.CRITICAL: 0.8
    }
    
    final_theta = current_theta * criticality_multipliers[system_criticality]
    
    return final_theta


def create_policy_based_threshold(criticality: SystemCriticality,
                             environment: str = "standard") -> DynamicThreshold:
    """
    Create threshold system based on policy and environment.
    
    Args:
        criticality: System criticality level
        environment: Operating environment (standard, research, production)
        
    Returns:
            Configured DynamicThreshold
    """
    
    # Base configurations
    if criticality == SystemCriticality.LOW:
        base_threshold = 0.2
        policy = PolicyType.CONSERVATIVE
    elif criticality == SystemCriticality.MEDIUM:
        base_threshold = 0.1
        policy = PolicyType.MODERATE
    elif criticality == SystemCriticality.HIGH:
        base_threshold = 0.05
        policy = PolicyType.AGGRESSIVE
    else:
        base_threshold = 0.025
        policy = PolicyType.AGGRESSIVE
    
    # Environment adjustments
    if environment == "production":
        min_threshold = 0.1
        max_threshold = 0.3
        adaptation_rate = 0.05  # Slower adaptation in production
    elif environment == "research":
        min_threshold = 0.01
        max_threshold = 0.8
        adaptation_rate = 0.2   # Faster adaptation for research
    else:
        min_threshold = 0.05
        max_threshold = 0.5
        adaptation_rate = 0.1
    
    return DynamicThreshold(
        base_threshold=base_threshold,
        policy=policy,
        min_threshold=min_threshold,
        max_threshold=max_threshold,
        adaptation_rate=adaptation_rate
    )