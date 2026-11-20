"""저장소에서 직접 확인한 용어만 등록한다. (확인 커밋: 95b7086, 2026-10-10)

나머지 후보(Q_QUANTUM, L_POLICY, BCDSI, ANCHOR, NOVA_DNA, RSTAR2_AGENT,
DARKFLOW_PREDICTOR, MACRO_PULSE)는 같은 방식으로 근거를 확인한 뒤 추가한다.
승인(Approval)은 하나도 없다. 승인은 ontology.store.OntologyStore.approve로만 기록된다.
"""
from __future__ import annotations

from datetime import date

from .schema import (
    CheckResult,
    DefinitionStatus as D,
    Evidence,
    EvidenceKind as K,
    ImplementationStatus as I,
    NextCheck,
    OntologyRecord,
)

SHA = "95b7086e3ea78025e4f0f8e7801c85c82cccca83"
SOURCE_DOC = "docs/ontology/delta_log_core.md"
SOURCE_SHA256 = "e5649af553f1a9f69841ccb901db33882dfaf74ca163f78ad0959dea26513ec4"

E_BREAK_QBN = OntologyRecord(
    term_id="E_BREAK_QBN",
    scope="Δ-Log 거버넌스 프레임워크의 불협화음 측정량",
    claim=(
        r"E_{break}^{QBN} = \Delta S + \gamma T\Sigma + \Delta C + \mathcal{N}(\varepsilon); "
        r"E_{break} > \theta_{integrity} \Rightarrow \text{BCDSI 개입}"
    ),
    evidence=(
        Evidence(kind=K.SOURCE_DOC, ref=SOURCE_DOC, source_version="v1",
                 content_sha256=SOURCE_SHA256, note="1. 비가역적 불협화음 측정"),
        Evidence(kind=K.CODE, ref="e_break_engine.py:111", commit=SHA,
                 note="(1-w)·S + w·C_rel. 변화량(Δ)·TΣ·ℕ(ε) 없음"),
        Evidence(kind=K.CODE, ref="q_quantum/e_break_engine.py:58", commit=SHA,
                 note="1 - exp(-(W-ΔF)/(T·S)). 위 식과 다른 수식"),
        Evidence(kind=K.CODE, ref="q_quantum/ebreak_calculator.py:74", commit=SHA,
                 note="고정값 0.42 반환. sicl/governance_bridge.py가 이 경로를 호출"),
        Evidence(kind=K.TEST, ref="test_e_break_engine.py::test_e_break_comprehensive",
                 commit=SHA, result=CheckResult.PASSED,
                 note="통과하지만 원문 수식이 아닌 가중합을 검증함"),
    ),
    counter_evidence=(
        "구현 3개가 서로 다른 수식이며 어느 것도 원문 4항을 모두 포함하지 않음",
        "런타임(SICL) 경로는 고정값이라 bcdsi_detected가 항상 False",
        "ρ 정의가 없으면 ΔS 계산 불가",
    ),
    definition_status=D.VERIFIED,
    implementation_status=I.PARTIAL,
    next_check=NextCheck(what="정본 구현 1개 선정 후 원문 4항 대비 테스트 작성",
                         due=date(2026, 10, 24)),
)

THETA_INTEGRITY = OntologyRecord(
    term_id="THETA_INTEGRITY",
    scope="E_break와 비교되는 BCDSI 개입 기준",
    claim=r"\theta_{integrity}: E_{break}가 이 값을 넘으면 BCDSI 개입",
    evidence=(
        Evidence(kind=K.SOURCE_DOC, ref=SOURCE_DOC, source_version="v1",
                 content_sha256=SOURCE_SHA256, note="1번 수식의 임계값 문장"),
        Evidence(kind=K.CODE, ref="q_quantum/e_break_engine.py:79", commit=SHA,
                 note="임계값으로 사용: e_break > theta"),
        Evidence(kind=K.CODE, ref="q_quantum/bcdsi/monitor.py:93", commit=SHA,
                 note="무결성 점수로 사용: 1 - e_break"),
        Evidence(kind=K.CODE, ref="bcdsi/threshold.py:63", commit=SHA,
                 note="엔트로피·코히런스·비단위원성 항 포함 버전"),
        Evidence(kind=K.CODE, ref="bcdsi/threshold.py:124", commit=SHA,
                 note="시스템 중요도 항 포함 버전"),
        Evidence(kind=K.TEST, ref="tests/governance/test_bcdsi_regressions.py::"
                 "test_theta_single_source_of_truth",
                 commit=SHA, result=CheckResult.XFAIL, note="정본 수식 결정 대기"),
    ),
    counter_evidence=(
        "임계값(비교 기준)과 무결성 점수(1-E_break)라는 두 의미가 같은 이름으로 쓰임",
    ),
    definition_status=D.DISPUTED,
    implementation_status=I.PARTIAL,
    next_check=NextCheck(what="임계값/점수 중 하나로 이름 고정, 다른 쪽은 개명",
                         due=date(2026, 10, 17)),
)

SICL_DELTALOG = OntologyRecord(
    term_id="SICL_DELTALOG",
    scope="sicl 상태기계의 ASSESS 단계 출력 레코드 (거버넌스 프레임워크 Δ-Log와 별개)",
    claim="psi, phi, chi, omega, comp, e_est, theta_drift_deg, anomalies를 담는 틱별 평가값",
    evidence=(
        Evidence(kind=K.CODE, ref="sicl/types.py:36", commit=SHA),
        Evidence(kind=K.CODE, ref="sicl/state_machine.py:18", commit=SHA,
                 note="e_est = 0.2 / 0.1 고정 분기, '나중에 v3.4 연결' 주석"),
    ),
    counter_evidence=(
        "'대화 출처 추적 프로토콜'이라는 정의와 불일치",
        "phi·chi·omega는 기본값 0.5에서 갱신되지 않음 (psi만 persona.py:194에서 +0.01)",
    ),
    definition_status=D.VERIFIED,
    implementation_status=I.STUB,
    next_check=NextCheck(what="DeltaLogCalculator를 E_BREAK_QBN 정본 구현에 연결",
                         due=date(2026, 10, 31)),
)

RECORDS: dict[str, OntologyRecord] = {
    r.term_id: r for r in (E_BREAK_QBN, THETA_INTEGRITY, SICL_DELTALOG)
}
