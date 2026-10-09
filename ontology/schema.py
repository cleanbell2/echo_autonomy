"""용어 레코드 계약.

이 모듈은 '무엇이 기록되어야 하는지'만 강제한다.
근거가 실제로 맞는지(파일·커밋·테스트 결과)는 ontology.verify가 따로 확인한다.
pydantic 검증은 타입과 상태 조합만 본다. 의미 충돌을 찾거나 진위를 판정하지 않는다.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DefinitionStatus(Enum):
    PROPOSED = "proposed"      # 제안됨, 근거 미확인 (기본값)
    INFERRED = "inferred"      # 다른 기록에서 추론, 원문 미확인
    VERIFIED = "verified"      # 원문 또는 코드와 정의가 일치함을 확인
    DISPUTED = "disputed"      # 같은 이름에 서로 다른 정의가 공존


class ImplementationStatus(Enum):
    NOT_IMPLEMENTED = "not_implemented"
    STUB = "stub"              # 고정값·더미 로직
    PARTIAL = "partial"        # 일부 경로만 구현, 또는 중복 구현 공존
    IMPLEMENTED = "implemented"


class EvidenceKind(Enum):
    SOURCE_DOC = "source_doc"  # 벨이 작성한 원문 정의
    CODE = "code"              # 코드 경로:줄
    TEST = "test"              # 테스트 경로::이름
    COMMIT = "commit"


class CheckResult(Enum):
    PASSED = "passed"
    XFAIL = "xfail"            # 결정 대기 중인 항목
    FAILED = "failed"


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: EvidenceKind
    ref: str                                  # "sicl/types.py:36", "tests/x.py::test_y"
    commit: Optional[str] = None              # 확인 시점의 커밋 SHA
    result: Optional[CheckResult] = None       # TEST일 때만
    note: str = ""

    @model_validator(mode="after")
    def _result_only_for_tests(self) -> "Evidence":
        if self.kind is EvidenceKind.TEST and self.result is None:
            raise ValueError(f"{self.ref}: 테스트 근거에는 결과가 필요")
        if self.kind is not EvidenceKind.TEST and self.result is not None:
            raise ValueError(f"{self.ref}: 테스트가 아닌 근거에 결과를 붙일 수 없음")
        if self.kind in (EvidenceKind.CODE, EvidenceKind.TEST) and not self.commit:
            raise ValueError(f"{self.ref}: 코드·테스트 근거는 커밋 SHA 필요")
        return self


class NextCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    what: str
    due: date


class OntologyRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    term_id: str
    version: int = 1
    scope: str                                # 이 정의가 적용되는 범위
    claim: str                                # 정의
    evidence: tuple[Evidence, ...] = ()
    counter_evidence: tuple[str, ...] = ()    # 정의가 성립하지 않는 조건·반례
    definition_status: DefinitionStatus = DefinitionStatus.PROPOSED
    implementation_status: ImplementationStatus = ImplementationStatus.NOT_IMPLEMENTED
    bell_approved: bool = False               # Φ_bel(t)
    next_check: Optional[NextCheck] = None
    supersedes: Optional[str] = None          # "TERM_ID@version"

    def _has(self, kind: EvidenceKind, result: Optional[CheckResult] = None) -> bool:
        return any(
            e.kind is kind and (result is None or e.result is result)
            for e in self.evidence
        )

    @model_validator(mode="after")
    def _status_consistency(self) -> "OntologyRecord":
        t = self.term_id
        if self.definition_status is DefinitionStatus.VERIFIED and not (
            self._has(EvidenceKind.SOURCE_DOC) or self._has(EvidenceKind.CODE)
        ):
            raise ValueError(f"{t}: VERIFIED에는 원문 또는 코드 근거 필요")

        if self.implementation_status is ImplementationStatus.IMPLEMENTED and not self._has(
            EvidenceKind.TEST, CheckResult.PASSED
        ):
            raise ValueError(f"{t}: IMPLEMENTED에는 통과한 테스트 근거 필요")

        if self.implementation_status is not ImplementationStatus.NOT_IMPLEMENTED and not self._has(
            EvidenceKind.CODE
        ):
            raise ValueError(f"{t}: 구현 상태를 주장하려면 코드 근거 필요")

        if self.bell_approved and self.definition_status is not DefinitionStatus.VERIFIED:
            raise ValueError(f"{t}: 정의가 VERIFIED가 아니면 승인 불가")

        unresolved = (
            self.definition_status is not DefinitionStatus.VERIFIED
            or self.implementation_status
            in (ImplementationStatus.STUB, ImplementationStatus.PARTIAL)
        )
        if unresolved and self.next_check is None:
            raise ValueError(f"{t}: 미확정 상태에는 next_check 필요")
        return self
