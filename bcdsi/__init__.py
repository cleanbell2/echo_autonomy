"""
BCDSI (Quantum Coherent Bias Detection System Intervention) package.

Monitors and intervenes in quantum systems to detect and counteract BCDSI interference.
"""

from .intervention import intervene, InterventionLevel, InterventionRecord
from .threshold import calculate_theta_integrity, DynamicThreshold
from .monitor import EBreakMonitor

__version__ = "1.0.0"
__all__ = [
    'intervene',
    'InterventionLevel', 
    'InterventionRecord',
    'calculate_theta_integrity',
    'DynamicThreshold',
    'EBreakMonitor'
]