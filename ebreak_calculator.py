"""
Integrated E_break calculator for ultrawork engine.

Combines all modules: thermodynamic, coherence, non_unitarity, and e_break_engine.
Implements: E_break^QBN = ΔS + γ·TΣ + ΔC + ℕ(ε)
"""

import numpy as np
from typing import Union, Dict, Optional, Tuple
from e_break_engine import EBreachEngine
from thermodynamic import thermodynamic_entropy
from coherence import quantum_coherence, coherence_measures
from non_unitarity import non_unitarity, bias_induction


class EBreakCalculator:
    """
    Integrated E_break calculator combining all quantum metrics.
    
    E_break^QBN = ΔS + γ·TΣ + ΔC + ℕ(ε)
    """
    
    def __init__(self, gamma: float = 1.0, 
                 theta_integrity_threshold: float = 0.1,
                 tolerance: float = 1e-12):
        """
        Initialize E_break calculator.
        
        Args:
            gamma: Thermodynamic coupling coefficient
            theta_integrity_threshold: Threshold for BCDSI detection
            tolerance: Numerical tolerance
        """
        self.gamma = gamma
        self.theta_integrity_threshold = theta_integrity_threshold
        self.tolerance = tolerance
        self.ebreak_engine = EBreachEngine(tolerance)
        
        # Analysis history
        self.analysis_history = []
    
    def calculate_ebreak(self, 
                          density_matrix: Union[np.ndarray, list],
                          work: float = 0.0,
                          free_energy_change: float = 0.0,
                          quantum_channel: Union[np.ndarray, list] = None,
                          reference_density_matrix: Union[np.ndarray, list] = None,
                          coherence_weight: float = 0.5,
                          non_unitarity_method: str = 'trace_distance',
                          bias_method: str = 'operator_norm') -> dict:
        """
        Calculate comprehensive E_break metrics.
        
        Args:
            density_matrix: Current quantum state density matrix
            work: Work done in process (W)
            free_energy_change: Change in free energy (ΔF)
            quantum_channel: Quantum channel for non-unitarity analysis
            reference_density_matrix: Reference state for coherence change
            coherence_weight: Weight for coherence in final calculation (0-1)
            non_unitarity_method: Method for non-unitarity calculation
            bias_method: Method for bias induction calculation
            
        Returns:
            Dictionary containing all E_break components and BCDSI detection
        """
        # Convert inputs to numpy arrays
        rho = np.asarray(density_matrix, dtype=complex)
        rho_ref = np.asarray(reference_density_matrix, dtype=complex) if reference_density_matrix is not None else None
        
        # Validate density matrix
        self.ebreak_engine._validate_density_matrix(rho)
        
        # Calculate individual components
        results = self._calculate_components(rho, rho_ref, work, free_energy_change, 
                                          quantum_channel, coherence_weight,
                                          non_unitarity_method, bias_method)
        
        # Calculate final E_break
        ebreak_value = self._calculate_final_ebreak(results)
        results['e_break_qbn'] = ebreak_value
        
        # BCDSI detection
        bcdsi_detected = self._detect_bcdsi(results)
        results['bcdsi_detected'] = bcdsi_detected
        results['theta_integrity'] = self._calculate_theta_integrity(results)
        
        # Analysis summary
        results['analysis_summary'] = self._generate_summary(results)
        
        self.analysis_history.append(results)
        return results
    
    def _calculate_components(self, rho: np.ndarray, rho_ref: Optional[np.ndarray],
                              work: float, free_energy_change: float,
                              quantum_channel: Optional[np.ndarray],
                              coherence_weight: float,
                              non_unitarity_method: str,
                              bias_method: str) -> dict:
        """Calculate all individual E_break components."""
        components = {}
        
        # 1. von Neumann entropy change (ΔS)
        vn_entropy = self.ebreak_engine.von_neumann_entropy(rho)
        components['von_neumann_entropy'] = vn_entropy
        
        if rho_ref is not None:
            vn_entropy_ref = self.ebreak_engine.von_neumann_entropy(rho_ref)
            delta_s = vn_entropy - vn_entropy_ref
            components['delta_von_neumann_entropy'] = delta_s
        else:
            delta_s = vn_entropy  # Assume reference is zero entropy state
            components['delta_von_neumann_entropy'] = delta_s
        
        # 2. Thermodynamic entropy (γ·TΣ)
        thermo_entropy = thermodynamic_entropy(work, free_energy_change, self.gamma)
        components['thermodynamic_entropy'] = thermo_entropy
        components['gamma_times_ts'] = thermo_entropy  # γ·TΣ
        
        # 3. Quantum coherence (ΔC)
        coherence_measures_result = coherence_measures(rho, self.tolerance)
        components['coherence_l1_norm'] = coherence_measures_result['l1_norm']
        components['coherence_relative_entropy'] = coherence_measures_result['relative_entropy']
        
        # Weighted coherence measure
        delta_c = (1 - coherence_weight) * coherence_measures_result['l1_norm'] + \
                  coherence_weight * coherence_measures_result['relative_entropy']
        components['delta_c'] = delta_c
        
        if rho_ref is not None:
            ref_coherence = coherence_measures(rho_ref, self.tolerance)
            delta_coherence_l1 = coherence_measures_result['l1_norm'] - ref_coherence['l1_norm']
            delta_coherence_re = coherence_measures_result['relative_entropy'] - ref_coherence['relative_entropy']
            
            delta_c = (1 - coherence_weight) * delta_coherence_l1 + \
                      coherence_weight * delta_coherence_re
            components['delta_coherence_l1'] = delta_coherence_l1
            components['delta_coherence_re'] = delta_coherence_re
            components['delta_c'] = delta_c
        
        # 4. Non-unitarity (ℕ(ε))
        if quantum_channel is not None:
            non_unity = non_unitarity(quantum_channel, non_unitarity_method, self.tolerance)
            bias = bias_induction(quantum_channel, method=bias_method)
            components['non_unitarity'] = non_unity
            components['bias_induction'] = bias
            
            # Combined non-unitarity measure
            n_epsilon = non_unity + bias
            components['n_epsilon'] = n_epsilon
        else:
            components['non_unitarity'] = 0.0
            components['bias_induction'] = 0.0
            components['n_epsilon'] = 0.0
        
        # Input parameters
        components['work'] = work
        components['free_energy_change'] = free_energy_change
        components['gamma'] = self.gamma
        components['coherence_weight'] = coherence_weight
        
        return components
    
    def _calculate_final_ebreak(self, components: dict) -> float:
        """Calculate final E_break value: E_break^QBN = ΔS + γ·TΣ + ΔC + ℕ(ε)"""
        delta_s = components['delta_von_neumann_entropy']
        gamma_ts = components['gamma_times_ts']
        delta_c = components['delta_c']
        n_epsilon = components['n_epsilon']
        
        ebreak = delta_s + gamma_ts + delta_c + n_epsilon
        return float(ebreak)
    
    def _calculate_theta_integrity(self, results: dict) -> float:
        """
        Calculate θ_integrity metric for BCDSI detection.
        
        Higher values indicate more integrity, lower values suggest BCDSI interference.
        """
        # Normalize components to [0, 1] range for integrity calculation
        delta_s = abs(results['delta_von_neumann_entropy'])
        gamma_ts = abs(results['gamma_times_ts'])
        delta_c = abs(results['delta_c'])
        n_epsilon = abs(results['n_epsilon'])
        
        # Calculate integrity based on expected ranges
        # This is a heuristic - can be refined based on specific requirements
        entropy_integrity = min(1.0, delta_s)  # Normalize expected entropy range
        thermodynamic_integrity = min(1.0, abs(gamma_ts) / 10.0)  # Typical range ~[0, 10]
        coherence_integrity = min(1.0, delta_c)  # Coherence typically [0, 1]
        non_unity_integrity = 1.0 - min(1.0, n_epsilon)  # Lower is better for unitary systems
        
        # Weighted average
        theta_integrity = (entropy_integrity + thermodynamic_integrity + 
                          coherence_integrity + non_unity_integrity) / 4.0
        
        return theta_integrity
    
    def _detect_bcdsi(self, results: dict) -> bool:
        """
        Detect BCDSI (Quantum Coherent Bias Detection System Interference).
        
        Returns True if θ_integrity falls below threshold.
        """
        theta_integrity = self._calculate_theta_integrity(results)
        return theta_integrity < self.theta_integrity_threshold
    
    def _generate_summary(self, results: dict) -> str:
        """Generate analysis summary."""
        summary_parts = []
        
        ebreak_value = results['e_break_qbn']
        summary_parts.append(f"E_break^QBN = {ebreak_value:.6f}")
        
        # Component breakdown
        components = [
            f"ΔS = {results['delta_von_neumann_entropy']:.6f}",
            f"γ·TΣ = {results['gamma_times_ts']:.6f}",
            f"ΔC = {results['delta_c']:.6f}",
            f"ℕ(ε) = {results['n_epsilon']:.6f}"
        ]
        summary_parts.append(f"Components: {' + '.join(components)}")
        
        # BCDSI status
        if results['bcdsi_detected']:
            summary_parts.append(f"WARNING: BCDSI DETECTED (theta_integrity = {results['theta_integrity']:.6f})")
        else:
            summary_parts.append(f"OK: No BCDSI interference (theta_integrity = {results['theta_integrity']:.6f})")
        
        return " | ".join(summary_parts)
    
    def compare_states(self, states: dict, 
                        work_values: dict = None,
                        free_energy_values: dict = None,
                        channels: dict = None) -> dict:
        """
        Compare E_break metrics across multiple quantum states.
        
        Args:
            states: Dictionary of state_name -> density_matrix
            work_values: Dictionary of state_name -> work (optional)
            free_energy_values: Dictionary of state_name -> free_energy_change (optional)
            channels: Dictionary of state_name -> quantum_channel (optional)
            
        Returns:
            Comparison results
        """
        results = {}
        
        for state_name, density_matrix in states.items():
            work = work_values.get(state_name, 0.0) if work_values else 0.0
            free_energy = free_energy_values.get(state_name, 0.0) if free_energy_values else 0.0
            channel = channels.get(state_name) if channels else None
            
            results[state_name] = self.calculate_ebreak(
                density_matrix, work, free_energy, channel
            )
        
        return results
    
    def find_anomalous_state(self, comparison_results: dict) -> str:
        """
        Find most anomalous state based on E_break deviation.
        
        Args:
            comparison_results: Results from compare_states
            
        Returns:
            Name of most anomalous state
        """
        if not comparison_results:
            return ""
        
        # Calculate average E_break
        ebreak_values = [result['e_break_qbn'] for result in comparison_results.values()]
        avg_ebreak = np.mean(ebreak_values)
        
        # Find state with maximum deviation
        max_deviation = -1
        most_anomalous = ""
        
        for state_name, result in comparison_results.items():
            deviation = abs(result['e_break_qbn'] - avg_ebreak)
            if deviation > max_deviation:
                max_deviation = deviation
                most_anomalous = state_name
        
        return most_anomalous
    
    def reset_history(self) -> None:
        """Clear analysis history."""
        self.analysis_history.clear()
    
    def get_analysis_statistics(self) -> dict:
        """Get statistics from analysis history."""
        if not self.analysis_history:
            return {'message': 'No analysis history available'}
        
        ebreak_values = [result['e_break_qbn'] for result in self.analysis_history]
        
        return {
            'total_analyses': len(self.analysis_history),
            'mean_ebreak': np.mean(ebreak_values),
            'std_ebreak': np.std(ebreak_values),
            'min_ebreak': np.min(ebreak_values),
            'max_ebreak': np.max(ebreak_values),
            'bcdsi_count': sum(1 for result in self.analysis_history if result['bcdsi_detected']),
            'bcdsi_rate': sum(1 for result in self.analysis_history if result['bcdsi_detected']) / len(self.analysis_history)
        }


def create_test_quantum_systems() -> dict:
    """Create test quantum systems for demonstration."""
    systems = {}
    
    # 1. Pure state |0⟩
    rho_0 = np.array([[1, 0], [0, 0]], dtype=complex)
    systems['pure_0'] = rho_0
    
    # 2. Superposition state |+⟩
    rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
    systems['superposition_plus'] = rho_plus
    
    # 3. Maximally mixed state
    rho_mixed = np.eye(2) / 2
    systems['maximally_mixed'] = rho_mixed
    
    # 4. Partially coherent state
    rho_partial = 0.7 * rho_0 + 0.3 * rho_plus
    systems['partial_coherence'] = rho_partial
    
    return systems


def create_test_channels() -> dict:
    """Create test quantum channels."""
    channels = {}
    
    # Unitary channel
    from non_unitarity import create_unitary_channel
    channels['unitary'] = create_unitary_channel(np.pi/4)
    
    # Dephasing channel
    from non_unitarity import create_dephasing_channel
    channels['dephasing'] = create_dephasing_channel(0.5)
    
    # Amplitude damping channel
    from non_unitarity import create_amplitude_damping_channel
    channels['damping'] = create_amplitude_damping_channel(0.3)
    
    return channels


# Example usage function
def example_usage():
    """Demonstrate E_break calculator usage."""
    print("=== E_break Calculator Example ===\n")
    
    # Initialize calculator
    calculator = EBreakCalculator(gamma=1.0, theta_integrity_threshold=0.3)
    
    # Create test systems
    systems = create_test_quantum_systems()
    channels = create_test_channels()
    
    # Analyze each system
    for name, rho in systems.items():
        print(f"Analyzing {name}:")
        
        # Use corresponding channel if available
        channel = channels.get('unitary') if name != 'maximally_mixed' else channels.get('dephasing')
        
        results = calculator.calculate_ebreak(
            density_matrix=rho,
            work=5.0,
            free_energy_change=3.0,
            quantum_channel=channel,
            coherence_weight=0.5
        )
        
        print(f"  {results['analysis_summary']}")
        print()
    
    # Comparison analysis
    print("=== Comparative Analysis ===")
    comparison = calculator.compare_states(systems)
    anomalous = calculator.find_anomalous_state(comparison)
    
    print(f"Most anomalous state: {anomalous}")
    
    # Statistics
    stats = calculator.get_analysis_statistics()
    print(f"\nAnalysis Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    example_usage()