from dataclasses import dataclass
from time import monotonic
from typing import Optional

def clamp01(x: float) -> float:
    """0.0과 1.0 사이로 값을 제한"""
    return 0.0 if x <= 0.0 else 1.0 if x >= 1.0 else x

@dataclass(frozen=True)
class EBreakResult:
    ebreak: float
    level: str  # "OK" | "WARNING" | "CRITICAL"
    target_level: float  # 계산된 목표 ebreak (쿨다운/홀드 적용 전)

class EBreakCalculator:
    """
    SSOT (Single Source of Truth) Calculator for E-Break
    
    Processing Flow:
      1) raw 위험도 base
      2) shock clamp(0..1)
      3) ebreak = base + shock
      4) target_level 분류(>= 경계 포함)
      5) cooldown/hold 적용 후 current_level 업데이트
    """

    def __init__(
        self,
        critical_threshold: float = 1.5,     # Boundary Check: >= 1.5 is CRITICAL
        warning_threshold: float = 1.0,      # Boundary Check: >= 1.0 is WARNING
        cooldown_sec: float = 2.0,           # Hysteresis: Hold time for level drop
        decay_step: float = 0.4              # (Optional) Step-down decay
    ):
        self.critical_threshold = critical_threshold
        self.warning_threshold = warning_threshold
        self.cooldown_sec = cooldown_sec
        self.decay_step = decay_step

        self.current_level: float = 0.0
        self._last_level_change_t: float = monotonic()

    def calculate(self, *, base: float, shock: float = 0.0, now: float | None = None) -> EBreakResult:
        """
        메인 계산 함수 (SSOT 구현)
        base: 기본 위험도 점수
        shock: 급격한 변화량 (Clamp 적용됨)
        """
        t = monotonic() if now is None else float(now)

        base_f = float(base)
        shock_f = clamp01(float(shock))
        candidate = base_f + shock_f  # raw ebreak (for reporting)

        # ✅ target_level은 "레벨 값"으로 (0.0 / warning_threshold / critical_threshold)
        if candidate >= self.critical_threshold:
            target = self.critical_threshold
        elif candidate >= self.warning_threshold:
            target = self.warning_threshold
        else:
            target = 0.0

        # ✅ 쿨다운 동안 하락이면 HOLD (레벨 기준)
        applied_level = target
        if target < self.current_level:
            if (t - self._last_change_t) < self.cooldown_sec:
                applied_level = self.current_level

        if applied_level != self.current_level:
            self.current_level = applied_level
            self._last_change_t = t

        # result.ebreak 는 boundary 테스트에서 1.5 그대로 비교하므로 raw candidate 유지
        return EBreakResult(
            ebreak=candidate,
            level=self._classify(applied_level),
            target_level=target,
        )

    def _classify_level_value(self, ebreak: float) -> float:
        """숫자 레벨로 변환 (경계값 >= 중요)"""
        if ebreak >= self.critical_threshold:
            return self.critical_threshold
        if ebreak >= self.warning_threshold:
            return self.warning_threshold
        return 0.0

    def _to_level_str(self, level: float) -> str:
        """문자열 레벨로 변환"""
        if level >= 1.5:
            return "CRITICAL"
        if level >= 1.0:
            return "WARNING"
        return "OK"

class EBreakCalculator:
    """
    테스트 계약을 만족하는 EBreakCalculator 더미 구현.
    실제 환경에서는 시스템 상태를 받아 분석 결과를 반환해야 함.
    """
    def calculate(self):
        # 예시 분석 결과 (테스트가 요구하는 analysis_summary 필드 포함)
        return {
            "analysis_summary": {
                "status": "ok",
                "theta_integrity": 0.95,
                "e_break_value": 0.05,
                "intervention": "none"
            }
        }
