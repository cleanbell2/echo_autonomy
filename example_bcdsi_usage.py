"""
Example usage of BCDSI (Quantum Coherent Bias Detection System).

Demonstrates intervention, threshold calculation, and monitoring capabilities.
"""

import numpy as np
import time
import threading
from datetime import datetime

# Import BCDSI components
from bcdsi.intervention import intervene, InterventionLevel, format_intervention_message
from bcdsi.threshold import (
    DynamicThreshold, PolicyType, SystemCriticality,
    calculate_theta_integrity, create_policy_based_threshold
)
from bcdsi.monitor import EBreakMonitor, EBreakMetrics, create_monitoring_dashboard


def simulate_quantum_system(duration_seconds: int = 30) -> None:
    """
    Simulate a quantum system with varying E_break values.
    
    Args:
        duration_seconds: Simulation duration
    """
    print("=== Quantum System Simulation ===")
    print(f"Simulating for {duration_seconds} seconds...")
    
    # Create monitoring system
    threshold_system = DynamicThreshold(
        base_threshold=0.1,
        policy=PolicyType.MODERATE,
        adaptation_rate=0.1
    )
    
    def alert_callback(data):
        print(f"\n🚨 ALERT: {format_intervention_message(intervene(
            data['e_break_value'],
            data['theta_integrity'],
            threshold_system.current_threshold
        ))}")
        print(f"   Recommended: {data['recommended_action']}")
        print(f"   Severity: {data['severity']}")
        print(f"   Trend: {data['trend_direction']}")
    
    monitor = EBreakMonitor(
        threshold_system=threshold_system,
        session_duration=duration_seconds,
        alert_callback=alert_callback
    )
    
    # Start monitoring
    session_id = monitor.start_monitoring("quantum_simulation")
    print(f"Started monitoring session: {session_id}")
    
    # Simulate quantum system behavior
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        # Simulate varying E_break patterns
        elapsed = time.time() - start_time
        
        if elapsed < 10:
            # Normal operation
            e_break = 0.8 + np.random.normal(0, 0.1)
        elif elapsed < 20:
            # Slight degradation
            e_break = 1.2 + np.random.normal(0, 0.2)
        elif elapsed < 25:
            # Recovering
            e_break = 0.6 + np.random.normal(0, 0.1)
        else:
            # Critical BCDSI attack simulation
            e_break = 2.5 + np.random.normal(0, 0.3)
        
        monitor.add_metrics(EBreakMetrics(
            e_break_value=max(0.0, e_break),
            timestamp=time.time(),
            source="quantum_simulator"
        ))
        
        # Update dashboard periodically
        if int(elapsed) % 5 == 0:
            print(f"\n{create_monitoring_dashboard(monitor)}")
        
        time.sleep(1)
    
    # Stop monitoring and show results
    summary = monitor.stop_monitoring()
    
    print(f"\n=== Session Summary ===")
    print(f"Session Duration: {summary.get('duration_seconds', 0):.2f}s")
    print(f"Metrics Processed: {summary.get('total_metrics', 0)}")
    print(f"Alerts Generated: {summary.get('total_alerts', 0)}")
    print(f"Interventions Recommended: {summary.get('total_interventions', 0)}")
    print(f"Final Threshold: {summary.get('final_threshold', 0.0):.6f}")


def demonstrate_intervention_levels():
    """Demonstrate different BCDSI intervention levels."""
    print("\n=== BCDSI Intervention Level Demonstration ===")
    
    scenarios = [
        (0.15, "Mild BCDSI - Warning"),
        (0.08, "Moderate BCDSI - Modification"),
        (0.03, "Critical BCDSI - Blocking"),
        (0.12, "No BCDSI - Monitoring")
    ]
    
    for theta_integrity, description in scenarios:
        record = intervene(
            e_break_value=1.0,
            theta_integrity=theta_integrity,
            threshold=0.1
        )
        
        print(f"\n{description}:")
        print(f"  θ_integrity: {theta_integrity:.6f}")
        print(f"  Intervention: {record.intervention_level.value}")
        print(f"  Action: {record.action_taken}")
        print(f"  Effectiveness: {record.effectiveness_score:.3f}")


def demonstrate_dynamic_thresholds():
    """Demonstrate dynamic threshold adjustment."""
    print("\n=== Dynamic Threshold Demonstration ===")
    
    # Create threshold systems with different policies
    policies = [
        PolicyType.CONSERVATIVE,
        PolicyType.MODERATE,
        PolicyType.AGGRESSIVE
    ]
    
    for policy in policies:
        threshold = DynamicThreshold(
            base_threshold=0.1,
            policy=policy,
            adaptation_rate=0.15
        )
        
        print(f"\n{policy.value.title()} Policy:")
        print(f"  Base Threshold: {threshold.base_threshold:.6f}")
        
        # Simulate system degradation
        theta_values = [0.9, 0.8, 0.6, 0.4, 0.2]
        
        for theta in theta_values:
            # Calculate integrity and update threshold
            adjusted_theta = threshold.calculate_theta_integrity(
                e_break_value=1.0,
                vn_entropy=0.5,
                coherence=0.3,
                non_unitarity=0.2,
                historical_theta=theta_values
            )
            threshold._update_threshold(adjusted_theta)
        
        print(f"  After degradation to θ={theta:.2f}: threshold={threshold.current_threshold:.6f}")


def demonstrate_monitoring_features():
    """Demonstrate advanced monitoring features."""
    print("\n=== Advanced Monitoring Features ===")
    
    # Create monitoring system with custom configuration
    threshold_system = create_policy_based_threshold(
        SystemCriticality.MEDIUM,
        environment="research"
    )
    
    monitor = EBreakMonitor(
        threshold_system=threshold_system,
        session_duration=10,
        alert_callback=lambda data: print(f"🔔 Custom Alert: E_break={data['e_break_value']:.3f}")
    )
    
    session_id = monitor.start_monitoring("advanced_demo")
    print(f"Started advanced monitoring: {session_id}")
    
    # Add various types of metrics
    print("\nAdding metrics...")
    
    # Normal metric
    monitor.add_metrics(EBreakMetrics(
        e_break_value=0.8,
        timestamp=time.time(),
        source="normal_operation",
        confidence=0.9,
        metadata={'component': 'quantum_processor'}
    ))
    
    # List of metrics
    metrics_batch = [
        EBreakMetrics(e_break_value=1.1, source="batch_1"),
        EBreakMetrics(e_break_value=0.9, source="batch_2"),
        EBreakMetrics(e_break_value=1.05, source="batch_3")
    ]
    monitor.add_metrics(metrics_batch)
    
    # Critical metric
    monitor.add_metrics(EBreakMetrics(
        e_break_value=2.3,
        timestamp=time.time(),
        source="anomaly_detected",
        confidence=0.95,
        metadata={'anomaly_type': 'spike', 'severity': 'high'}
    ))
    
    time.sleep(1)
    
    # Show statistics
    stats = monitor.get_monitoring_statistics()
    print(f"\nMonitoring Statistics:")
    print(f"  Buffer Size: {stats.get('buffer_statistics', {}).get('buffer_size', 0)}")
    print(f"  Current E_break: {stats.get('buffer_statistics', {}).get('e_break_current', 0):.3f}")
    print(f"  Alerts: {stats.get('total_alerts', 0)}")
    
    # Export session data
    filename = f"bcdsi_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    monitor.export_session_data(filename)
    print(f"\nSession data exported to: {filename}")
    
    monitor.stop_monitoring()


def demonstrate_real_world_scenario():
    """Demonstrate realistic BCDSI detection scenario."""
    print("\n=== Real-World BCDSI Scenario ===")
    print("Simulating quantum computing cluster under BCDSI attack...")
    
    # Initialize monitoring for production environment
    production_threshold = create_policy_based_threshold(
        SystemCriticality.HIGH,
        environment="production"
    )
    
    attack_detected = threading.Event()
    recovery_triggered = threading.Event()
    
    def sophisticated_alert(data):
        if data['severity'] == 'critical' and not attack_detected.is_set():
            attack_detected.set()
            print(f"\n🚨🚨🚨 CRITICAL BCDSI ATTACK DETECTED!")
            print(f"   Pattern: Rapid θ_integrity degradation")
            print(f"   Source: {data.get('source', 'unknown')}")
            print(f"   Response: System isolation initiated")
        elif data['severity'] == 'high' and attack_detected.is_set():
            recovery_triggered.set()
            print(f"\n✅ BCDSI mitigation in progress")
            print(f"   Status: Quantum error correction applied")
            print(f"   Recovery: {data['theta_integrity']:.6f}")
    
    monitor = EBreakMonitor(
        threshold_system=production_threshold,
        session_duration=15,
        alert_callback=sophisticated_alert
    )
    
    session_id = monitor.start_monitoring("production_cluster")
    print(f"Production monitoring started: {session_id}")
    
    # Simulate attack progression
    phases = [
        (5, "Initial infiltration - gradual degradation"),
        (8, "Active attack - rapid integrity loss"),
        (3, "System response - intervention and recovery"),
        (4, "Post-attack monitoring - stabilization")
    ]
    
    for phase_duration, description in phases:
        print(f"\n--- {description} ---")
        
        phase_start = time.time()
        
        if "infiltration" in description:
            # Gradual degradation
            for i in range(phase_duration):
                e_break = 0.8 + (i * 0.05)  # Slow degradation
                monitor.add_metrics(EBreakMetrics(
                    e_break_value=e_break,
                    source="bcdsi_probe",
                    metadata={'attack_phase': 'infiltration'}
                ))
                time.sleep(0.1)
        
        elif "active attack" in description:
            # Rapid degradation
            for i in range(phase_duration):
                e_break = 1.5 + (i * 0.2)  # Fast degradation
                monitor.add_metrics(EBreakMetrics(
                    e_break_value=e_break,
                    source="bcdsi_attack",
                    metadata={'attack_phase': 'active'}
                ))
                time.sleep(0.1)
        
        elif "response" in description:
            # Recovery phase
            for i in range(phase_duration):
                current_time = time.time()
                if recovery_triggered.is_set():
                    # System recovering
                    e_break = max(0.3, 2.0 - (i * 0.3))
                else:
                    # Still under attack
                    e_break = 1.8 + np.random.normal(0, 0.1)
                
                monitor.add_metrics(EBreakMetrics(
                    e_break_value=e_break,
                    source="defense_system",
                    metadata={'attack_phase': 'response'}
                ))
                time.sleep(0.1)
        
        else:
            # Stabilization
            for i in range(phase_duration):
                e_break = 0.6 + np.random.normal(0, 0.05)  # Return to normal
                monitor.add_metrics(EBreakMetrics(
                    e_break_value=e_break,
                    source="recovery_system",
                    metadata={'attack_phase': 'stabilization'}
                ))
                time.sleep(0.1)
        
        # Show dashboard after each phase
        print(f"\n{create_monitoring_dashboard(monitor)}")
    
    summary = monitor.stop_monitoring()
    
    print(f"\n=== Attack Summary ===")
    print(f"Total Metrics: {summary.get('total_metrics', 0)}")
    print(f"Alerts Generated: {summary.get('total_alerts', 0)}")
    print(f"Interventions: {summary.get('total_interventions', 0)}")
    print(f"Final Threshold: {summary.get('final_threshold', 0.0):.6f}")
    
    if attack_detected.is_set():
        print("✅ BCDSI attack successfully detected and mitigated!")
    else:
        print("❌ BCDSI attack simulation completed")


def main():
    """Main demonstration function."""
    print("BCDSI (Quantum Coherent Bias Detection System) Demo")
    print("=" * 60)
    
    try:
        # Run demonstrations
        demonstrate_intervention_levels()
        demonstrate_dynamic_thresholds()
        demonstrate_monitoring_features()
        demonstrate_real_world_scenario()
        
        # Interactive simulation
        print(f"\n=== Interactive Simulation ===")
        print("Press Enter to start interactive quantum system simulation...")
        print("Type 'stop' to end simulation")
        
        monitor = EBreakMonitor()
        session_id = monitor.start_monitoring("interactive")
        
        while True:
            user_input = input(f"[{session_id}]> ").strip()
            
            if user_input.lower() == 'stop':
                break
            elif user_input:
                try:
                    e_break = float(user_input)
                    monitor.add_metrics(EBreakMetrics(
                        e_break_value=e_break,
                        timestamp=time.time(),
                        source="user_input"
                    ))
                    print(f"Added E_break: {e_break}")
                except ValueError:
                    print("Invalid E_break value. Please enter a number.")
        
        summary = monitor.stop_monitoring()
        print(f"\nInteractive session ended: {summary.get('total_metrics', 0)} metrics processed")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError during demonstration: {e}")
    
    print("\n🏁 BCDSI Demo Complete!")


if __name__ == "__main__":
    main()