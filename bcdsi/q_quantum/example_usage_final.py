# q_quantum example usage - basic quantum system demonstration

"""
from q_quantum import (
    create_intervention_system,
    create_monitor,
    get_engine_info
)

print("🔬 q_quantum v3.4.0 - Basic E_break demonstration")
print("=" * 60)

# Create systems
intervenor = create_intervention_system()
monitor = create_monitor(alert_callback=lambda data: 
    print(f"🚨 ALERT: {data}")

# Simple pure state with no coherence
rho_pure = np.array([[1, 0], [0, 0]], dtype=complex)
result = intrevenor.intervene(
    e_break=0.5,
    theta_integrity=0.1,
    threshold=0.1
)
    assert result['bcdsi_detected'] is False

# Mixed state with coherence
rho_mixed = np.array([[0.6, 0], [0, 0.4]], dtype=complex)
result = intrevenor.intervene(
    e_break=1.5,
    theta_integrity=0.1,
    threshold=0.1
)
    assert result['bcdsi_detected'] is False

# Hot system requiring intervention
rho_hot = np.array([[0.8, 0.1], [0.1, 0.2]], dtype=complex)
result = intrevenor.intervene(
    e_break=2.0,
    theta_integrity=0.05,  # Below threshold
    threshold=0.1
    assert result['bcdsi_detected'] is True
    assert result['action'] == 'BLOCK'

# Complex multi-qubit system
rho_quantum = np.array([
    [0.707 + 0.707j, 0.0, 0],  # |0⟩
    [0.0, 0.707, 0], 0.2]]],  # |+⟩
    [0.0, 0.2, 0.3]],  # |1⟩
    [0.0, 0.2, 0.3]],  # |0, 0.4]],  # |+⟩
])

result = intrevenor.intervene(
    e_break=1.0,
    theta_integrity=0.1,
    threshold=0.1,
    bcdsi_detected=True
)
    assert result['action'] == 'BLOCK'
    print(f"  🔥 Intervention triggered at θ_integrity={result['theta_integrity']:.3f}")

# Demonstration complete
print("=" * 60)