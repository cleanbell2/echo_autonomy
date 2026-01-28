
import numpy as np
from typing import Union, Dict, Optional, Any, List
from dataclasses import dataclass, field

# [FIX 1] 순환 참조(자기 자신 import) 삭제함!
# [FIX 2] 하위 모듈 의존성 연결
from q_quantum.e_break_engine import EBreachEngine
from q_quantum.thermodynamic import thermodynamic_entropy
from q_quantum.coherence import coherence_measures
from q_quantum.non_unitarity import non_unitarity, bias_induction

__all__ = ['EBreakCalculator']

def _jsonable(x: Any) -> Any:
    """analysis_summary를 항상 JSON-serializable로 강제"""
    if isinstance(x, (np.floating, float)):
        return float(x)
    if isinstance(x, (np.integer, int)):
        return int(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, complex):
        return str(x)
    if isinstance(x, dict):
        return {k: _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x

class EBreakCalculator:
    """
    Integrated E_break calculator.
    Combines all metrics: ΔS + γ·TΣ + ΔC + ℕ(ε)
    """
    
    def __init__(self, gamma: float = 1.0, 
                 theta_integrity_threshold: float = 0.1,
                 tolerance: float = 1e-12):
        self.gamma = gamma
        self.theta_integrity_threshold = theta_integrity_threshold
        self.tolerance = tolerance
        # 엔진 초기화
        self.ebreak_engine = EBreachEngine(config={"tolerance": tolerance})
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
        
        try:
            # 복소수 행렬 변환
            rho = np.asarray(density_matrix, dtype=complex)
            rho_ref = np.asarray(reference_density_matrix, dtype=complex) if reference_density_matrix is not None else None
            
            # 1. 엔진 검증 (여기서 에러나면 catch로 감)
            self.ebreak_engine._validate_density_matrix(rho)
            
            # 2. 컴포넌트 계산 (물리학 로직)
            results = self._calculate_components(rho, rho_ref, work, free_energy_change, 
                                               quantum_channel, coherence_weight,
                                               non_unitarity_method, bias_method)
            
            # 3. 총점 계산
            ebreak_value = self._calculate_final_ebreak(results)
            results['e_break_qbn'] = ebreak_value
            
            # 4. 진단
            bcdsi_detected = self._detect_bcdsi(results)
            theta_integrity = self._calculate_theta_integrity(results)
            analysis_summary = self._generate_summary(results)
            
        except Exception as e:
            # 안전장치
            ebreak_value = -1.0
            theta_integrity = 0.0
            bcdsi_detected = False
            analysis_summary = {"error": str(e), "trace": "calculation_failed"}
            
        finally:
            # [FIX 3] JSON 직렬화 보장
            final_summary = _jsonable(analysis_summary)
            
            result = {
                "e_break_qbn": float(ebreak_value),
                "theta_integrity": float(theta_integrity),
                "bcdsi_detected": bool(bcdsi_detected),
                "analysis_summary": final_summary,
            }
            self.analysis_history.append(result)
            return result

    # 호환성 별칭 (calculate 호출 시 calculate_ebreak로 연결)
    def calculate(self, rho, echo_context=None):
        echo_context = echo_context or {}
        return self.calculate_ebreak(
            density_matrix=rho,
            work=echo_context.get("work", 0.0),
            free_energy_change=echo_context.get("free_energy_change", 0.0)
        )

    def _calculate_components(self, rho, rho_ref, work, free_energy_change, 
                              quantum_channel, coherence_weight, 
                              non_unitarity_method, bias_method):
        components = {}
        
        # Entropy
        vn_entropy = self.ebreak_engine.von_neumann_entropy(rho)
        components['von_neumann_entropy'] = vn_entropy
        
        if rho_ref is not None:
            vn_ref = self.ebreak_engine.von_neumann_entropy(rho_ref)
            components['delta_von_neumann_entropy'] = vn_entropy - vn_ref
        else:
            components['delta_von_neumann_entropy'] = vn_entropy
            
        # Thermo
        thermo = thermodynamic_entropy(work, free_energy_change, self.gamma)
        components['gamma_times_ts'] = thermo
        
        # Coherence
        coh = coherence_measures(rho, self.tolerance)
        delta_c = (1 - coherence_weight) * coh['l1_norm'] + coherence_weight * coh['relative_entropy']
        components['delta_c'] = delta_c
        components.update(coh)
        
        # Non-unitarity
        n_eps = 0.0
        if quantum_channel is not None:
            n_eps = non_unitarity(quantum_channel, non_unitarity_method, self.tolerance) + \
                    bias_induction(quantum_channel, bias_method)
        components['n_epsilon'] = n_eps
        
        return components

    def _calculate_final_ebreak(self, c):
        return float(c.get('delta_von_neumann_entropy', 0) + c.get('gamma_times_ts', 0) + 
                     c.get('delta_c', 0) + c.get('n_epsilon', 0))

    def _calculate_theta_integrity(self, r):
        score = 1.0
        if r.get('n_epsilon', 0) > 0.1: score -= 0.2
        return max(0.0, score)

    def _detect_bcdsi(self, r):
        return self._calculate_theta_integrity(r) < self.theta_integrity_threshold

    def _generate_summary(self, r):
        return {
            "E_break": r.get('e_break_qbn'),
            "dS": r.get('delta_von_neumann_entropy'),
            "dC": r.get('delta_c')
        }

if __name__ == "__main__":
    print("=== E_break Calculator Final Verification ===")
    calc = EBreakCalculator()
    
    # Test Case 1: Pure State
    rho1 = np.array([[1, 0], [0, 0]], dtype=complex)
    res1 = calc.calculate_ebreak(rho1, work=5.0, free_energy_change=2.0)
    print("\n[Test 1] Pure State Result:", res1)
    
    # Test Case 2: Mixed State
    rho2 = np.eye(2, dtype=complex) / 2
    res2 = calc.calculate_ebreak(rho2, work=5.0, free_energy_change=2.0)
    print("\n[Test 2] Mixed State Result:", res2)
