"""레코드 저장소. 저장·승인 시점에 모든 조건을 다시 검사한다.

레코드 객체가 어떤 경로로 만들어졌든(model_construct, 우회 복사 등) 저장 전에
원시 값으로 되돌려 처음부터 다시 검증하므로, 객체 단계의 우회는 저장소를 통과하지 못한다.

한계: approver 문자열은 인증이 아니다. '벨 계정'임을 보장하려면 승인 기록이
벨만 쓸 수 있는 채널(서명 커밋, CODEOWNERS가 걸린 파일, PR 리뷰)에 있어야 하고,
channel_ref가 그 위치를 가리켜야 한다. 이 모듈은 channel_ref의 존재와 형식까지만 본다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .schema import Approval, DefinitionStatus as D, OntologyRecord
from .verify import check_evidence

# 정의 상태 전이: 한 번 VERIFIED/DISPUTED가 된 정의를 PROPOSED/INFERRED로 되돌려
# 검토 이력을 지우는 것을 막는다.
_ALLOWED: dict[D, set[D]] = {
    D.PROPOSED: {D.PROPOSED, D.INFERRED, D.VERIFIED, D.DISPUTED},
    D.INFERRED: {D.INFERRED, D.VERIFIED, D.DISPUTED},
    D.VERIFIED: {D.VERIFIED, D.DISPUTED},
    D.DISPUTED: {D.DISPUTED, D.VERIFIED},
}


class StoreError(ValueError):
    pass


class OntologyStore:
    def __init__(self, repo_root: Path, approver: str):
        self.repo_root = Path(repo_root)
        self.approver = approver
        self._versions: dict[str, list[OntologyRecord]] = {}
        self._approvals: dict[str, Approval] = {}

    # ---------- 저장 ----------
    def save(self, record: OntologyRecord) -> OntologyRecord:
        rec = OntologyRecord.model_validate(record.model_dump())  # 원시 값에서 재검증

        problems = check_evidence(rec, self.repo_root)
        if problems:
            raise StoreError("; ".join(problems))

        history = self._versions.get(rec.term_id, [])
        if not history:
            if rec.version != 1:
                raise StoreError(f"{rec.term_id}: 첫 저장은 version 1이어야 함")
        else:
            last = history[-1]
            if rec.version == last.version:
                if rec.content_sha256() == last.content_sha256():
                    return last  # 같은 내용 재저장
                raise StoreError(f"{rec.term_id}@{rec.version}: 같은 버전에 다른 내용 저장 불가")
            if rec.version != last.version + 1:
                raise StoreError(f"{rec.term_id}: 다음 버전은 {last.version + 1}이어야 함")
            if rec.definition_status not in _ALLOWED[last.definition_status]:
                raise StoreError(
                    f"{rec.term_id}: 정의 상태 {last.definition_status.value} → "
                    f"{rec.definition_status.value} 전이 불가"
                )
        self._versions.setdefault(rec.term_id, []).append(rec)
        return rec

    def current(self, term_id: str) -> OntologyRecord:
        try:
            return self._versions[term_id][-1]
        except KeyError:
            raise StoreError(f"{term_id}: 저장된 레코드 없음") from None

    def history(self, term_id: str) -> tuple[OntologyRecord, ...]:
        return tuple(self._versions.get(term_id, ()))

    # ---------- 승인 (Φ_bel) ----------
    def approve(self, approval: Approval) -> Approval:
        ap = Approval.model_validate(approval.model_dump())
        rec = self.current(ap.term_id)
        if ap.approver != self.approver:
            raise StoreError(f"{ap.term_id}: 승인자 {ap.approver}는 권한 없음")
        if ap.version != rec.version:
            raise StoreError(f"{ap.term_id}: 승인 버전 {ap.version} ≠ 현재 {rec.version}")
        if ap.content_sha256 != rec.content_sha256():
            raise StoreError(f"{ap.term_id}: 승인 해시가 현재 내용과 다름")
        if rec.definition_status is not D.VERIFIED:
            raise StoreError(f"{ap.term_id}: 정의가 VERIFIED가 아니면 승인 불가")
        self._approvals[ap.term_id] = ap
        return ap

    def approval_for(self, term_id: str) -> Optional[Approval]:
        """현재 버전·내용과 일치하는 승인만 돌려준다. 새 버전이 저장되면 기존 승인은 자동 무효."""
        ap = self._approvals.get(term_id)
        if ap is None:
            return None
        rec = self.current(term_id)
        if ap.version != rec.version or ap.content_sha256 != rec.content_sha256():
            return None
        return ap

    def is_committed(self, term_id: str) -> bool:
        """C_commit: 현재 버전에 유효한 Φ_bel 승인이 있는가."""
        return self.approval_for(term_id) is not None
