"""
Simplified BCDSI intervention module without dataclass dependency.
"""

from enum import Enum
from typing import List, Dict, Optional, Union
from datetime import datetime


class InterventionLevel(Enum):
    """Levels of BCDSI intervention."""
    WARNING = "warning"
    BLOCK = "block"
    MODIFY = "modify"
    MONITOR = "monitor"


class InterventionRecord:
    """Record of BCDSI intervention."""
    def __init__(self, e_break_value: float, theta_integrity: float, 
                 intervention_level: InterventionLevel, action_taken: str,
                 details: str = "", effectiveness_score: Optional[float] = None,
                 timestamp: Optional[datetime] = None):
        self.e_break_value = e_break_value
        self.theta_integrity = theta_integrity
        self.intervention_level = intervention_level
        self.action_taken = action_taken
        self.details = details
        self.effectiveness_score = effectiveness_score
        self.timestamp = timestamp or datetime.now()


def intervene(e_break_value: float, 
              theta_integrity: float,
              threshold: float = 0.1,
              context: Optional[Dict] = None) -> InterventionRecord:
    """
    Determine appropriate intervention based on E_break and θ_integrity.
    
    Args:
        e_break_value: Calculated E_break^QBN value
        theta_integrity: θ_integrity metric (0-1)
        threshold: BCDSI detection threshold
        context: Additional context for decision making
        
    Returns:
        InterventionRecord with action details
    """
    
    # Determine intervention level
    if theta_integrity < threshold * 0.5:
        # Critical BCDSI - block operations
        level = InterventionLevel.BLOCK
        action = "BLOCK_EXECUTION"
        details = f"Critical BCDSI detected. θ_integrity={theta_integrity:.6f} < {threshold*0.5:.6f}"
        
    elif theta_integrity < threshold * 0.7:
        # Moderate BCDSI - modify behavior
        level = InterventionLevel.MODIFY
        action = "APPLY_CORRECTION"
        details = f"Moderate BCDSI detected. θ_integrity={theta_integrity:.6f} < {threshold*0.7:.6f}"
        
    elif theta_integrity < threshold:
        # Mild BCDSI - warning only
        level = InterventionLevel.WARNING
        action = "LOG_WARNING"
        details = f"Mild BCDSI detected. θ_integrity={theta_integrity:.6f} < {threshold:.6f}"
        
    else:
        # No BCDSI - continue monitoring
        level = InterventionLevel.MONITOR
        action = "CONTINUE_MONITORING"
        details = f"No BCDSI detected. θ_integrity={theta_integrity:.6f} >= {threshold:.6f}"
    
    # Calculate effectiveness score
    effectiveness = _calculate_intervention_effectiveness(e_break_value, theta_integrity, level, context)
    
    return InterventionRecord(
        e_break_value=e_break_value,
        theta_integrity=theta_integrity,
        intervention_level=level,
        action_taken=action,
        details=details,
        effectiveness_score=effectiveness
    )


def _calculate_intervention_effectiveness(e_break: float, 
                                    theta_integrity: float,
                                    level: InterventionLevel,
                                    context: Optional[Dict]) -> float:
    """Calculate effectiveness score for intervention."""
    
    base_score = theta_integrity  # Higher integrity = higher effectiveness
    
    # Adjust based on intervention level
    level_multipliers = {
        InterventionLevel.MONITOR: 1.0,
        InterventionLevel.WARNING: 0.9,
        InterventionLevel.MODIFY: 0.7,
        InterventionLevel.BLOCK: 0.5
    }
    
    effectiveness = base_score * level_multipliers[level]
    
    # Context adjustments
    if context:
        # Adjust for system criticality
        if context.get('critical_system', False):
            effectiveness *= 1.2
            
        # Adjust for temporal factors
        if context.get('urgent_operation', False):
            effectiveness *= 1.1
    
    return min(1.0, effectiveness)


def format_intervention_message(record: InterventionRecord) -> str:
    """Format intervention record for display."""
    
    icons = {
        InterventionLevel.BLOCK: "🚫 BLOCKED",
        InterventionLevel.MODIFY: "⚠️  MODIFIED", 
        InterventionLevel.WARNING: "⚡ WARNING",
        InterventionLevel.MONITOR: "✅ MONITORING"
    }
    
    icon = icons.get(record.intervention_level, "❓ UNKNOWN")
    
    message = (
        f"{icon} {record.timestamp.strftime('%H:%M:%S')} | "
        f"E_break: {record.e_break_value:.6f} | "
        f"θ_integrity: {record.theta_integrity:.6f} | "
        f"{record.action_taken} | "
        f"Effectiveness: {record.effectiveness_score:.3f if record.effectiveness_score else 0.0:.3f}"
    )
    
    if record.details:
        message += f" | {record.details}"
    
    return message


class BCDSIInterventionHistory:
    """Manages intervention history and patterns."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize intervention history.
        
        Args:
            max_history: Maximum records to keep
        """
        self.max_history = max_history
        self.records: List[InterventionRecord] = []
        self.intervention_counts = {}
        for level in InterventionLevel:
            self.intervention_counts[level.value] = 0
    
    def add_record(self, record: InterventionRecord) -> None:
        """Add intervention record to history."""
        self.records.append(record)
        self.intervention_counts[record.intervention_level] += 1
        
        # Maintain maximum history size
        if len(self.records) > self.max_history:
            self.records = self.records[-self.max_history:]
    
    def get_intervention_rate(self, window_size: int = 50) -> Dict[str, float]:
        """
        Calculate intervention rates over time window.
        
        Args:
            window_size: Number of recent records to analyze
            
        Returns:
            Dictionary of intervention rates by level
        """
        if not self.records:
            return {level.value: 0.0 for level in InterventionLevel}
        
        recent_records = self.records[-window_size:]
        total = len(recent_records)
        
        rates = {}
        for level in InterventionLevel:
            count = sum(1 for r in recent_records if r.intervention_level == level)
            rates[level.value] = count / total if total > 0 else 0.0
        
        return rates
    
    def get_pattern_analysis(self) -> Dict[str, Union[str, float]]:
        """
        Analyze patterns in intervention history.
        
        Returns:
            Dictionary with pattern analysis
        """
        if not self.records:
            return {"message": "No intervention history available"}
        
        # Calculate trends
        recent_theta = [r.theta_integrity for r in self.records[-20:]]
        if len(recent_theta) > 1:
            theta_trend = "improving" if recent_theta[-1] > recent_theta[0] else "degrading"
        else:
            theta_trend = "stable"
        
        # Calculate most common intervention
        if self.intervention_counts:
            most_common = max(self.intervention_counts, key=self.intervention_counts.get)
            intervention_frequency = f"Most common: {most_common.value} ({self.intervention_counts[most_common]} times)"
        else:
            intervention_frequency = "No interventions recorded"
        
        return {
            "theta_trend": theta_trend,
            "intervention_frequency": intervention_frequency,
            "total_interventions": len(self.records),
            "intervention_distribution": dict(self.intervention_counts)
        }
    
    def clear_history(self) -> None:
        """Clear intervention history."""
        self.records.clear()
        self.intervention_counts = {level.value: 0 for level in InterventionLevel}


def auto_intervention_system(e_break_history: List[float],
                            theta_history: List[float],
                            threshold: float = 0.1) -> Dict[str, Union[InterventionRecord, str]]:
    """
    Automated intervention system for continuous monitoring.
    
    Args:
        e_break_history: Recent E_break values
        theta_history: Recent θ_integrity values
        threshold: BCDSI detection threshold
        
    Returns:
        Dictionary with intervention recommendations
    """
    if not e_break_history or not theta_history:
        return {"status": "No data available"}
    
    # Get current values
    current_e_break = e_break_history[-1]
    current_theta = theta_history[-1]
    
    # Analyze trends
    if len(theta_history) > 5:
        recent_trend = np.mean(theta_history[-3:]) - np.mean(theta_history[-6:-3])
    else:
        recent_trend = 0.0
    
    # Enhanced context for decision making
    context = {
        'critical_system': recent_trend < -0.1,  # Rapid degradation
        'urgent_operation': current_theta < threshold * 0.3,
        'trend_direction': recent_trend
    }
    
    # Generate intervention recommendation
    recommendation = intervene(
        current_e_break, 
        current_theta, 
        threshold,
        context
    )
    
    # Predict next intervention
    if len(theta_history) > 10:
        prediction_model = _predict_intervention_trend(theta_history)
        next_intervention = predict_model.predict_next(theta_history[-5:])
    else:
        next_intervention = "Insufficient data for prediction"
    
    return {
        "current_intervention": recommendation,
        "prediction": next_intervention,
        "context": context,
        "status": "System monitoring active"
    }


def _predict_intervention_trend(theta_history: List[float]) -> str:
    """
    Predict next intervention type based on historical pattern.
    
    Args:
        theta_history: Historical θ_integrity values
        
    Returns:
        Predicted intervention level
    """
    if len(theta_history) < 3:
        return "insufficient_data"
    
    # Simple trend analysis
    if theta_history[-1] < theta_history[-2] < theta_history[-3]:
        return "likely_warning_or_moderate"
    elif theta_history[-1] > theta_history[-2] > theta_history[-3]:
        return "likely_monitoring"
    else:
        return "stable_pattern"