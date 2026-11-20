"""용어 레코드 계약.

이 모듈은 '무엇이 기록되어야 하는지'와 상태 조합만 강제한다.
- 근거 대상이 실제로 존재하는지, 원문 해시가 맞는지: ontology.verify
- 승인(Φ_bel)과 버전·상태 전이: ontology.store (저장 시점에 전부 다시 검사)
레코드에는 승인 플래그가 없다. 승인은 별도 Approval 기록이며, 레코드 내용 해시에 묶인다.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

_SHA = re.compile(r"^[0-9a-f]{7,40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


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


class ExperimentStatus(Enum):
    NONE = "none"
    PLANNED = "planned"
    RUN = "run"                # 실행 결과 기록 있음 (결과가 성공이라는 뜻은 아님)


class EvidenceKind(Enum):
    SOURCE_DOC = "source_doc"  # 저장소 안의 원문 파일 + 버전 + 내용 해시
    CODE = "code"              # 코드 경로:줄 + 커밋
    TEST = "test"              # 테스트 경로::이름 + 커밋 + 결과
    EXPERIMENT = "experiment"  # 실험 스크립트/로그 경로 + 커밋 + 결과


class CheckResult(Enum):
    PASSED = "passed"
    XFAIL = "xfail"            # 결정 대기 중인 항목
    FAILED = "failed"


def _not_blank(v: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError("공백 문자열 불가")
    return v.strip()


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    def model_copy(self, *, update: dict[str, Any] | None = None, deep: bool = False):
        """기본 model_copy는 update를 검증하지 않으므로, 복사본을 다시 검증한다."""
        data = self.model_dump()
        data.update(update or {})
        return type(self).model_validate(data)


class Evidence(_Frozen):
    kind: EvidenceKind
    ref: str
    commit: Optional[str] = None
    result: Optional[CheckResult] = None
    source_version: Optional[str] = None     # SOURCE_DOC 전용
    content_sha256: Optional[str] = None     # SOURCE_DOC 전용
    note: str = ""

    _ref = field_validator("ref")(_not_blank)

    @model_validator(mode="after")
    def _by_kind(self) -> "Evidence":
        k, r = self.kind, self.ref
        needs_result = k in (EvidenceKind.TEST, EvidenceKind.EXPERIMENT)
        if needs_result != (self.result is not None):
            raise ValueError(f"{r}: 결과는 테스트·실험 근거에만, 반드시 붙인다")
        if k is EvidenceKind.SOURCE_DOC:
            if not (self.source_version and self.source_version.strip()):
                raise ValueError(f"{r}: 원문 근거에는 버전 필요")
            if not (self.content_sha256 and _SHA256.match(self.content_sha256)):
                raise ValueError(f"{r}: 원문 근거에는 sha256 내용 해시 필요")
        else:
            if self.source_version or self.content_sha256:
                raise ValueError(f"{r}: 버전·해시는 원문 근거 전용")
            if not (self.commit and _SHA.match(self.commit)):
                raise ValueError(f"{r}: 코드·테스트·실험 근거는 커밋 SHA 필요")
        return self


class NextCheck(_Frozen):
    what: str
    due: date

    _what = field_validator("what")(_not_blank)


class OntologyRecord(_Frozen):
    term_id: str
    version: int = 1
    scope: str
    claim: str
    evidence: tuple[Evidence, ...] = ()
    counter_evidence: tuple[str, ...] = ()
    definition_status: DefinitionStatus = DefinitionStatus.PROPOSED
    implementation_status: ImplementationStatus = ImplementationStatus.NOT_IMPLEMENTED
    experiment_status: ExperimentStatus = ExperimentStatus.NONE
    next_check: Optional[NextCheck] = None
    supersedes: Optional[str] = None          # "TERM_ID@version"

    _strs = field_validator("term_id", "scope", "claim")(_not_blank)

    @field_validator("counter_evidence")
    @classmethod
    def _counter_not_blank(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_not_blank(s) for s in v)

    @field_validator("version")
    @classmethod
    def _version_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("version은 1 이상")
        return v

    def content_sha256(self) -> str:
        """승인이 묶이는 대상. 어떤 필드가 바뀌어도 해시가 바뀌어 기존 승인은 무효가 된다."""
        blob = json.dumps(self.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _has(self, kind: EvidenceKind, result: Optional[CheckResult] = None) -> bool:
        return any(
            e.kind is kind and (result is None or e.result is result) for e in self.evidence
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
        if self.experiment_status is ExperimentStatus.RUN and not self._has(EvidenceKind.EXPERIMENT):
            raise ValueError(f"{t}: 실험 RUN에는 실험 근거 필요")
        if (self.version == 1) != (self.supersedes is None):
            raise ValueError(f"{t}: version 1만 supersedes가 없고, 이후 버전은 반드시 있어야 함")
        if self.supersedes is not None and self.supersedes != f"{t}@{self.version - 1}":
            raise ValueError(f"{t}: supersedes는 {t}@{self.version - 1}이어야 함")

        unresolved = (
            self.definition_status is not DefinitionStatus.VERIFIED
            or self.implementation_status in (ImplementationStatus.STUB, ImplementationStatus.PARTIAL)
            or self.experiment_status is ExperimentStatus.PLANNED
        )
        if unresolved and self.next_check is None:
            raise ValueError(f"{t}: 미확정 상태에는 next_check 필요")
        return self


class Approval(_Frozen):
    """Φ_bel(t) 기록. 특정 레코드 버전의 내용 해시에 묶인다."""

    term_id: str
    version: int
    content_sha256: str
    approver: str
    approved_at: date
    channel_ref: str          # 승인이 남은 곳: 서명 커밋 SHA, PR 리뷰 URL 등

    _strs = field_validator("term_id", "approver", "channel_ref")(_not_blank)

    @field_validator("content_sha256")
    @classmethod
    def _hash(cls, v: str) -> str:
        if not _SHA256.match(v):
            raise ValueError("sha256 해시 형식 아님")
        return v
