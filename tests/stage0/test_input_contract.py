# -*- coding: utf-8 -*-
"""Stage 0 입력 계약 재현·회귀 테스트 (이슈 #16).

2026-11-20 main 522bef3 에서 실행으로 재현한 다섯 가지 문제를 고정한다.
- 고친 것: 일반 테스트. 각 테스트 docstring 에 '수정 전' 동작을 적었다.
- 결정 대기: xfail(strict=True). 기준을 정해 코드를 고치면 XPASS 로 실패하므로 그때 표시를 제거한다.
  후보 기준과 근거: docs/experiments/stage0_anchor_criteria_proposal.md
"""
import math

import numpy as np
import pytest

from experiments.stage0.ebreak_candidates import (
    AgentStep, anchor_dephase, anchor_overlap, coherence_anchor, coherence_rel_entropy,
    orthonormal_basis, q_quantum, rho_semantic, von_neumann_entropy,
)

LN2 = math.log(2)
NORMAL = np.diag([1.0, 0.0, 0.0])     # 정상 방향 순수 상태 (e1)
LEAK = np.diag([0.0, 1.0, 0.0])       # 유출 방향 순수 상태 (e2)
PLUS_I = 0.5 * np.array([[1, -1j], [1j, 1]])   # |+i><+i|


def _anchor_calls(rho, anchors):
    """앵커를 받는 공개 함수 전부."""
    return (
        lambda: anchor_overlap(rho, anchors),
        lambda: anchor_dephase(rho, anchors),
        lambda: coherence_anchor(rho, anchors),
        lambda: q_quantum(rho, anchors, 0.0),
        lambda: orthonormal_basis(anchors, rho.shape[0]),
    )


# ---------- 1. 중복·거의 겹치는 앵커
def test_exact_duplicate_anchors_rejected():
    """기존 동작 유지: 정확히 같은 앵커 중복은 거부한다."""
    for call in _anchor_calls(NORMAL, np.array([[1.0, 0, 0], [1.0, 0, 0]])):
        with pytest.raises(ValueError):
            call()


@pytest.mark.xfail(strict=True, reason=(
    "거의 겹치는 앵커의 처리 기준 결정 대기 (docs/experiments/stage0_anchor_criteria_proposal.md). "
    "현재: [1,0,0] 과 [1,1e-6,0] 이 허용되고, 그 차이가 만든 방향이 앵커 부분공간에 통째로 들어가 "
    "유출 상태 e2 의 앵커 겹침이 1.0 이 된다"))
def test_near_duplicate_anchors_do_not_trust_noise_direction():
    anchors = np.array([[1.0, 0, 0], [1.0, 1e-6, 0]])
    try:
        overlap = anchor_overlap(LEAK, anchors)
    except ValueError:
        return                      # 거부도 유효한 해결이다
    assert overlap < 0.5            # 거부하지 않는다면, 잡음 방향을 온전히 신뢰해서는 안 된다


# ---------- 2. 앵커 수
def test_more_anchors_than_dimensions_rejected():
    """수정 전: 3차원에 앵커 4개(반드시 선형종속)가 허용되어 P_A = I, 유출 상태의 겹침 1.0."""
    anchors = np.array([[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0], [1.0, 1.0, 1.0]])
    for call in _anchor_calls(LEAK, anchors):
        with pytest.raises(ValueError):
            call()


def test_empty_anchor_set_rejected():
    """수정 전: 앵커 0개가 허용되어 겹침 0.0 을 반환 (오류 없이 우연히 차단 쪽으로 동작)."""
    for call in _anchor_calls(NORMAL, np.zeros((0, 3))):
        with pytest.raises(ValueError):
            call()


@pytest.mark.xfail(strict=True, reason=(
    "앵커가 전체 공간을 채우는 경우(m = dim, P_A = I)의 처리 결정 대기 "
    "(docs/experiments/stage0_anchor_criteria_proposal.md). 현재: 유출 상태도 Q = 1.0 으로 통과한다. "
    "기존 test_anchor_overlap_bounds 는 이 경우의 겹침 1.0 을 명세로 두고 있다"))
def test_full_space_anchors_do_not_make_q_gate_vacuous():
    try:
        q = q_quantum(LEAK, np.eye(3), 0.0)
    except ValueError:
        return
    assert q < 1.0


# ---------- 3. coherence_rel_entropy 의 기준 기저
def test_basis_must_be_orthonormal():
    """수정 전: 정규직교가 아닌 기저 [[0.6,0.8],[1,0]] 에서 오류 없이 0.653 을 반환.
    정사각이 아닌 기저(3x2)는 0.0 을 반환."""
    rho = np.diag([1.0, 0.0])
    with pytest.raises(ValueError):
        coherence_rel_entropy(rho, np.array([[0.6, 0.8], [1.0, 0.0]]))
    with pytest.raises(ValueError):
        coherence_rel_entropy(np.diag([1.0, 0.0, 0.0]), np.eye(3)[:, :2])
    with pytest.raises(ValueError):
        coherence_rel_entropy(rho, np.array([[1.0, np.nan], [0.0, 1.0]]))
    with pytest.raises(ValueError):
        coherence_rel_entropy(rho, 2.0 * np.eye(2))        # 직교하지만 정규화되지 않음


def test_valid_basis_still_works():
    plus = np.full((2, 2), 0.5)
    hadamard = orthonormal_basis(np.array([[1.0, 1.0]]), 2)
    assert coherence_rel_entropy(plus) == pytest.approx(LN2)
    assert coherence_rel_entropy(plus, hadamard) == pytest.approx(0.0, abs=1e-9)
    assert coherence_rel_entropy(plus, np.eye(2)) == pytest.approx(LN2)


def test_complex_unitary_basis_uses_conjugate_transpose():
    """수정 전: basis.T 를 써서, |+i><+i| 를 자기 고유기저에서 재면 0 대신 'Tr ρ = 1' 오류."""
    u = np.array([[1, 1], [1j, -1j]]) / np.sqrt(2)          # 열 = |+i>, |-i>
    assert coherence_rel_entropy(PLUS_I, u) == pytest.approx(0.0, abs=1e-9)
    assert coherence_rel_entropy(PLUS_I) == pytest.approx(LN2)
    with pytest.raises(ValueError):
        coherence_rel_entropy(PLUS_I, np.array([[1, 1j], [1j, 1]]))      # B†B = 2I, 유니터리 아님


# ---------- 4. 실수 입력 계약
def test_complex_anchors_rejected():
    """수정 전: 복소 앵커 [1, i]/√2 의 허수부가 ComplexWarning 만 내고 버려져 겹침 0.5 (정답 1.0)."""
    anchors = np.array([[1, 1j]]) / np.sqrt(2)
    for call in _anchor_calls(PLUS_I, anchors):
        with pytest.raises(ValueError):
            call()
    with pytest.raises(ValueError):                          # 허수부가 0 이어도 복소 dtype 은 거부
        anchor_overlap(NORMAL, np.array([[1 + 0j, 0, 0]]))


@pytest.mark.parametrize("bad", [[[np.nan, 0, 0]], [[np.inf, 0, 0]], [[0.0, 0, 0]]])
def test_non_finite_and_zero_anchors_rejected(bad):
    """수정 전: NaN·inf 앵커가 오류 없이 겹침 0.0 을 반환."""
    for call in _anchor_calls(NORMAL, np.array(bad)):
        with pytest.raises(ValueError):
            call()


def test_complex_step_inputs_rejected():
    """수정 전: 복소 확률은 경고만 내고 그대로 보관되고, 복소 임베딩은 허수부가 버려진다."""
    with pytest.raises(ValueError):
        AgentStep(np.array([0.5 + 0j, 0.5]), np.eye(2))
    with pytest.raises(ValueError):
        AgentStep(np.array([1.0]), np.array([[1, 1j]]) / np.sqrt(2))


# ---------- 5. AgentStep 의 배열 소유권
def test_step_owns_validated_copies():
    """수정 전: 스텝이 호출자의 배열을 그대로 참조한다. 생성 후 임베딩을 같은 방향으로 바꾸면
    엔트로피가 ln 2 에서 0 으로 오류 없이 바뀐다."""
    p = np.array([0.5, 0.5])
    e = np.eye(2)
    step = AgentStep(p, e)
    before = rho_semantic(step).copy()
    p[0] = 5.0
    e[1] = [1.0, 0.0]
    assert step.probs is not p and step.embeddings is not e
    assert np.array_equal(rho_semantic(step), before)
    assert von_neumann_entropy(rho_semantic(step)) == pytest.approx(LN2)


def test_step_arrays_are_read_only():
    """수정 전: 리스트를 주면 리스트로 보관되고, 보관된 배열을 그대로 고칠 수 있다."""
    step = AgentStep([0.5, 0.5], [[1.0, 0.0], [0.0, 1.0]])
    assert isinstance(step.probs, np.ndarray) and step.probs.dtype == np.float64
    assert isinstance(step.embeddings, np.ndarray) and step.embeddings.shape == (2, 2)
    with pytest.raises(ValueError):
        step.probs[0] = 5.0
    with pytest.raises(ValueError):
        step.embeddings[1] = [1.0, 0.0]
    with pytest.raises(ValueError):
        step.probs.setflags(write=True)          # 쓰기 가능으로 되돌릴 수 없다
    with pytest.raises(ValueError):
        step.embeddings.setflags(write=True)
    with pytest.raises(AttributeError):
        step.probs = np.array([1.0, 0.0])        # frozen dataclass
