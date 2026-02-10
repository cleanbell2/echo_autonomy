# Core Engine (Single Source of Truth)
try:
    from .ebreak_calculator import EBreachEngine
    EBreachEngine = EBreachEngine
except ImportError:
    # Fallback if main engine not available
    EBreachEngine = None
    print("Warning: Using fallback implementation")

__version__ = "3.4.0"

# Expose core calculation functions
def calculate_ebreak(*args, **kwargs):
    """Calculate E_break using available engine."""
    if EBreachEngine is None:
        raise ImportError("EBreakEngine not available")
    
    return EBreachEngine.calculate_ebreak(*args, **kwargs)

def get_ebreak_engine():
    """Get the active EBreak engine instance."""
    return EBreachEngine

# Version compatibility
def get_version():
    """Get version information."""
    return {
        'version': __version__,
        'engine_type': 'fallback' if EBreachEngine is None else 'primary',
        'components_available': __all__
    }