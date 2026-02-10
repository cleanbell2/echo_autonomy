from __future__ import annotations

import numpy as np
from typing import Optional, Dict, Any

__all__ = [
    "von_neumann_entropy",
    "EBreachEngine",
    "EBreakEngine",
    "get_engine_instance",
]

def von_neumann_entropy(rho: np.ndarray) -> float:
    """
    양자 상태 rho의 von Neumann 엔트로피 계산: S = -Tr(rho * log(rho))
    """
    # [FIX] dtype=float 제거 -> 복소수 유지
    rho = np.asarray(rho)
    
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError(f"rho must be a square 2D matrix, got shape={rho.shape}")

    # 수치 안정성: Hermitian화
    rho = 0.5 * (rho + rho.conj().T)
    
    # 고유값 분해 (Hermitian이므로 eigvalsh 사용 가능, 결과는 실수)
    eigenvalues = np.linalg.eigvalsh(rho)
    
    # 0보다 큰 고유값만 사용 (log(0) 방지)
    eigenvalues = eigenvalues[eigenvalues > 1e-12]
    
    if eigenvalues.size == 0:
        return 0.0
        
    # 결과는 실수여야 함
    return float(-np.sum(eigenvalues * np.log(eigenvalues)))


class EBreachEngine:
    """
    Δ-Log Macro Pulse의 핵심인 E_break 지수를 계산하는 엔진.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not isinstance(config, dict):
            config = {}
        self.config = config
        self.min_e_break = float(self.config.get("min_e_break", 0.0))
        self.max_e_break = float(self.config.get("max_e_break", 1.0))

    def _validate_density_matrix(self, rho: np.ndarray) -> None:
        if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
            raise ValueError(f"rho must be a square 2D matrix, got shape={rho.shape}")

    def von_neumann_entropy(self, rho: np.ndarray) -> float:
        return von_neumann_entropy(rho)

    def calculate_e_break(
        self,
        rho: np.ndarray,
        work: float,
        free_energy_change: float,
        temperature: float = 1.0,
    ) -> float:
        if temperature <= 0:
            temperature = 1.0

        entropy = self.von_neumann_entropy(rho)
        dissipation = max(0.0, float(work) - float(free_energy_change))

        if entropy < 1e-10:
            e_break = 1.0 if dissipation > 0 else 0.0
        else:
            eps = 1e-5
            e_break = 1.0 - float(np.exp(-(dissipation / (temperature * (entropy + eps)))))

        return float(np.clip(e_break, self.min_e_break, self.max_e_break))

    def evaluate_integrity(self, e_break: float, theta_threshold: float) -> bool:
        return float(e_break) > float(theta_threshold)

    # 호환성 API
    def calculate(self, **kwargs) -> Dict[str, Any]:
        rho = kwargs.get("density_matrix")
        if rho is None: rho = kwargs.get("rho")
        work = kwargs.get("work", 0.0)
        free_energy = kwargs.get("free_energy_change", 0.0)
        temp = kwargs.get("temperature", 1.0)
        
        if rho is None: return {"error": "Density matrix required"}

        e_break = self.calculate_e_break(rho, work, free_energy, temp)
        theta = float(kwargs.get("theta_integrity", 1.0))
        
        return {
            "e_break_qbn": e_break,
            "theta_integrity": theta,
            "bcdsi_detected": self.evaluate_integrity(e_break, theta),
            "analysis_summary": {
                "entropy": von_neumann_entropy(rho),
                "dissipation": max(0.0, float(work) - float(free_energy)),
            }
        }

    def compute(self, **kwargs):
        return self.calculate(**kwargs)

EBreakEngine = EBreachEngine
def get_engine_instance(): return EBreachEngine()
