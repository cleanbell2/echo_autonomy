# -*- coding: utf-8 -*-
"""앵커 기준 제안 문서의 수치가 스크립트·실제 코드와 같은지 확인한다 (제안·미승인, 이슈 #16).

판정 기준 자체를 검증하는 테스트가 아니다. 문서가 실제 동작과 어긋나지 않게 묶어 두는 테스트다.
"""
import pathlib

import numpy as np
import pytest

from experiments.stage0 import anchor_criteria as ac
from experiments.stage0.ebreak_candidates import anchor_overlap

DOC = pathlib.Path(__file__).resolve().parents[2] / "docs/experiments/stage0_anchor_criteria_proposal.md"


def _verdicts():
    header, rows = ac.table_verdicts()
    return {r[0]: dict(zip(header[1:], r[1:])) for r in rows}


def test_doc_tables_match_script_output():
    """문서의 표 1~3 은 스크립트 출력 그대로여야 한다."""
    text = DOC.read_text(encoding="utf-8")
    for table in (ac.table_verdicts, ac.table_noise, ac.table_scale):
        for line in ac.markdown(*table()):
            assert line in text, f"문서에 없는 줄: {line}"


def test_current_rule_accepts_reported_case():
    v = _verdicts()
    assert v["정확히 같은 앵커"]["현재"] == "거부"
    assert v["차이 1e-6 (보고된 사례)"]["현재"] == "허용"
    # '현재' 열은 실제 코드의 판정이다: 허용된 앵커로 유출 방향의 겹침이 1.0 이 된다
    leak = np.zeros((ac.DIM, ac.DIM))
    leak[1, 1] = 1.0
    assert anchor_overlap(leak, ac.pair_eps(1e-6)) == pytest.approx(1.0)


def test_singular_value_family_separates_numerical_from_semantic():
    v = _verdicts()
    assert ac.sv_ratio(ac.pair_eps(1e-6)) == pytest.approx(5e-7, rel=1e-3)
    assert v["차이 1e-6 (보고된 사례)"]["σ비<1e-9"] == "허용"
    for label in ("σ비<1e-6", "σ비<1e-4", "σ비<1e-2"):
        assert v["차이 1e-6 (보고된 사례)"][label] == "거부"
        # 서로 다른 앵커는 가장 느슨한 후보에서도 거부되지 않는다
        for case in ("코사인 0.999", "코사인 0.99", "코사인 0.8", "직교", "앵커 3개, 쌍별 코사인 모두 0.3"):
            assert v[case][label] == "허용"


def test_pairwise_cosine_family_misses_higher_order_dependence():
    v = _verdicts()
    case = "앵커 3개, 셋째 = 앞 둘의 조합 + 1e-6"
    assert ac.max_abs_cos(ac.triple_higher_order()) < 0.9
    assert all(v[case][f"cos>{c:g}"] == "허용" for c in ac.COS_CUTS)
    assert v[case]["σ비<1e-6"] == "거부"
    # 코사인 기준은 수치적으로 안정한 문장쌍도 거부한다
    assert v["코사인 0.97"]["cos>0.95"] == "거부" and v["코사인 0.93"]["cos>0.9"] == "거부"


def test_noise_wobble_formula_matches_projector():
    """표 2 의 공식 δ²/(s²+δ²) 를 투영 행렬로 직접 계산한 값과 비교한다."""
    for name, anchors in ac.cases():
        for _, noise in ac.NOISES:
            formula, numeric = ac.noise_wobble(anchors, noise), ac.noise_wobble_numeric(anchors, noise)
            if formula > 1e-9:        # 그보다 작으면 1 − x 뺄셈의 반올림 오차가 값을 가린다
                assert numeric == pytest.approx(formula, rel=1e-3), name
            else:
                assert numeric < 1e-8, name


def test_numerical_overlap_is_noise_driven_but_semantic_similarity_is_stable():
    reported = ac.noise_wobble(ac.pair_eps(1e-6), 1e-7)
    assert reported == pytest.approx(0.0099, rel=1e-2)          # float32 수준 잡음이 새 방향의 1% 를 정한다
    assert ac.noise_wobble(ac.pair_eps(1e-9), 1e-7) > 0.99      # 전부 잡음
    assert ac.noise_wobble(ac.pair_cos(0.999), 1e-7) < 1e-11    # 뜻이 가까운 서로 다른 문장은 안정


def test_current_rule_depends_on_vector_scale():
    rows = dict(ac.table_scale()[1])
    assert rows["단위 크기, 차이 1e-12"] == "거부" and rows["같은 두 방향을 1e6 배"] == "허용"
    assert rows["앵커 1개, 크기 1"] == "허용" and rows["앵커 1개, 크기 1e-10"] == "거부"


def test_random_direction_overlap_is_m_over_d():
    rng = np.random.default_rng(0)
    anchors = rng.normal(size=(3, 24))
    p = ac.projector(anchors)
    assert np.trace(p) == pytest.approx(3.0)                      # 평균 겹침 = Tr(P)/d = m/d
    assert ac.random_overlap(3, 24) == pytest.approx(np.trace(p) / 24)


def test_real_summary_with_fake_embedder():
    """--real 모드의 집계 경로를 가짜 임베딩으로 확인한다. 실제 모델 측정이 아니다."""
    table = {
        "a": [1.0, 0.0, 0.0, 0.0], "b": [0.0, 1.0, 0.0, 0.0], "c": [0.0, 0.0, 1.0, 0.0],
        "a2": [1.0, 1e-7, 0.0, 0.0],                       # a 와 수치적으로 겹침
        "d": [0.97, (1 - 0.97 ** 2) ** 0.5, 0.0, 0.0],     # a 와 코사인 0.97
    }
    embed = lambda texts: np.array([table[t] for t in texts])
    sets = [("distinct", ["a", "b", "c"]), ("numeric-dup", ["a", "a2", "c"]), ("similar", ["a", "d", "c"])]
    s = ac.real_summary(embed, sets)
    assert s["n"] == 3
    assert s["rejected"]["σ비<1e-6"] == ["numeric-dup"]
    assert s["rejected"]["σ비<1e-2"] == ["numeric-dup"]
    assert s["rejected"]["cos>0.95"] == ["numeric-dup", "similar"]
    assert s["rejected"]["cos>0.99"] == ["numeric-dup"]
    assert s["max_cos_min_med_p95_max"][0] == pytest.approx(0.0) and s["max_cos_min_med_p95_max"][-1] == pytest.approx(1.0)
