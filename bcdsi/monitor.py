"""
Real-time BCDSI monitoring system for E_break tracking.

Monitors quantum systems for BCDSI patterns and provides intervention alerts.
"""

from typing import List, Dict, Optional, Callable, Union
from dataclasses import dataclass, field
import numpy as np
import threading
import time
from datetime import datetime, timedelta
from collections import deque

from .intervention import intervene, InterventionLevel, InterventionRecord
from .threshold import DynamicThreshold, PolicyType, SystemCriticality


class EBreakMetrics:
    """E_break measurement with metadata."""
    e_break_value: float
    timestamp: float
    source: str = "unknown"
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class MonitoringSession:
    """Active monitoring session data."""
    session_id: str
    start_time: float
    threshold_system: DynamicThreshold
    alerts_count: int = 0
    interventions_count: int = 0
    status: str = "active"


class EBreakMonitor:
    """
    Real-time E_break monitoring with BCDSI detection and alerts.
    """
    
    def __init__(self, 
                 threshold_system: Optional[DynamicThreshold] = None,
                 session_duration: int = 3600,  # 1 hour in seconds
                 alert_callback: Optional[Callable] = None):
        """
        Initialize E_break monitor.
        
        Args:
            threshold_system: Dynamic threshold configuration
            session_duration: Maximum session duration in seconds
            alert_callback: Callback function for alerts
        """
        self.threshold_system = threshold_system or DynamicThreshold()
        self.session_duration = session_duration
        self.alert_callback = alert_callback
        
        # Monitoring state
        self.is_monitoring = False
        self.current_session: Optional[MonitoringSession] = None
        self.metrics_buffer: deque = deque(maxlen=1000)
        self.alert_history: List[Dict] = []
        
        # Statistics
        self.total_metrics_processed = 0
        self.total_alerts_generated = 0
        self.total_interventions_recommended = 0
        
        # Threading
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
    
    def start_monitoring(self, session_id: str = None) -> str:
        """
        Start real-time E_break monitoring.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session ID
        """
        if self.is_monitoring:
            raise RuntimeError("Monitoring already active")
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        # Create monitoring session
        self.current_session = MonitoringSession(
            session_id=session_id,
            start_time=time.time(),
            threshold_system=self.threshold_system
        )
        
        self.is_monitoring = True
        self.stop_event.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        return session_id
    
    def stop_monitoring(self) -> Dict:
        """
        Stop monitoring and return session statistics.
        
        Returns:
            Session summary statistics
        """
        if not self.is_monitoring:
            return {"status": "No active monitoring session"}
        
        # Signal stop
        self.stop_event.set()
        
        # Wait for thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        # Generate session summary
        if self.current_session:
            duration = time.time() - self.current_session.start_time
            summary = {
                "session_id": self.current_session.session_id,
                "duration_seconds": duration,
                "metrics_processed": self.total_metrics_processed,
                "alerts_generated": self.total_alerts_generated,
                "interventions_recommended": self.total_interventions_recommended,
                "final_threshold": self.threshold_system.current_threshold,
                "status": "completed"
            }
        else:
            summary = {"status": "No session data available"}
        
        self.is_monitoring = False
        self.current_session = None
        
        return summary
    
    def add_metrics(self, metrics: Union[EBreakMetrics, float, List[EBreakMetrics]]) -> None:
        """
        Add E_break metrics to monitoring buffer.
        
        Args:
            metrics: Single EBreakMetrics, float value, or list of metrics
        """
        if not self.is_monitoring:
            return
        
        # Normalize to list
        if isinstance(metrics, (int, float)):
            metrics_list = [EBreakMetrics(e_break_value=float(metrics), timestamp=time.time())]
        elif isinstance(metrics, EBreakMetrics):
            metrics_list = [metrics]
        else:
            metrics_list = metrics
        
        # Add to buffer
        for metric in metrics_list:
            self.metrics_buffer.append(metric)
            self.total_metrics_processed += 1
            
            # Check for immediate alerts
            self._check_immediate_alert(metric)
    
    def _monitor_loop(self) -> None:
        """
        Main monitoring loop running in separate thread.
        """
        check_interval = 1.0  # Check every second
        last_check_time = 0.0
        
        while not self.stop_event.is_set():
            current_time = time.time()
            
            # Check if enough time has passed
            if current_time - last_check_time >= check_interval:
                self._perform_monitoring_check()
                last_check_time = current_time
            
            # Small sleep to prevent busy waiting
            time.sleep(0.1)
    
    def _perform_monitoring_check(self) -> None:
        """
        Perform periodic monitoring checks.
        """
        if not self.current_session or not self.metrics_buffer:
            return
        
        # Get recent metrics
        recent_window = 10  # Last 10 measurements
        if len(self.metrics_buffer) < recent_window:
            return
        
        recent_metrics = list(self.metrics_buffer)[-recent_window:]
        
        # Calculate current E_break trend
        e_break_values = [m.e_break_value for m in recent_metrics]
        current_e_break = e_break_values[-1]
        
        # Calculate moving averages
        ma_5 = np.mean(e_break_values[-5:])
        ma_10 = np.mean(e_break_values[-10:])
        
        # Detect anomalies
        anomalies = self._detect_anomalies(e_break_values)
        
        # Calculate integrity and check threshold
        theta_integrity = self._calculate_current_integrity(current_e_break)
        threshold_breached = theta_integrity < self.threshold_system.current_threshold
        
        # Generate alert if needed
        if threshold_breached:
            alert_data = self._generate_alert(
                current_e_break, theta_integrity, anomalies, recent_metrics
            )
            self._handle_alert(alert_data)
    
    def _detect_anomalies(self, values: List[float]) -> List[bool]:
        """
        Detect anomalies in E_break values using statistical methods.
        
        Args:
            values: List of E_break values
            
        Returns:
            List of anomaly flags
        """
        if len(values) < 5:
            return [False] * len(values)
        
        anomalies = []
        
        # Z-score based anomaly detection
        mean_val = np.mean(values[:-1])  # Exclude current value
        std_val = np.std(values[:-1])
        current_val = values[-1]
        
        z_score = abs(current_val - mean_val) / (std_val + 1e-10)
        is_anomaly = abs(z_score) > 2.0
        
        anomalies.append(is_anomaly)
        
        # Fill remaining with False for consistency
        while len(anomalies) < len(values):
            anomalies.append(False)
        
        return anomalies
    
    def _calculate_current_integrity(self, e_break_value: float) -> float:
        """
        Calculate θ_integrity for current E_break value.
        
        Args:
            e_break_value: Current E_break^QBN value
            
        Returns:
            θ_integrity metric
        """
        # Simplified integrity calculation
        # In production, this would use actual E_break engine
        if e_break_value <= 0:
            return 0.0
        elif e_break_value <= 0.5:
            return 0.8
        elif e_break_value <= 1.0:
            return 0.6
        elif e_break_value <= 2.0:
            return 0.4
        else:
            return 0.2
    
    def _check_immediate_alert(self, metrics: EBreakMetrics) -> None:
        """
        Check if immediate alert is needed for single metric.
        
        Args:
            metrics: EBreakMetrics to check
        """
        # Critical threshold check
        theta_integrity = self._calculate_current_integrity(metrics.e_break_value)
        
        if theta_integrity < self.threshold_system.min_threshold:
            alert_data = self._generate_immediate_alert(metrics, theta_integrity)
            self._handle_alert(alert_data)
    
    def _generate_alert(self, current_e_break: float, theta_integrity: float,
                     anomalies: List[bool], recent_metrics: List[EBreakMetrics]) -> Dict:
        """
        Generate alert data structure.
        
        Args:
            current_e_break: Current E_break value
            theta_integrity: Current θ_integrity
            anomalies: Anomaly detection results
            recent_metrics: Recent metrics data
            
        Returns:
            Alert data structure
        """
        alert_data = {
            'timestamp': time.time(),
            'session_id': self.current_session.session_id if self.current_session else 'unknown',
            'e_break_value': current_e_break,
            'theta_integrity': theta_integrity,
            'threshold': self.threshold_system.current_threshold,
            'severity': self._calculate_alert_severity(theta_integrity),
            'anomalies_detected': sum(anomalies),
            'trend_direction': self._calculate_trend(recent_metrics),
            'recommended_action': self._recommend_action(theta_integrity, sum(anomalies))
        }
        
        return alert_data
    
    def _generate_immediate_alert(self, metrics: EBreakMetrics, theta_integrity: float) -> Dict:
        """
        Generate immediate alert for critical threshold breach.
        
        Args:
            metrics: Current metrics
            theta_integrity: Current integrity
            
        Returns:
            Immediate alert data
        """
        return {
            'timestamp': time.time(),
            'session_id': self.current_session.session_id if self.current_session else 'unknown',
            'type': 'critical_threshold_breach',
            'e_break_value': metrics.e_break_value,
            'theta_integrity': theta_integrity,
            'severity': 'critical',
            'recommended_action': 'IMMEDIATE_INTERVENTION'
        }
    
    def _calculate_alert_severity(self, theta_integrity: float) -> str:
        """
        Calculate alert severity based on θ_integrity.
        
        Args:
            theta_integrity: Current θ_integrity value
            
        Returns:
            Severity level string
        """
        if theta_integrity < self.threshold_system.min_threshold:
            return 'critical'
        elif theta_integrity < self.threshold_system.current_threshold * 0.5:
            return 'high'
        elif theta_integrity < self.threshold_system.current_threshold:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_trend(self, recent_metrics: List[EBreakMetrics]) -> str:
        """
        Calculate trend direction from recent metrics.
        
        Args:
            recent_metrics: Recent metrics list
            
        Returns:
            Trend direction string
        """
        if len(recent_metrics) < 3:
            return 'insufficient_data'
        
        values = [m.e_break_value for m in recent_metrics[-5:]]
        
        # Simple linear trend
        if len(values) >= 3:
            recent_avg = np.mean(values[-2:])
            earlier_avg = np.mean(values[-5:-3])
            
            if recent_avg > earlier_avg * 1.05:
                return 'increasing'
            elif recent_avg < earlier_avg * 0.95:
                return 'decreasing'
            else:
                return 'stable'
        
        return 'unknown'
    
    def _recommend_action(self, theta_integrity: float, anomalies_count: int) -> str:
        """
        Recommend action based on current state.
        
        Args:
            theta_integrity: Current θ_integrity
            anomalies_count: Number of anomalies detected
            
        Returns:
            Recommended action string
        """
        if anomalies_count > 2:
            return 'INVESTIGATE_SYSTEM'
        elif theta_integrity < self.threshold_system.min_threshold:
            return 'EMERGENCY_INTERVENTION'
        elif theta_integrity < self.threshold_system.current_threshold:
            return 'APPLY_CORRECTION'
        else:
            return 'CONTINUE_MONITORING'
    
    def _handle_alert(self, alert_data: Dict) -> None:
        """
        Handle generated alert.
        
        Args:
            alert_data: Alert information
        """
        # Store alert
        self.alert_history.append(alert_data)
        self.total_alerts_generated += 1
        
        # Check if intervention is recommended
        if alert_data.get('recommended_action') in ['EMERGENCY_INTERVENTION', 'IMMEDIATE_INTERVENTION', 'APPLY_CORRECTION']:
            self.total_interventions_recommended += 1
            if self.current_session:
                self.current_session.interventions_count += 1
        
        # Call custom alert callback if provided
        if self.alert_callback:
            try:
                self.alert_callback(alert_data)
            except Exception as e:
                print(f"Alert callback error: {e}")
    
    def get_monitoring_statistics(self) -> Dict:
        """
        Get comprehensive monitoring statistics.
        
        Returns:
            Monitoring statistics dictionary
        """
        if not self.is_monitoring:
            return {"status": "No active monitoring"}
        
        # Calculate buffer statistics
        if self.metrics_buffer:
            e_break_values = [m.e_break_value for m in self.metrics_buffer]
            current_e_break = e_break_values[-1] if e_break_values else 0.0
            
            buffer_stats = {
                'buffer_size': len(self.metrics_buffer),
                'e_break_current': current_e_break,
                'e_break_min': min(e_break_values),
                'e_break_max': max(e_break_values),
                'e_break_mean': np.mean(e_break_values),
                'e_break_std': np.std(e_break_values)
            }
        else:
            buffer_stats = {'buffer_size': 0}
        
        return {
            'status': 'monitoring',
            'session_duration': time.time() - self.current_session.start_time if self.current_session else 0,
            'threshold_stats': self.threshold_system.get_threshold_statistics(),
            'alert_history_count': len(self.alert_history),
            'total_metrics': self.total_metrics_processed,
            'total_alerts': self.total_alerts_generated,
            'total_interventions': self.total_interventions_recommended,
            'buffer_statistics': buffer_stats
        }
    
    def export_session_data(self, filename: str) -> None:
        """
        Export session data to file for analysis.
        
        Args:
            filename: Output filename
        """
        try:
            import json
            
            data = {
                'session_info': self.current_session.__dict__ if self.current_session else {},
                'threshold_system': self.threshold_system.__dict__,
                'metrics_buffer': [
                    {
                        'e_break_value': m.e_break_value,
                        'timestamp': m.timestamp,
                        'source': m.source
                    } for m in self.metrics_buffer
                ],
                'alert_history': self.alert_history,
                'statistics': self.get_monitoring_statistics()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Export failed: {e}")


def create_monitoring_dashboard(monitor: EBreakMonitor) -> str:
    """
    Create a text-based dashboard for monitoring display.
    
    Args:
        monitor: EBreakMonitor instance
        
    Returns:
        Formatted dashboard string
    """
    stats = monitor.get_monitoring_statistics()
    
    dashboard = f"""
╔════════════════════════════════════════════╗
║              BCDSI MONITORING DASHBOARD              ║
╠════════════════════════════════════════════╣
║ Status: {stats.get('status', 'N/A').upper():<20} ║
║ Session: {stats.get('session_info', {}).get('session_id', 'N/A'):<20} ║
║ Duration: {stats.get('session_duration', 0):>10.1f}s{'':>11} ║
╠════════════════════════════════════════════╣
║ METRICS                                      ║
║ Current E_break: {stats.get('buffer_statistics', {}).get('e_break_current', 0.0):>12.6f}              ║
║ Buffer Size: {stats.get('buffer_statistics', {}).get('buffer_size', 0):>12}               ║
║ Range: [{stats.get('buffer_statistics', {}).get('e_break_min', 0.0):>8.3f}, {stats.get('buffer_statistics', {}).get('e_break_max', 0.0):>8.3f}]         ║
║ Alerts: {stats.get('total_alerts', 0):>12}                             ║
║ Interventions: {stats.get('total_interventions', 0):>12}                     ║
╠════════════════════════════════════════════╣
║ THRESHOLD SYSTEM                              ║
║ Current: {stats.get('threshold_stats', {}).get('current_threshold', 0.0):>12.6f}          ║
║ Policy: {stats.get('threshold_stats', {}).get('policy', 'N/A'):>12}                   ║
║ Stability: {stats.get('threshold_stats', {}).get('stability_score', 0.0):>12.6f}           ║
╚════════════════════════════════════════════════╝
    """
    
    return dashboard