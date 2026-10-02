# -*- coding: utf-8 -*-
"""Stage 0 참조 구현의 수학적 성질 검증. 정의가 양자정보 의미를 지키는지 확인한다."""
import math

import numpy as np
import pytest

from experiments.stage0.ebreak_candidates import (
    AgentStep, anchor_overlap, coherence_rel_entropy, e_break_terms, non_unitarity,
    orthonormal_basis, rho_classical, rho_semantic, spectrum, theta_integrity,
    von_neumann_entropy,
)

LN2 = math.log(2)
rng = np.random.default_rng(7)


def rand_step(k=4, d=6):
    p = rng.random(k); p /= p.sum()
    return AgentStep(p, rng.normal(size=(k, d)))


def haar_unitary(d):
    z = rng.normal(size=(d, d))
    q, r = np.linalg.qr(z)
    return q * np.sign(np.diag(r))


# ---------- ρ 가 진짜 밀도행렬인가
@pytest.mark.parametrize("build", [rho_semantic, rho_classical])
def test_rho_is_density_matrix(build):
    for _ in range(20):
        rho = build(rand_step())
        assert np.allclose(rho, rho.T)
        assert math.isclose(np.trace(rho), 1.0, abs_tol=1e-9)
        assert np.linalg.eigvalsh(rho).min() > -1e-9


def test_input_contract():
    with pytest.raises(ValueError):
        AgentStep([0.5, 0.6], np.eye(2))               # 합 ≠ 1
    with pytest.raises(ValueError):
        AgentStep([0.5, 0.5], np.array([[1, 0], [0, 0]]))   # 0 벡터
    with pytest.raises(ValueError):
        AgentStep([1.0], np.eye(2))                     # 크기 불일치


# ---------- 엔트로피 기준값
def test_entropy_reference_values():
    assert von_neumann_entropy(np.diag([1.0, 0.0])) == pytest.approx(0.0)
    assert von_neumann_entropy(np.eye(2) / 2) == pytest.approx(LN2)
    assert von_neumann_entropy(np.eye(4) / 4) == pytest.approx(math.log(4))


def test_classical_candidate_is_shannon():
    p = np.array([0.5, 0.25, 0.25])
    shannon = -(p * np.log(p)).sum()
    assert von_neumann_entropy(rho_classical(AgentStep(p, np.eye(3)))) == pytest.approx(shannon)


def test_semantic_equals_classical_when_embeddings_orthogonal():
    p = np.array([0.6, 0.3, 0.1])
    s = AgentStep(p, np.eye(3))
    assert von_neumann_entropy(rho_semantic(s)) == pytest.approx(von_neumann_entropy(rho_classical(s)))


def test_parallel_paraphrases_have_zero_semantic_entropy():
    """같은 의미(평행 임베딩)의 서로 다른 문자열: A 는 불확실성으로, B 는 0 으로 본다."""
    v = np.array([[1.0, 0, 0], [2.0, 0, 0], [0.5, 0, 0]])
    s = AgentStep(np.ones(3) / 3, v)
    assert von_neumann_entropy(rho_semantic(s)) == pytest.approx(0.0, abs=1e-9)
    assert von_neumann_entropy(rho_classical(s)) == pytest.approx(math.log(3))


# ---------- 코히런스
def test_coherence_plus_state_is_ln2():
    plus = np.full((2, 2), 0.5)
    assert coherence_rel_entropy(plus) == pytest.approx(LN2)
    assert coherence_rel_entropy(np.eye(2) / 2) == pytest.approx(0.0)


def test_coherence_is_basis_dependent_and_nonnegative():
    plus = np.full((2, 2), 0.5)
    hadamard_basis = orthonormal_basis(np.array([[1.0, 1.0]]), 2)
    assert coherence_rel_entropy(plus, hadamard_basis) == pytest.approx(0.0, abs=1e-9)
    for _ in range(20):
        assert coherence_rel_entropy(rho_semantic(rand_step())) >= -1e-9


def test_basis_contains_anchor_direction():
    a = np.array([[1.0, 2.0, 2.0]])
    b = orthonormal_basis(a, 3)
    assert np.allclose(b.T @ b, np.eye(3), atol=1e-9)
    assert abs(abs(b[:, 0] @ (a[0] / np.linalg.norm(a[0]))) - 1) < 1e-9
    with pytest.raises(ValueError):
        orthonormal_basis(np.array([[1.0, 0, 0], [2.0, 0, 0]]), 3)


def test_anchor_overlap_bounds():
    rho = rho_semantic(rand_step(d=5))
    a = rng.normal(size=(2, 5))
    assert -1e-9 <= anchor_overlap(rho, a) <= 1 + 1e-9
    assert anchor_overlap(rho, np.eye(5)) == pytest.approx(1.0)


# ---------- ℕ(ε): 유니터리면 0, 아니면 양수, 대칭, 삼각부등식
def test_non_unitarity_zero_for_any_unitary_evolution():
    for _ in range(20):
        rho = rho_semantic(rand_step(d=5))
        u = haar_unitary(5)
        assert non_unitarity(rho, u @ rho @ u.T) == pytest.approx(0.0, abs=1e-9)


def test_non_unitarity_positive_for_dephasing_and_bounded():
    plus = np.full((2, 2), 0.5)
    dephased = np.eye(2) / 2
    n = non_unitarity(plus, dephased)
    assert n == pytest.approx(0.5)
    for _ in range(20):
        a, b = rho_semantic(rand_step(d=4)), rho_semantic(rand_step(d=4))
        assert 0 <= non_unitarity(a, b) <= 1 + 1e-9
        assert non_unitarity(a, b) == pytest.approx(non_unitarity(b, a))


def test_non_unitarity_is_min_over_unitaries():
    """Mirsky: 임의 유니터리 U 에 대해 ½‖ρ₁−Uρ₀U†‖₁ ≥ ℕ. 즉 ℕ 은 진짜 최솟값."""
    a, b = rho_semantic(rand_step(d=4)), rho_semantic(rand_step(d=4))
    n = non_unitarity(a, b)
    for _ in range(200):
        u = haar_unitary(4)
        d = 0.5 * np.abs(np.linalg.eigvalsh(b - u @ a @ u.T)).sum()
        assert d >= n - 1e-9


# ---------- E_break 조립과 θ
def test_identical_steps_give_zero_ebreak():
    s = rand_step()
    rho = rho_semantic(s)
    t = e_break_terms(rho, rho)
    assert (t.delta_s, t.delta_c, t.n_epsilon, t.gamma_t_sigma) == pytest.approx((0, 0, 0, 0), abs=1e-9)
    assert t.e_break == pytest.approx(0.0, abs=1e-9)


def test_thermo_term_is_gamma_w_minus_df():
    rho = np.eye(2) / 2
    t = e_break_terms(rho, rho, work=2.0, delta_free_energy=0.5, gamma=0.4)
    assert t.gamma_t_sigma == pytest.approx(0.6)
    with pytest.raises(ValueError):
        e_break_terms(rho, rho, work=float("nan"))


def test_theta_monotone_and_fail_closed():
    xs = [0.0, 0.1, 0.5, 1.0, 3.0]
    th = [theta_integrity(x) for x in xs]
    assert th == sorted(th, reverse=True) and th[0] == 1.0
    assert theta_integrity(float("nan")) == 0.0
    assert theta_integrity(-5.0) == 1.0


# ---------- 문서(docs/experiments/stage0) 표의 주장을 고정
def test_doc_scenario_claims():
    from experiments.stage0.scenarios import run
    r = {name.split()[0]: (a, b) for name, a, b in run()}
    a2, b2 = r["S2"]; a3, b3 = r["S3"]; a4, b4 = r["S4"]
    # 후보 A 는 양성(표현 차이)을 주입보다 위험하게 본다 → 오탐 + 미탐
    assert a2.e_break > a3.e_break
    # 후보 B 는 순서가 맞다
    assert b3.e_break > b2.e_break and b3.e_break > 1.0 and b2.e_break < 0.1
    # 혼합 단일 행동은 ΔC(앵커 기저 코히런스)로만 잡힌다
    assert b4.delta_c == pytest.approx(LN2, abs=0.01) and abs(a4.delta_c) < 1e-9
    assert a4.e_break < 0 < b4.e_break
    # 주입 시 앵커 겹침 하락
    assert b3.anchor_overlap == pytest.approx(0.5, abs=1e-6) and b2.anchor_overlap > 0.98
