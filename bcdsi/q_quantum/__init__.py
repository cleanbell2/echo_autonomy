# Core Engine (Single Source of Truth)
from .ebreak_calculator import EBreakCalculator

__version__ = "3.4.0"

# Expose all components
__all__ = [
    'EBreakCalculator',
    
    # Individual calculation modules
    'von_neumann_entropy',
    'thermodynamic_entropy', 
    'quantum_coherence',
    'coherence_measures',
    'non_unitarity',
    'bias_induction',
    
    # BCDSI integration
    
    # Legacy compatibility
    'LegacyEbreakEngine',  # Fallback name
    
    # Integration components
    'BcdsiIntervenor',
    'DynamicThreshold',
    'EBreakMonitor',
    'GovernanceBridge',
    'BcdsiIntervenor',
    'DynamicThreshold',
    'EBreakMonitor',
    'GovernanceBridge',
    
    # Utilities
    'CONTRACT'
]