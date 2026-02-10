"""
Δ-Log v3.4 Core Package
"""
# 1. Core Logic Imports
from .ebreak_calculator import EBreakCalculator

# 2. BCDSI Imports (Recovered modules)
from .bcdsi.monitor import EBreakMonitor
from .bcdsi.intervention import BcdsiIntervenor
from .bcdsi.threshold import DynamicThreshold

__version__ = "3.4.0"

# 3. The CONTRACT (이게 없어서 에러가 났음)
CONTRACT = {
    "entrypoint": "EBreakCalculator.calculate_ebreak()",
    "required_returns": ["e_break_qbn", "theta_integrity", "bcdsi_detected", "analysis_summary"],
    "version": __version__
}

__all__ = [
    "EBreakCalculator", 
    "EBreakMonitor", 
    "BcdsiIntervenor", 
    "CONTRACT"
]

# Optional: Threshold might be missing, create dummy if needed
try:
    from .bcdsi.threshold import DynamicThreshold
except ImportError:
    pass



