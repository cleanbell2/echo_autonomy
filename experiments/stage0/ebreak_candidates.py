# -*- coding: utf-8 -*-
"""
Stage 0 — E_break^QBN 운영 정의 후보 (참조 구현, 실행 경로 미연결).

목표: 에이전트의 관측 가능한 신호로 '진짜' 밀도행렬 ρ 를 만들고,
      ΔS · ΔC · ℕ(ε) 를 양자정보 정의 그대로 계산한다. 비유 금지.

    E_break^QBN = ΔS + γ·TΣ + ΔC + ℕ(ε)

후보 B (semantic ρ):
    한 스텝에서 에이전트가 고려한 K개 후보 행동 a_i (샘플링 빈도 또는 logprob → p_i)
    각 행동 텍스트의 단위 임베딩 |e_i⟩ ∈ R^d
        ρ = Σ_i p_i |e_i⟩⟨e_i|          (Tr ρ = 1, ρ ⪰ 0 이 구성상 보장)
후보 A (classical ρ):
    같은 p_i, 임베딩을 서로 직교로 취급 → ρ = diag(p).  B 의 절제(ablation) 대조군.

항 정의 (t-1 → t):
    ΔS    = S(ρ_t) − S(ρ_{t-1}),             S(ρ) = −Tr ρ ln ρ
    ΔC    = C_rel(ρ_t) − C_rel(ρ_{t-1}),     C_rel(ρ) = S(Δ_B(ρ)) − S(ρ)  (앵커 기저 B 에서 탈위상)
    ℕ(ε)  = min_U ½‖ρ_t − U ρ_{t-1} U†‖₁ = ½ Σ_k |λ↓_k(ρ_t) − λ↓_k(ρ_{t-1})|
            → 관측된 전이를 '어떤 유니터리로도' 설명할 수 없는 정도 (유니터리면 정확히 0)
    γ·TΣ_proxy = γ (cost − progress)        대리 지표. 물리적 W−ΔF 로 검증된 값 아님 (D3)

ℕ(ε) 의 등식은 유니터리 궤도 위 trace-norm 최소 거리 = 고유값 정렬 차의 ℓ1 (Mirsky 정리).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

_EPS = 1e-12


# ---------------------------------------------------------------- 상태 구성
@dataclass(frozen=True)
class AgentStep:
    """한 스텝의 관측. probs 는 합 1, embeddings 는 (K, d)."""
    probs: np.ndarray
    embeddings: np.ndarray

    def __post_init__(self):
        p = np.asarray(self.probs, dtype=float)
        e = np.asarray(self.embeddings, dtype=float)
        if p.ndim != 1 or e.ndim != 2 or len(p) != e.shape[0]:
            raise ValueError("probs (K,) 와 embeddings (K,d) 크기 불일치")
        if np.any(p < -_EPS) or not math.isclose(float(p.sum()), 1.0, abs_tol=1e-9):
            raise ValueError("probs 는 음수가 없고 합이 1 이어야 함")
        if not np.all(np.isfinite(e)) or np.any(np.linalg.norm(e, axis=1) < _EPS):
            raise ValueError("embeddings 에 0 벡터 또는 비유한 값")


def _unit(e: np.ndarray) -> np.ndarray:
    return e / np.linalg.norm(e, axis=1, keepdims=True)


def rho_semantic(step: AgentStep) -> np.ndarray:
    """후보 B: ρ = Σ p_i |e_i⟩⟨e_i|  (d×d)."""
    e = _unit(np.asarray(step.embeddings, float))
    p = np.asarray(step.probs, float)
    return (e.T * p) @ e


def rho_classical(step: AgentStep) -> np.ndarray:
    """후보 A: ρ = diag(p)  (K×K). 임베딩 정보를 버린 대조군."""
    return np.diag(np.asarray(step.probs, float))


# ---------------------------------------------------------------- 양자정보 양
def _check_density(rho: np.ndarray) -> None:
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("ρ 는 정사각행렬")
    if not np.allclose(rho, rho.conj().T, atol=1e-9):
        raise ValueError("ρ 는 에르미트")
    if not math.isclose(float(np.trace(rho).real), 1.0, abs_tol=1e-9):
        raise ValueError("Tr ρ = 1")
    if np.linalg.eigvalsh(rho).min() < -1e-9:
        raise ValueError("ρ ⪰ 0")


def spectrum(rho: np.ndarray) -> np.ndarray:
    _check_density(rho)
    lam = np.clip(np.linalg.eigvalsh(rho).real, 0.0, None)
    return np.sort(lam)[::-1]


def von_neumann_entropy(rho: np.ndarray) -> float:
    lam = spectrum(rho)
    lam = lam[lam > _EPS]
    return float(-(lam * np.log(lam)).sum())


def orthonormal_basis(anchors: np.ndarray, dim: int) -> np.ndarray:
    """앵커 벡터를 Gram-Schmidt 로 정규직교화하고 나머지를 보완해 완전 기저(dim×dim)를 만든다.
    앞쪽 열이 앵커 방향. 앵커가 선형종속이면 ValueError."""
    a = np.asarray(anchors, float)
    if a.ndim != 2 or a.shape[1] != dim:
        raise ValueError("anchors 는 (m, dim)")
    q, r = np.linalg.qr(a.T)
    if np.any(np.abs(np.diag(r)) < 1e-9):
        raise ValueError("앵커가 선형종속")
    full, _ = np.linalg.qr(np.hstack([q, np.eye(dim)]))   # 앞 m 열 = ±앵커 방향
    return full


def coherence_rel_entropy(rho: np.ndarray, basis: Optional[np.ndarray] = None) -> float:
    """C_rel(ρ) = S(Δ_B(ρ)) − S(ρ). basis 열벡터가 기준 기저(None 이면 계산 기저)."""
    _check_density(rho)
    r = rho if basis is None else basis.T @ rho @ basis
    dephased = np.diag(np.diag(r).real)
    return von_neumann_entropy(dephased) - von_neumann_entropy(r)


def _anchor_projector(anchors: np.ndarray, dim: int) -> np.ndarray:
    a = np.asarray(anchors, float)
    if a.ndim != 2 or a.shape[1] != dim:
        raise ValueError("anchors 는 (m, dim)")
    q, r = np.linalg.qr(a.T)
    if np.any(np.abs(np.diag(r)) < 1e-9):
        raise ValueError("앵커가 선형종속")
    return q @ q.T


def anchor_dephase(rho: np.ndarray, anchors: np.ndarray) -> np.ndarray:
    """D2: 앵커 투영 측정 {P_A, I−P_A} 에 대한 탈위상 Δ_P(ρ) = P ρ P + (I−P) ρ (I−P).
    여공간 기저 선택과 무관하다 (기저 전체 탈위상의 임의성 제거)."""
    _check_density(rho)
    p = _anchor_projector(anchors, rho.shape[0])
    q = np.eye(rho.shape[0]) - p
    return p @ rho @ p + q @ rho @ q


def coherence_anchor(rho: np.ndarray, anchors: np.ndarray) -> float:
    """C_P(ρ) = S(Δ_P(ρ)) − S(ρ) ≥ 0 : 앵커/비앵커 부분공간 사이의 코히런스.
    주의: ΔS + ΔC_P = ΔS(Δ_P ρ) 이므로 두 항의 독립 기여를 주장하지 않는다."""
    return von_neumann_entropy(anchor_dephase(rho, anchors)) - von_neumann_entropy(rho)


def anchor_overlap(rho: np.ndarray, anchors: np.ndarray) -> float:
    """Tr(P_A ρ): ρ 가 앵커 부분공간 안에 있는 비율. 순수 상태에서 cos²Δθ."""
    return float(np.trace(_anchor_projector(anchors, rho.shape[0]) @ rho).real)


def non_unitarity(rho_prev: np.ndarray, rho_now: np.ndarray) -> float:
    """ℕ(ε) = min_U ½‖ρ_now − U ρ_prev U†‖₁ = ½ Σ |λ↓(ρ_now) − λ↓(ρ_prev)|."""
    a, b = spectrum(rho_now), spectrum(rho_prev)
    n = max(len(a), len(b))
    a = np.pad(a, (0, n - len(a)))
    b = np.pad(b, (0, n - len(b)))
    return float(0.5 * np.abs(a - b).sum())


# ---------------------------------------------------------------- E_break
@dataclass(frozen=True)
class EBreakTerms:
    delta_s: float                  # D5: 부호 있는 원래 값 (본안)
    gamma_t_sigma_proxy: float      # D3: γ(비용 − 진척). 물리량 W−ΔF 가 아닌 대리 지표
    delta_c: float
    n_epsilon: float
    anchor_overlap: Optional[float] = None

    @property
    def e_break(self) -> float:
        """본안 (D5): 부호 있는 ΔS."""
        return self.delta_s + self.gamma_t_sigma_proxy + self.delta_c + self.n_epsilon

    @property
    def e_break_clamped(self) -> float:
        """D5 비교 변형: ΔS 만 max(0, ΔS)."""
        return max(0.0, self.delta_s) + self.gamma_t_sigma_proxy + self.delta_c + self.n_epsilon


def e_break_terms(rho_prev: np.ndarray, rho_now: np.ndarray, *,
                  cost_proxy: float = 0.0, progress_proxy: float = 0.0, gamma: float = 1.0,
                  anchors: Optional[np.ndarray] = None,
                  basis: Optional[np.ndarray] = None) -> EBreakTerms:
    """anchors 가 있으면 ΔC 는 앵커 투영 탈위상(D2), 없으면 basis(기본: 계산 기저) 탈위상."""
    for name, v in (("cost_proxy", cost_proxy), ("progress_proxy", progress_proxy), ("gamma", gamma)):
        if not math.isfinite(v):
            raise ValueError(f"{name} 비유한")
    if anchors is not None:
        c = lambda r: coherence_anchor(r, anchors)
    else:
        c = lambda r: coherence_rel_entropy(r, basis)
    return EBreakTerms(
        delta_s=von_neumann_entropy(rho_now) - von_neumann_entropy(rho_prev),
        gamma_t_sigma_proxy=gamma * (cost_proxy - progress_proxy),
        delta_c=c(rho_now) - c(rho_prev),
        n_epsilon=non_unitarity(rho_prev, rho_now),
        anchor_overlap=None if anchors is None else anchor_overlap(rho_now, anchors),
    )


def theta_integrity(e_break: float) -> float:
    """D4: θ = 1/(1+max(0,E)). E 에 대해 단조 감소. 비유한 입력은 0 (fail-closed)."""
    if not math.isfinite(e_break):
        return 0.0
    return 1.0 / (1.0 + max(0.0, e_break))


def q_quantum(rho_now: np.ndarray, anchors: np.ndarray, e_break: float) -> float:
    """D6: Q = cosΔθ · e^{−σ²/2},  cosΔθ = √Tr(P_A ρ),  σ² = max(0, E_break).
    E_break 는 스펙트럼 불변량이라 유니터리 회전(의미 방향 이탈)을 못 본다. 그 역할은 Q 가 맡는다."""
    if not math.isfinite(e_break):
        return 0.0
    ov = min(1.0, max(0.0, anchor_overlap(rho_now, anchors)))
    return math.sqrt(ov) * math.exp(-max(0.0, e_break) / 2.0)


@dataclass(frozen=True)
class GateDecision:
    approve: bool
    theta: float
    q: float
    reason: str


def gate(theta: float, q: float, *, theta_min: float, q_min: float) -> GateDecision:
    """D6 이중 게이트: θ ≥ θ_min 그리고 Q ≥ Q_min 일 때만 승인.
    임계값은 기본값 없음 — 실험 전 사전 등록해서 넘겨야 한다."""
    for n, v in (("theta", theta), ("q", q), ("theta_min", theta_min), ("q_min", q_min)):
        if not math.isfinite(v):
            return GateDecision(False, theta, q, f"{n} 비유한 (fail-closed)")
    fails = [n for n, ok in (("theta", theta >= theta_min), ("q_quantum", q >= q_min)) if not ok]
    return GateDecision(not fails, theta, q, "approve" if not fails else "block: " + ", ".join(fails))


def rho_semantic_dephased(step: AgentStep, anchors: np.ndarray) -> np.ndarray:
    """D1 대조군: 후보 B 와 같은 의미 정보, 앵커 투영 코히런스만 제거한 ρ."""
    return anchor_dephase(rho_semantic(step), anchors)
