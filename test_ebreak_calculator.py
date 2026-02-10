import pytest
import time
from bcdsi.ebreak_calculator import EBreakCalculator

class TestEBreakCalculator:
    def test_ebreak_boundary_critical(self):
        """[검증 1] 경계값: 정확히 1.5일 때 CRITICAL(Block)이 떠야 함 (>= 적용 확인)"""
        # 임계값: Warning=1.0, Critical=1.5
        calc = EBreakCalculator(critical_threshold=1.5, warning_threshold=1.0)
        
        # 1.5 입력 (Base 1.5 + Shock 0.0)
        result = calc.calculate(base=1.5, shock=0.0)
        
        # 기대: 1.5는 Critical에 포함되어야 함 (>=)
        assert result.ebreak == 1.5
        assert result.level == "CRITICAL", f"Expected CRITICAL at 1.5, but got {result.level}"
        assert result.target_level == 1.5

    def test_ebreak_cooldown_hold(self):
        """[검증 2] 쿨다운: 위험도가 떨어져도 쿨다운 중에는 레벨 유지 (Hold 확인)"""
        # 쿨다운 1초 설정
        calc = EBreakCalculator(cooldown_sec=1.0)
        
        # 1. 먼저 CRITICAL로 올림 (상승은 즉시 반영)
        calc.calculate(base=2.0)
        assert calc.current_level == 1.5  # CRITICAL 레벨 값(1.5) 상태
        
        # 2. 바로 0.0으로 낮춤 (쿨다운 시간 안지남)
        # 이때 target은 0.0이지만, applied(current_level)은 1.5로 유지되어야 함
        res = calc.calculate(base=0.0)
        
        assert res.target_level == 0.0  # 목표는 0.0이었으나
        assert calc.current_level == 1.5, "Cooldown failed: Level dropped immediately"

        # 3. 쿨다운 후 (1.1초 대기)
        time.sleep(1.1)
        calc.calculate(base=0.0)
        # 이제 떨어져야 함
        assert calc.current_level < 1.5, "Decay failed: Level stuck after cooldown"

    def test_ebreak_shock_clamp(self):
        """[검증 3] 쇼크 클램프: 충격이 아무리 커도(2.5) 최대 1.0만 반영되어야 함"""
        calc = EBreakCalculator()
        
        # Base 1.0 + Shock 2.5 
        # -> Shock는 내부에서 1.0으로 잘려야(Clamp) 함
        # -> ebreak = 1.0 + 1.0 = 2.0
        result = calc.calculate(base=1.0, shock=2.5)
        
        assert result.ebreak == 2.0, f"Clamp failed: Expected 2.0, got {result.ebreak}"
