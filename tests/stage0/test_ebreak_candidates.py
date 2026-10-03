# -*- coding: utf-8 -*-
"""Stage 0 참조 구현의 수학적 성질 검증. 정의가 양자정보 의미를 지키는지 확인한다."""
import math

import numpy as np
import pytest

from experiments.stage0.ebreak_candidates import (
    AgentStep, anchor_dephase, anchor_overlap, coherence_anchor, coherence_rel_entropy,
    e_break_terms, gate, non_unitarity, orthonormal_basis, q_quantum, rho_classical,
    rho_semantic, rho_semantic_dephased, spectrum, theta_integrity, von_neumann_entropy,
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
    assert (t.delta_s, t.delta_c, t.n_epsilon, t.gamma_t_sigma_proxy) == pytest.approx((0, 0, 0, 0), abs=1e-9)
    assert t.e_break == pytest.approx(0.0, abs=1e-9)


def test_thermo_term_is_gamma_w_minus_df():
    rho = np.eye(2) / 2
    t = e_break_terms(rho, rho, cost_proxy=2.0, progress_proxy=0.5, gamma=0.4)
    assert t.gamma_t_sigma_proxy == pytest.approx(0.6)
    with pytest.raises(ValueError):
        e_break_terms(rho, rho, cost_proxy=float("nan"))


def test_theta_monotone_and_fail_closed():
    xs = [0.0, 0.1, 0.5, 1.0, 3.0]
    th = [theta_integrity(x) for x in xs]
    assert th == sorted(th, reverse=True) and th[0] == 1.0
    assert theta_integrity(float("nan")) == 0.0
    assert theta_integrity(-5.0) == 1.0


# ---------- D2: 앵커 투영 탈위상
def test_anchor_coherence_independent_of_complement_basis():
    """같은 앵커면 여공간 기저를 어떻게 골라도 값이 같다 (전체 기저 탈위상은 달라짐)."""
    e = np.eye(4); a = np.array([e[0]])
    rho = np.outer(e[0] + e[1] + e[2], e[0] + e[1] + e[2]) / 3
    b0 = orthonormal_basis(a, 4)
    r = np.eye(4); c, s_ = np.cos(.7), np.sin(.7); r[1:3, 1:3] = [[c, -s_], [s_, c]]
    assert coherence_rel_entropy(rho, b0) != pytest.approx(coherence_rel_entropy(rho, b0 @ r), abs=1e-3)
    assert coherence_anchor(rho, a) == pytest.approx(coherence_anchor(rho, 3.7 * a))   # 같은 부분공간이면 동일
    for _ in range(20):
        a2 = rng.normal(size=(2, 4))
        x = rho_semantic(rand_step(d=4))
        dep = anchor_dephase(x, a2)
        assert math.isclose(np.trace(dep), 1.0, abs_tol=1e-9) and coherence_anchor(x, a2) >= -1e-9
        assert coherence_anchor(dep, a2) == pytest.approx(0.0, abs=1e-9)


def test_delta_s_plus_delta_c_equals_dephased_entropy_change():
    """ΔS + ΔC_P = ΔS(Δ_P ρ). 두 항의 독립 기여를 주장하면 안 되는 이유."""
    a = rng.normal(size=(1, 4))
    for _ in range(50):
        x, y = rho_semantic(rand_step(d=4)), rho_semantic(rand_step(d=4))
        t = e_break_terms(x, y, anchors=a)
        lhs = t.delta_s + t.delta_c
        rhs = von_neumann_entropy(anchor_dephase(y, a)) - von_neumann_entropy(anchor_dephase(x, a))
        assert lhs == pytest.approx(rhs, abs=1e-9)


# ---------- D1: 탈위상 대조군
def test_dephased_control_keeps_overlap_removes_coherence():
    a = np.array([np.eye(4)[0]])
    for _ in range(20):
        st = rand_step(d=4)
        rb, rd = rho_semantic(st), rho_semantic_dephased(st, a)
        assert anchor_overlap(rd, a) == pytest.approx(anchor_overlap(rb, a))
        assert coherence_anchor(rd, a) == pytest.approx(0.0, abs=1e-9)


# ---------- D5: 부호 ΔS 본안 + 클램프 변형
def test_clamped_variant_only_changes_negative_delta_s():
    a = np.array([np.eye(4)[0]])
    x, y = rho_semantic(rand_step(d=4)), rho_semantic(rand_step(d=4))
    t = e_break_terms(x, y, anchors=a)
    assert t.e_break_clamped - t.e_break == pytest.approx(max(0.0, t.delta_s) - t.delta_s)
    assert t.e_break_clamped >= t.e_break


# ---------- D6: Q_quantum 이중 게이트 + 반례
def test_counterexample_unitary_drift_is_invisible_to_ebreak_but_caught_by_q():
    """순수 정상 → 순수 유출: ΔS=ΔC=ℕ=0, E=0, θ=1. 클램프로도 해결 안 됨. Q=0 이 막는다."""
    e = np.eye(4); a = np.array([e[0]])
    r0, r1 = np.outer(e[0], e[0]), np.outer(e[2], e[2])
    t = e_break_terms(r0, r1, anchors=a)
    assert t.e_break == pytest.approx(0.0, abs=1e-12) and t.e_break_clamped == pytest.approx(0.0, abs=1e-12)
    th, q = theta_integrity(t.e_break), q_quantum(r1, a, t.e_break)
    assert th == 1.0 and q == pytest.approx(0.0, abs=1e-12)
    d = gate(th, q, theta_min=0.5, q_min=0.5)
    assert not d.approve and "q_quantum" in d.reason and "theta" not in d.reason


def test_q_quantum_properties():
    e = np.eye(3); a = np.array([e[0]])
    r = np.outer(e[0], e[0])
    assert q_quantum(r, a, 0.0) == pytest.approx(1.0)
    assert q_quantum(r, a, 2.0) == pytest.approx(math.exp(-1.0))
    psi = np.array([math.cos(.3), math.sin(.3), 0])
    assert q_quantum(np.outer(psi, psi), a, 0.0) == pytest.approx(abs(math.cos(.3)))   # cosΔθ
    assert q_quantum(r, a, float("nan")) == 0.0


def test_gate_requires_both_and_fails_closed():
    assert gate(0.9, 0.9, theta_min=0.5, q_min=0.5).approve
    assert not gate(0.4, 0.9, theta_min=0.5, q_min=0.5).approve
    assert not gate(0.9, 0.4, theta_min=0.5, q_min=0.5).approve
    assert not gate(float("nan"), 0.9, theta_min=0.5, q_min=0.5).approve
    with pytest.raises(TypeError):
        gate(0.9, 0.9)                         # 임계값 기본값 없음 (사전 등록 강제)


# ---------- 문서(docs/experiments/stage0) 표의 주장을 고정
def test_doc_scenario_claims():
    from experiments.stage0.scenarios import run
    r = {(n.split()[0], tag): (t, th, q) for n, tag, t, th, q in run()}
    E = lambda s, c: r[(s, c)][0].e_break
    # A 는 양성(표현 차이)을 주입보다 위험하게 본다
    assert E("S2", "A") > E("S3", "A")
    # B 는 순서가 맞다
    assert E("S3", "B") > 1.0 > 0.1 > E("S2", "B")
    # 장난감 예시에서 B 와 탈위상 대조군 Bd 의 ΔS+ΔC 합은 같다 (항등식) → 코히런스의 추가 판별력 근거 없음
    for s in ("S1", "S2", "S3", "S4", "S5"):
        tb, td = r[(s, "B")][0], r[(s, "Bd")][0]
        assert tb.delta_s + tb.delta_c == pytest.approx(td.delta_s + td.delta_c, abs=1e-6)
    assert E("S4", "Bd") > E("S4", "B")            # S4 는 대조군도 잡는다 (더 크게)
    # S5 반례: 세 후보 모두 E=0, B 의 Q=0
    assert all(abs(E("S5", c)) < 1e-12 for c in ("A", "B", "Bd"))
    assert r[("S5", "B")][2] == pytest.approx(0.0, abs=1e-12)
