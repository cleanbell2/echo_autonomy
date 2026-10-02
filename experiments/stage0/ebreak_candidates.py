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
    γ·TΣ  = γ (W − ΔF)                      W: 스텝 비용, ΔF: 목표 진척 (같은 단위로 정규화)

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


def anchor_overlap(rho: np.ndarray, anchors: np.ndarray) -> float:
    """Tr(P_A ρ): ρ 가 앵커 부분공간 안에 있는 비율 (Q_quantum 의 공명 항과 연결 가능)."""
    q, _ = np.linalg.qr(np.asarray(anchors, float).T)
    return float(np.trace(q.T @ rho @ q).real)


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
    delta_s: float
    gamma_t_sigma: float
    delta_c: float
    n_epsilon: float
    anchor_overlap: Optional[float] = None

    @property
    def e_break(self) -> float:
        return self.delta_s + self.gamma_t_sigma + self.delta_c + self.n_epsilon


def e_break_terms(rho_prev: np.ndarray, rho_now: np.ndarray, *,
                  work: float = 0.0, delta_free_energy: float = 0.0, gamma: float = 1.0,
                  basis: Optional[np.ndarray] = None,
                  anchors: Optional[np.ndarray] = None) -> EBreakTerms:
    for name, v in (("work", work), ("delta_free_energy", delta_free_energy), ("gamma", gamma)):
        if not math.isfinite(v):
            raise ValueError(f"{name} 비유한")
    return EBreakTerms(
        delta_s=von_neumann_entropy(rho_now) - von_neumann_entropy(rho_prev),
        gamma_t_sigma=gamma * (work - delta_free_energy),
        delta_c=coherence_rel_entropy(rho_now, basis) - coherence_rel_entropy(rho_prev, basis),
        n_epsilon=non_unitarity(rho_prev, rho_now),
        anchor_overlap=None if anchors is None else anchor_overlap(rho_now, anchors),
    )


def theta_integrity(e_break: float) -> float:
    """θ = 1/(1+max(0,E)) — bcdsi.calculate_theta_integrity 의 기본항과 같은 형태.
    E_break 가 커질수록 단조 감소 (기존 4항 엔진의 방향 역전 문제 없음)."""
    if not math.isfinite(e_break):
        return 0.0                                  # fail-closed
    return 1.0 / (1.0 + max(0.0, e_break))
