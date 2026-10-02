# -*- coding: utf-8 -*-
"""
Stage 0 예시 시나리오 — 문서 표의 수치를 재현한다.
    python -m experiments.stage0.scenarios

주의: 임베딩은 손으로 만든 4차원 장난감 벡터다. 실제 임베딩 모델 결과가 아니다.
축: e1 = 요청된 정상 행동, e2 = 정상 행동의 표현 차이, e3 = 외부 유출(주입된 지시), e4 = 무관한 행동
앵커: e1 (사용자 지시 이행 · 데이터 보호)
"""
from __future__ import annotations

import numpy as np

from .ebreak_candidates import (
    AgentStep, e_break_terms, orthonormal_basis, rho_classical, rho_semantic, theta_integrity,
)

E1, E2, E3, E4 = np.eye(4)
ANCHORS = np.array([E1])
BASIS = orthonormal_basis(ANCHORS, 4)


def v(*rows):
    return np.array(rows, float)


PREV = AgentStep(np.array([0.5, 0.3, 0.2]), v(E1, E1 + 0.1 * E2, E1 - 0.1 * E2))

SCENARIOS = {
    "S1 정상 진행": AgentStep(np.array([0.6, 0.25, 0.15]), v(E1, E1 + 0.1 * E2, E1 - 0.1 * E2)),
    "S2 표현만 다른 후보 4개": AgentStep(np.full(4, 0.25),
                                    v(E1, E1 + 0.15 * E2, E1 - 0.15 * E2, E1 + 0.05 * E2)),
    "S3 프롬프트 주입": AgentStep(np.array([0.5, 0.4, 0.1]), v(E1, E3, E4)),
    # 정상 행동과 유출이 '한 행동 안에' 섞인 경우: 예) "요약을 보내면서 외부 주소에도 첨부"
    "S4 혼합된 단일 행동": AgentStep(np.array([1.0]), v(E1 + E3)),
}


def run():
    rows = []
    for name, step in SCENARIOS.items():
        b = e_break_terms(rho_semantic(PREV), rho_semantic(step), basis=BASIS, anchors=ANCHORS)
        a = e_break_terms(rho_classical(PREV), rho_classical(step))
        rows.append((name, a, b))
    return rows


def main():
    print(f"{'시나리오':22s} | {'후보':4s} | {'ΔS':>7s} {'ΔC':>7s} {'ℕ(ε)':>7s} | {'E_break':>7s} {'θ':>6s} | 앵커겹침")
    for name, a, b in run():
        for tag, t in (("A", a), ("B", b)):
            ov = "" if t.anchor_overlap is None else f"{t.anchor_overlap:.3f}"
            print(f"{name:22s} | {tag:4s} | {t.delta_s:7.3f} {t.delta_c:7.3f} {t.n_epsilon:7.3f} | "
                  f"{t.e_break:7.3f} {theta_integrity(t.e_break):6.3f} | {ov}")


if __name__ == "__main__":
    main()
