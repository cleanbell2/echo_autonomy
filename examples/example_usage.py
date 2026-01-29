"""
Example usage of the ultrawork E_break calculation engine.

This example demonstrates how to use the EBreachEngine to calculate:
- von Neumann entropy
- Thermodynamic entropy  
- Quantum coherence
- Comprehensive E_break metrics

Requirements:
- numpy
- scipy
"""

import numpy as np
from e_break_engine import EBreachEngine


def main():
    """Demonstrate E_break engine functionality with various quantum states."""
    
    print("=== Ultrawork E_break Calculation Engine Demo ===\n")
    
    # Initialize the engine
    engine = EBreachEngine(tolerance=1e-12)
    
    # Example 1: Pure states
    print("1. Pure State Analysis")
    print("-" * 30)
    
    # Create a superposition state
    psi_superposition = np.array([1, 1]) / np.sqrt(2)  # |+⟩ state
    rho_pure = engine.create_pure_state(psi_superposition)
    
    results_pure = engine.e_break(rho_pure, temperature=300.0)
    print(f"Superposition state |+>:")
    print(f"  von Neumann entropy: {results_pure['von_neumann_entropy']:.6f}")
    print(f"  Coherence (l1-norm): {results_pure['coherence_l1_norm']:.6f}")
    print(f"  Coherence (rel-entropy): {results_pure['coherence_relative_entropy']:.6f}")
    print(f"  E_break: {results_pure['e_break']:.6f}")
    print()
    
    # Example 2: Mixed states
    print("2. Mixed State Analysis")
    print("-" * 30)
    
    # Create a thermal state
    H = np.array([[1.0, 0.0], [0.0, 2.0]])  # Simple 2-level Hamiltonian
    rho_thermal = engine.create_thermal_state(H, temperature=300.0)
    
    results_thermal = engine.e_break(rho_thermal, temperature=300.0)
    print(f"Thermal state (T=300K):")
    print(f"  von Neumann entropy: {results_thermal['von_neumann_entropy']:.6f}")
    print(f"  Thermodynamic entropy: {results_thermal['thermodynamic_entropy']:.2e} J/K")
    print(f"  Coherence (l1-norm): {results_thermal['coherence_l1_norm']:.6f}")
    print(f"  E_break: {results_thermal['e_break']:.6f}")
    print()
    
    # Example 3: Maximally mixed state
    print("3. Maximally Mixed State")
    print("-" * 30)
    
    rho_maximally_mixed = np.eye(2) / 2
    results_max_mixed = engine.e_break(rho_maximally_mixed, temperature=300.0)
    print(f"Maximally mixed state (2x2):")
    print(f"  von Neumann entropy: {results_max_mixed['von_neumann_entropy']:.6f}")
    print(f"  Expected: ln(2) = {np.log(2):.6f}")
    print(f"  Coherence (l1-norm): {results_max_mixed['coherence_l1_norm']:.6f}")
    print()
    
    # Example 4: Bell state (entangled pure state)
    print("4. Entangled State Analysis")
    print("-" * 30)
    
    bell_state = np.array([1, 0, 0, 1]) / np.sqrt(2)  # |Φ+⟩ Bell state
    rho_bell = engine.create_pure_state(bell_state)
    
    results_bell = engine.e_break(rho_bell, temperature=300.0)
    print(f"Bell state |Phi+>:")
    print(f"  von Neumann entropy: {results_bell['von_neumann_entropy']:.6f}")
    print(f"  Coherence (l1-norm): {results_bell['coherence_l1_norm']:.6f}")
    print()
    
    # Example 5: Custom mixed state
    print("5. Custom Mixed State")
    print("-" * 30)
    
    probabilities = [0.7, 0.2, 0.1]
    states = [
        np.array([1, 0]),           # |0>
        np.array([0, 1]),           # |1>  
        np.array([1, 1]) / np.sqrt(2)  # |+>
    ]
    
    rho_custom = engine.create_mixed_state(probabilities, states)
    results_custom = engine.e_break(rho_custom, temperature=300.0)
    
    print(f"Custom mixed state (p=[0.7, 0.2, 0.1]):")
    print(f"  von Neumann entropy: {results_custom['von_neumann_entropy']:.6f}")
    print(f"  Thermodynamic entropy: {results_custom['thermodynamic_entropy']:.2e} J/K")
    print(f"  Coherence (l1-norm): {results_custom['coherence_l1_norm']:.6f}")
    print(f"  Coherence (rel-entropy): {results_custom['coherence_relative_entropy']:.6f}")
    print()
    
    # Example 6: Temperature dependence
    print("6. Temperature Dependence")
    print("-" * 30)
    
    temperatures = [10, 100, 1000, 10000]  # Kelvin
    
    print(f"Temperature vs Entropy for thermal state:")
    print(f"{'T (K)':<8} {'S_vN':<12} {'S_thermo (J/K)':<15}")
    print("-" * 40)
    
    for T in temperatures:
        rho_temp = engine.create_thermal_state(H, T)
        s_vn = engine.von_neumann_entropy(rho_temp)
        s_thermo = engine.thermodynamic_entropy(rho_temp, T)
        print(f"{T:<8} {s_vn:<12.6f} {s_thermo:<15.2e}")
    print()
    
    # Example 7: Coherence weight analysis
    print("7. E_break Coherence Weight Analysis")
    print("-" * 40)
    
    weights = [0.0, 0.25, 0.5, 0.75, 1.0]
    
    print(f"Coherence Weight vs E_break:")
    print(f"{'Weight':<8} {'E_break':<12}")
    print("-" * 25)
    
    for weight in weights:
        results = engine.e_break(rho_custom, 300.0, coherence_weight=weight)
        print(f"{weight:<8} {results['e_break']:<12.6f}")
    
    print("\n=== Demo Complete ===")


def quantum_gate_example():
    """Example showing how quantum gates affect coherence."""
    print("\n=== Quantum Gate Effects on Coherence ===\n")
    
    engine = EBreachEngine()
    
    # Start with |0> state (no coherence)
    psi_0 = np.array([1, 0])
    rho_0 = engine.create_pure_state(psi_0)
    
    print("Initial state |0>:")
    results_0 = engine.e_break(rho_0, 300.0)
    print(f"  Coherence (l1-norm): {results_0['coherence_l1_norm']:.6f}")
    
    # Apply Hadamard gate: creates superposition
    H_gate = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    psi_plus = H_gate @ psi_0
    rho_plus = engine.create_pure_state(psi_plus)
    
    print("\nAfter Hadamard gate (creates |+>):")
    results_plus = engine.e_break(rho_plus, 300.0)
    print(f"  Coherence (l1-norm): {results_plus['coherence_l1_norm']:.6f}")
    
    # Apply phase gate: adds relative phase
    S_gate = np.array([[1, 0], [0, 1j]])
    psi_phase = S_gate @ psi_plus
    rho_phase = engine.create_pure_state(psi_phase)
    
    print("\nAfter Phase gate:")
    results_phase = engine.e_break(rho_phase, 300.0)
    print(f"  Coherence (l1-norm): {results_phase['coherence_l1_norm']:.6f}")


if __name__ == "__main__":
    main()
    quantum_gate_example()