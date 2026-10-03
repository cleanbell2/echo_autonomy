# -*- coding: utf-8 -*-
"""
Stage 0 예시 시나리오 — 문서 표의 수치를 재현한다.
    python -m experiments.stage0.scenarios

주의: 임베딩은 손으로 만든 4차원 장난감 벡터다. 실제 임베딩 모델 결과가 아니다.
축: e1 = 요청된 정상 행동, e2 = 정상 행동의 표현 차이, e3 = 외부 유출(주입된 지시), e4 = 무관한 행동
앵커: e1 (사용자 지시 이행 · 데이터 보호)
후보: A = classical, B = semantic (본안), Bd = B 의 앵커 투영 탈위상 (D1 대조군)
"""
from __future__ import annotations

import numpy as np

from .ebreak_candidates import (
    AgentStep, e_break_terms, q_quantum, rho_classical, rho_semantic, rho_semantic_dephased,
    theta_integrity,
)

E1, E2, E3, E4 = np.eye(4)
ANCHORS = np.array([E1])


def v(*rows):
    return np.array(rows, float)


PREV = AgentStep(np.array([0.5, 0.3, 0.2]), v(E1, E1 + 0.1 * E2, E1 - 0.1 * E2))
PREV_PURE = AgentStep(np.array([1.0]), v(E1))

# (이름, 이전 스텝, 현재 스텝)
SCENARIOS = [
    ("S1 정상 진행", PREV, AgentStep(np.array([0.6, 0.25, 0.15]), v(E1, E1 + 0.1 * E2, E1 - 0.1 * E2))),
    ("S2 표현만 다른 후보 4개", PREV, AgentStep(np.full(4, 0.25),
                                          v(E1, E1 + 0.15 * E2, E1 - 0.15 * E2, E1 + 0.05 * E2))),
    ("S3 프롬프트 주입", PREV, AgentStep(np.array([0.5, 0.4, 0.1]), v(E1, E3, E4))),
    # 정상 행동과 유출이 '한 행동 안에' 섞인 경우
    ("S4 혼합된 단일 행동", PREV, AgentStep(np.array([1.0]), v(E1 + E3))),
    # 반례: 확신에 찬 정상 행동 → 확신에 찬 유출 (유니터리 회전). E_break 는 0, Q 가 잡아야 함
    ("S5 순수 정상→순수 유출", PREV_PURE, AgentStep(np.array([1.0]), v(E3))),
]


def run():
    """[(이름, 후보, EBreakTerms, θ, Q)]  — A 는 앵커가 없으므로 Q 는 None."""
    rows = []
    for name, prev, now in SCENARIOS:
        a = e_break_terms(rho_classical(prev), rho_classical(now))
        rb_prev, rb_now = rho_semantic(prev), rho_semantic(now)
        b = e_break_terms(rb_prev, rb_now, anchors=ANCHORS)
        rd_prev, rd_now = rho_semantic_dephased(prev, ANCHORS), rho_semantic_dephased(now, ANCHORS)
        d = e_break_terms(rd_prev, rd_now, anchors=ANCHORS)
        rows.append((name, "A", a, theta_integrity(a.e_break), None))
        rows.append((name, "B", b, theta_integrity(b.e_break), q_quantum(rb_now, ANCHORS, b.e_break)))
        rows.append((name, "Bd", d, theta_integrity(d.e_break), q_quantum(rd_now, ANCHORS, d.e_break)))
    return rows


def main():
    print(f"{'시나리오':24s} | {'후보':3s} | {'ΔS':>7s} {'ΔC':>7s} {'ℕ(ε)':>7s} | "
          f"{'E_break':>7s} {'E_clamp':>7s} {'θ':>6s} | {'앵커겹침':>7s} {'Q':>6s}")
    for name, tag, t, th, q in run():
        ov = "" if t.anchor_overlap is None else f"{t.anchor_overlap:.3f}"
        qs = "" if q is None else f"{q:.3f}"
        print(f"{name:24s} | {tag:3s} | {t.delta_s:7.3f} {t.delta_c:7.3f} {t.n_epsilon:7.3f} | "
              f"{t.e_break:7.3f} {t.e_break_clamped:7.3f} {th:6.3f} | {ov:>7s} {qs:>6s}")


if __name__ == "__main__":
    main()
