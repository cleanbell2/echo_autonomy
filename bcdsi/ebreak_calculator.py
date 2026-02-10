from __future__ import annotations

from dataclasses import dataclass
from time import monotonic


def clamp01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return x


@dataclass(frozen=True)
class EBreakResult:
    @property
    def analysis_summary(self):
        # 레거시 테스트 호환: dict 형태로 반환
        return {
            "ebreak": self.ebreak,
            "level": self.level,
            "target_level": self.target_level,
        }

    ebreak: float          # 원시 계산값 (Candidate)
    level: str             # "OK" | "WARNING" | "CRITICAL"
    target_level: float    # 레벨별 대표값 (0.0, 1.0, 1.5)

    def __getitem__(self, key):
        # 레거시 테스트 호환: dict-like access
        return getattr(self, key)


class EBreakCalculator:
    """
    SSOT (Single Source of Truth) Calculator for E-Break
    """

    def __init__(
        self,
        *,
        critical_threshold: float = 1.5,
        warning_threshold: float = 1.0,
        cooldown_sec: float = 0.0,
    ) -> None:
        self.critical_threshold = float(critical_threshold)
        self.warning_threshold = float(warning_threshold)
        self.cooldown_sec = float(cooldown_sec)

        self.current_level: float = 0.0
        self._last_change_t: float = monotonic()

    # [Fix] base와 shock에 기본값(0.0)을 추가하여 테스트 호환성 확보
    def calculate(self, *, base: float = 0.0, shock: float = 0.0, now: float | None = None) -> EBreakResult:
        t = monotonic() if now is None else float(now)

        base_f = float(base)
        shock_f = clamp01(float(shock))
        candidate = base_f + shock_f  # raw ebreak candidate

        # ✅ [Target Level 결정]
        if candidate >= self.critical_threshold:
            target_level = self.critical_threshold
        elif candidate >= self.warning_threshold:
            target_level = self.warning_threshold
        else:
            target_level = 0.0

        # ✅ [Cooldown Logic]
        applied_level = target_level
        if target_level < self.current_level:
            if (t - self._last_change_t) < self.cooldown_sec:
                applied_level = self.current_level

        # ✅ [State Update]
        if applied_level != self.current_level:
            self.current_level = applied_level
            self._last_change_t = t

        return EBreakResult(
            ebreak=candidate,
            level=self._classify(applied_level),
            target_level=target_level,
        )

    def _classify(self, level_val: float) -> str:
        if level_val >= self.critical_threshold:
            return "CRITICAL"
        if level_val >= self.warning_threshold:
            return "WARNING"
        return "OK"
