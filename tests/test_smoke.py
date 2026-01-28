import pytest
import numpy as np
from q_quantum import (
    EBreakCalculator, 
    CONTRACT, 
    EBreakMonitor,  # 이게 import 되어야 함 (방금 복구한 파일)
    BcdsiIntervenor
)

def test_core_contract_lock():
    """1. 코어 헌법(CONTRACT) 잠금 확인"""
    assert CONTRACT['entrypoint'] == "EBreakCalculator.calculate_ebreak()"
    assert "e_break_qbn" in CONTRACT['required_returns']
    print("\n✅ Contract Lock: Secured")

def test_monitor_resurrection():
    """2. 모니터링 시스템 부활 확인"""
    monitor = EBreakMonitor(threshold=0.85)
    monitor.start()
    assert monitor.is_running is True
    
    # 데이터 주입 테스트
    is_danger = monitor.analyze_trend(0.9) # 임계값 초과
    assert is_danger is True
    
    monitor.stop()
    assert monitor.is_running is False
    print("\n✅ Monitor Pulse: Active")

def test_calculation_pipeline():
    """3. 통합 계산 파이프라인 확인"""
    calc = EBreakCalculator()
    
    # 더미 데이터로 계산 시도
    rho = np.array([[1, 0], [0, 0]])
    result = calc.calculate_ebreak(
        density_matrix=rho,
        work=10.0,
        free_energy_change=5.0
    )
    
    assert result['e_break_qbn'] >= 0.0
    assert result['bcdsi_detected'] in [True, False]
    print("\n✅ Calculation Engine: Operational")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
