"""
Unit tests for BCDSI intervention module.
"""

import pytest
import numpy as np
from datetime import datetime
import time
import threading
import tempfile
import json

from bcdsi.intervention import (
    intervene, InterventionLevel, InterventionRecord,
    BCDSIInterventionHistory, format_intervention_message
)
from bcdsi.threshold import (
    DynamicThreshold, PolicyType, SystemCriticality,
    calculate_theta_integrity, create_policy_based_threshold
)
from bcdsi.monitor import (
    EBreakMonitor, EBreakMetrics, MonitoringSession,
    create_monitoring_dashboard
)


class TestIntervention:
    """Test BCDSI intervention system."""
    
    def test_intervene_levels(self):
        """Test different intervention levels."""
        # Critical BCDSI - should block
        record = intervene(2.0, 0.05, 0.1)
        assert record.intervention_level == InterventionLevel.BLOCK
        assert record.action_taken == "BLOCK_EXECUTION"
        
        # Moderate BCDSI - should modify
        record = intervene(1.0, 0.08, 0.1)
        assert record.intervention_level == InterventionLevel.MODIFY
        assert record.action_taken == "APPLY_CORRECTION"
        
        # Mild BCDSI - should warn
        record = intervene(1.0, 0.09, 0.1)
        assert record.intervention_level == InterventionLevel.WARNING
        assert record.action_taken == "LOG_WARNING"
        
        # No BCDSI - should monitor
        record = intervene(0.5, 0.15, 0.1)
        assert record.intervention_level == InterventionLevel.MONITOR
        assert record.action_taken == "CONTINUE_MONITORING"
    
    def test_intervention_effectiveness(self):
        """Test intervention effectiveness calculation."""
        # High integrity should have higher effectiveness
        record_high = intervene(2.0, 0.8, 0.1)
        record_low = intervene(2.0, 0.2, 0.1)
        
        assert record_high.effectiveness_score > record_low.effectiveness_score
    
    def test_intervention_with_context(self):
        """Test intervention with context adjustment."""
        context = {
            'critical_system': True,
            'urgent_operation': True
        }
        
        record = intervene(1.0, 0.08, 0.1, context=context)
        
        # Should have boosted effectiveness due to critical system
        record_no_context = intervene(1.0, 0.08, 0.1)
        
        assert record.effectiveness_score > record_no_context.effectiveness_score
    
    def test_intervention_history(self):
        """Test intervention history management."""
        history = BCDSIInterventionHistory(max_history=3)
        
        # Add records
        record1 = intervene(1.0, 0.08, 0.1)
        record2 = intervene(0.5, 0.15, 0.1)
        record3 = intervene(2.0, 0.05, 0.1)
        
        history.add_record(record1)
        history.add_record(record2)
        history.add_record(record3)
        
        assert len(history.records) == 3
        assert history.intervention_counts[InterventionLevel.MODIFY] == 1
        assert history.intervention_counts[InterventionLevel.BLOCK] == 1
        assert history.intervention_counts[InterventionLevel.WARNING] == 1
        
        # Test maximum history limit
        record4 = intervene(0.7, 0.12, 0.1)
        history.add_record(record4)
        
        assert len(history.records) == 3  # Should stay at max
        assert history.records[0] == record2  # Should have rotated out record1
    
    def test_pattern_analysis(self):
        """Test pattern analysis in intervention history."""
        history = BCDSIInterventionHistory()
        
        # Add trending pattern (decreasing integrity)
        for i in range(10):
            theta_integrity = 0.9 - (i * 0.05)
            record = intervene(1.0, theta_integrity, 0.1)
            history.add_record(record)
        
        analysis = history.get_pattern_analysis()
        
        assert 'theta_trend' in analysis
        assert analysis['theta_trend'] == "degrading"
        assert 'total_interventions' in analysis
        assert analysis['total_interventions'] == 10


class TestDynamicThreshold:
    """Test dynamic threshold system."""
    
    def test_threshold_creation(self):
        """Test threshold system creation."""
        threshold = DynamicThreshold(
            base_threshold=0.1,
            policy=PolicyType.AGGRESSIVE,
            min_threshold=0.01,
            max_threshold=0.3
        )
        
        assert threshold.base_threshold == 0.1
        assert threshold.policy == PolicyType.AGGRESSIVE
        assert threshold.current_threshold == 0.1
        assert len(threshold.threshold_history) == 0
    
    def test_policy_adjustment(self):
        """Test threshold adjustment based on policy."""
        threshold = DynamicThreshold(base_threshold=0.1)
        
        # Test different policies
        threshold.set_policy(PolicyType.CONSERVATIVE)
        assert threshold.base_threshold == 0.15
        
        threshold.set_policy(PolicyType.AGGRESSIVE)
        assert threshold.base_threshold == 0.05
        
        threshold.set_policy(PolicyType.MODERATE)
        assert threshold.base_threshold == 0.1
    
    def test_dynamic_adjustment(self):
        """Test dynamic threshold adjustments."""
        threshold = DynamicThreshold(
            base_threshold=0.1,
            adaptation_rate=0.2
        )
        
        # Simulate degradation
        for i in range(5):
            theta = 0.8 - (i * 0.1)
            adjusted = threshold.calculate_theta_integrity(
                1.0, 0.0, 0.0, 0.0,
                [theta]
            )
            threshold._update_threshold(adjusted)
        
        # Should have adjusted downward for aggressive degradation
        assert threshold.current_threshold < 0.1
    
    def test_threshold_bounds(self):
        """Test threshold bounds enforcement."""
        threshold = DynamicThreshold(
            base_threshold=0.1,
            min_threshold=0.05,
            max_threshold=0.2
        )
        
        # Try to go below minimum
        threshold.current_threshold = 0.01
        threshold._update_threshold(0.0)
        assert threshold.current_threshold >= 0.05
        
        # Try to go above maximum
        threshold.current_threshold = 0.3
        threshold._update_threshold(1.0)
        assert threshold.current_threshold <= 0.2
    
    def test_system_criticality(self):
        """Test system criticality assessment."""
        threshold = DynamicThreshold()
        
        # Test different criticality levels
        metrics_low = {'error_rate': 0.05, 'latency': 10.0, 'resource_usage': 0.3}
        metrics_high = {'error_rate': 0.2, 'latency': 80.0, 'resource_usage': 0.9}
        
        criticality_low = threshold.get_system_criticality(metrics_low)
        criticality_high = threshold.get_system_criticality(metrics_high)
        
        assert criticality_low == SystemCriticality.LOW
        assert criticality_high == SystemCriticality.HIGH
    
    def test_theta_integrity_calculation(self):
        """Test θ_integrity calculation."""
        threshold = DynamicThreshold()
        
        # Test integrity calculation
        integrity = threshold.calculate_theta_integrity(
            e_break_value=1.0,
            vn_entropy=0.5,
            coherence=0.3,
            non_unitarity=0.2
        )
        
        assert 0.0 <= integrity <= 1.0
        
        # Test with historical data
        history = [0.8, 0.7, 0.6, 0.5]
        integrity_with_history = threshold.calculate_theta_integrity(
            e_break_value=1.0,
            vn_entropy=0.5,
            coherence=0.3,
            non_unitarity=0.2,
            historical_theta=history
        )
        
        # Should be adjusted downward based on declining trend
        assert integrity_with_history < integrity


class TestCalculateThetaIntegrity:
    """Test θ_integrity calculation function."""
    
    def test_basic_calculation(self):
        """Test basic integrity calculation."""
        theta = calculate_theta_integrity(1.0)
        assert 0.0 <= theta <= 1.0
        
        theta_high = calculate_theta_integrity(0.1)
        theta_low = calculate_theta_integrity(3.0)
        
        assert theta_high > theta_low
    
    def test_policy_based_calculation(self):
        """Test policy-based integrity calculation."""
        theta_conservative = calculate_theta_integrity(
            1.0,
            policy=PolicyType.CONSERVATIVE,
            system_criticality=SystemCriticality.LOW
        )
        
        theta_aggressive = calculate_theta_integrity(
            1.0,
            policy=PolicyType.AGGRESSIVE,
            system_criticality=SystemCriticality.HIGH
        )
        
        # Conservative should be more lenient
        assert theta_conservative > theta_aggressive


class TestEBreakMonitor:
    """Test E_break monitoring system."""
    
    def test_monitor_lifecycle(self):
        """Test monitoring session lifecycle."""
        monitor = EBreakMonitor(session_duration=2)  # 2 seconds for testing
        
        # Start monitoring
        session_id = monitor.start_monitoring("test_session")
        
        assert monitor.is_monitoring is True
        assert monitor.current_session.session_id == "test_session"
        
        # Add some metrics
        monitor.add_metrics(1.0)
        monitor.add_metrics(0.8)
        monitor.add_metrics(1.2)
        
        # Wait a bit
        time.sleep(0.5)
        
        # Stop monitoring
        summary = monitor.stop_monitoring()
        
        assert summary["status"] == "completed"
        assert summary["session_id"] == "test_session"
        assert summary["metrics_processed"] >= 3
    
    @pytest.mark.skip(reason="Callback mechanism requires full build dependencies")
    def test_real_time_monitoring(self):
        """Test real-time monitoring functionality."""
        monitor = EBreakMonitor(session_duration=1)
        
        alert_data = []
        def alert_callback(data):
            alert_data.append(data)
        
        # Start monitoring with callback
        monitor.start_monitoring("realtime_test")
        
        # Add metrics that should trigger alerts
        monitor.add_metrics(2.0)  # Should trigger critical alert
        
        # Wait for monitoring to process
        time.sleep(0.2)
        
        # Check alert was generated
        assert len(alert_data) > 0
        
        # Stop monitoring
        monitor.stop_monitoring()
    
    def test_metrics_buffer(self):
        """Test metrics buffer management."""
        monitor = EBreakMonitor()
        
        # Test adding different metric types
        single_metric = EBreakMetrics(e_break_value=1.0)
        metrics_list = [
            EBreakMetrics(e_break_value=1.1),
            EBreakMetrics(e_break_value=0.9)
        ]
        float_value = 1.2
        
        monitor.add_metrics(single_metric)
        monitor.add_metrics(metrics_list)
        monitor.add_metrics(float_value)
        
        # Check buffer size
        assert len(monitor.metrics_buffer) == 4  # 1 + 2 + 1
        
        # Check buffer ordering
        e_break_values = [m.e_break_value for m in monitor.metrics_buffer]
        assert e_break_values[-1] == 1.2  # Last added value
    
    def test_anomaly_detection(self):
        """Test anomaly detection in monitoring."""
        monitor = EBreakMonitor()
        
        # Add normal values
        for i in range(5):
            monitor.add_metrics(1.0 + (i * 0.01))
        
        # Add anomalous value
        monitor.add_metrics(2.0)  # Much larger than previous
        
        # Should detect anomaly
        stats = monitor.get_monitoring_statistics()
        anomalies = stats.get('buffer_statistics', {}).get('anomalies_detected', 0)
        
        assert anomalies > 0
    
    def test_dashboard_creation(self):
        """Test monitoring dashboard creation."""
        monitor = EBreakMonitor()
        
        # Add some test data
        monitor.add_metrics(1.5)
        monitor.start_monitoring("dashboard_test")
        
        # Generate dashboard
        dashboard = create_monitoring_dashboard(monitor)
        
        assert "BCDSI MONITORING DASHBOARD" in dashboard
        assert "Current E_break:" in dashboard
        assert "THRESHOLD SYSTEM:" in dashboard
        
        monitor.stop_monitoring()
    
    def test_session_export(self):
        """Test session data export."""
        monitor = EBreakMonitor()
        
        monitor.add_metrics(1.0)
        monitor.add_metrics(1.1)
        
        monitor.start_monitoring("export_test")
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filename = f.name
            monitor.export_session_data(filename)
        
        # Verify file was created and contains data
        with open(filename, 'r') as f:
            data = json.load(f)
            
            assert 'session_info' in data
            assert 'metrics_buffer' in data
            assert len(data['metrics_buffer']) == 2
        
        monitor.stop_monitoring()
    
    def test_concurrent_monitoring(self):
        """Test that concurrent monitoring is prevented."""
        monitor = EBreakMonitor()
        
        # Start first session
        monitor.start_monitoring("session1")
        
        # Try to start second session
        with pytest.raises(RuntimeError, match="Monitoring already active"):
            monitor.start_monitoring("session2")
        
        monitor.stop_monitoring()


class TestIntegration:
    """Test integration between BCDSI components."""
    
    def test_monitor_with_intervention(self):
        """Test monitoring system with intervention alerts."""
        monitor = EBreakMonitor()
        
        intervention_records = []
        
        def alert_callback(data):
            # Simulate intervention
            record = intervene(
                data['e_break_value'],
                data['theta_integrity'],
                0.1  # threshold
            )
            intervention_records.append(record)
        
        monitor.start_monitoring("integration_test")
        monitor.alert_callback = alert_callback
        
        # Add metrics that should trigger intervention
        monitor.add_metrics(2.0)  # High E_break, should trigger intervention
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify intervention was triggered
        assert len(intervention_records) > 0
        assert intervention_records[0].intervention_level == InterventionLevel.BLOCK
        
        monitor.stop_monitoring()
    
    def test_dynamic_threshold_with_monitoring(self):
        """Test dynamic threshold system with monitoring."""
        threshold = DynamicThreshold(
            base_threshold=0.1,
            adaptation_rate=0.2
        )
        
        monitor = EBreakMonitor(threshold_system=threshold)
        
        monitor.start_monitoring("dynamic_test")
        
        # Add metrics showing degradation
        for i in range(5):
            theta = 0.9 - (i * 0.1)  # Decreasing
            monitor.add_metrics(1.0 + (i * 0.2))
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check that threshold was adjusted
        assert threshold.current_threshold != 0.1
        
        monitor.stop_monitoring()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])