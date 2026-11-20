from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from ontology import RECORDS, Approval, OntologyStore, StoreError, check_evidence
from ontology.records import SOURCE_DOC, SOURCE_SHA256
from ontology.schema import (
    CheckResult,
    DefinitionStatus as D,
    Evidence,
    EvidenceKind as K,
    ImplementationStatus as I,
    NextCheck,
    OntologyRecord,
)

ROOT = Path(__file__).resolve().parents[2]
NC = NextCheck(what="x", due=date(2026, 12, 1))
SHA = "95b7086"
SRC = Evidence(kind=K.SOURCE_DOC, ref=SOURCE_DOC, source_version="v1", content_sha256=SOURCE_SHA256)
CODE = Evidence(kind=K.CODE, ref="sicl/types.py:36", commit=SHA)


def _rec(**kw):
    base = dict(term_id="T", scope="s", claim="c", next_check=NC)
    base.update(kw)
    return OntologyRecord(**base)


def _verified(version=1, **kw):
    sup = None if version == 1 else f"T@{version - 1}"
    return _rec(evidence=(SRC,), definition_status=D.VERIFIED, version=version, supersedes=sup, **kw)


def _approval(rec, approver="cleanbell2"):
    return Approval(term_id=rec.term_id, version=rec.version, content_sha256=rec.content_sha256(),
                    approver=approver, approved_at=date(2026, 10, 10), channel_ref="PR#review")


@pytest.fixture
def store():
    return OntologyStore(ROOT, approver="cleanbell2")


# ---------- 리뷰에서 보고된 우회 4건 ----------
def test_bypass_1_record_has_no_approval_flag():
    with pytest.raises(ValidationError):
        _rec(bell_approved=True)


def test_bypass_2_attribute_assignment_blocked():
    r = _rec()
    with pytest.raises(ValidationError):
        r.definition_status = D.VERIFIED


def test_bypass_3_model_copy_revalidates():
    with pytest.raises(ValidationError, match="VERIFIED"):
        _rec().model_copy(update={"definition_status": D.VERIFIED})


def test_bypass_3b_model_construct_rejected_at_save(store):
    forged = OntologyRecord.model_construct(
        term_id="T", version=1, scope="s", claim="c", evidence=(),
        counter_evidence=(), definition_status=D.VERIFIED,
        implementation_status=I.NOT_IMPLEMENTED, next_check=None, supersedes=None,
    )
    with pytest.raises(ValidationError, match="VERIFIED"):
        store.save(forged)


@pytest.mark.parametrize("ref", [" ", "", "\t\n"])
def test_bypass_4_blank_evidence_rejected(ref):
    with pytest.raises(ValidationError, match="공백"):
        Evidence(kind=K.CODE, ref=ref, commit=SHA)


def test_source_doc_needs_version_and_hash():
    with pytest.raises(ValidationError, match="버전"):
        Evidence(kind=K.SOURCE_DOC, ref=SOURCE_DOC, content_sha256=SOURCE_SHA256)
    with pytest.raises(ValidationError, match="해시"):
        Evidence(kind=K.SOURCE_DOC, ref=SOURCE_DOC, source_version="v1", content_sha256="abc")


def test_source_doc_hash_mismatch_fails_save(store):
    bad = Evidence(kind=K.SOURCE_DOC, ref=SOURCE_DOC, source_version="v1", content_sha256="0" * 64)
    with pytest.raises(StoreError, match="해시 불일치"):
        store.save(_rec(evidence=(bad,), definition_status=D.VERIFIED))


# ---------- 상태 규칙 ----------
def test_default_is_proposed():
    r = _rec()
    assert r.definition_status is D.PROPOSED and r.implementation_status is I.NOT_IMPLEMENTED


def test_unresolved_requires_next_check():
    with pytest.raises(ValidationError, match="next_check"):
        OntologyRecord(term_id="T", scope="s", claim="c")


def test_implemented_requires_passing_test():
    xfail = Evidence(kind=K.TEST, ref="t.py::test_a", commit=SHA, result=CheckResult.XFAIL)
    with pytest.raises(ValidationError, match="IMPLEMENTED"):
        _rec(evidence=(CODE, xfail), definition_status=D.VERIFIED, implementation_status=I.IMPLEMENTED)


# ---------- 저장소: 버전·전이 ----------
def test_store_version_sequence(store):
    store.save(_verified())
    with pytest.raises(StoreError, match="다음 버전"):
        store.save(_verified(version=3))
    with pytest.raises(StoreError, match="같은 버전"):
        store.save(_verified(claim="changed"))


def test_store_blocks_downgrade_to_proposed(store):
    store.save(_verified())
    with pytest.raises(StoreError, match="전이 불가"):
        store.save(_rec(version=2, supersedes="T@1"))


# ---------- 저장소: 승인 (Φ_bel / C_commit) ----------
def test_approval_bound_to_content_and_version(store):
    v1 = store.save(_verified())
    store.approve(_approval(v1))
    assert store.is_committed("T")

    store.save(_verified(version=2, claim="c2"))  # 내용이 바뀌면
    assert not store.is_committed("T")            # 기존 승인은 무효


def test_approval_rejects_wrong_approver(store):
    v1 = store.save(_verified())
    with pytest.raises(StoreError, match="권한"):
        store.approve(_approval(v1, approver="someone"))


def test_approval_rejects_stale_hash(store):
    v1 = store.save(_verified())
    stale = _approval(v1).model_copy(update={"content_sha256": "f" * 64})
    with pytest.raises(StoreError, match="해시"):
        store.approve(stale)


def test_approval_requires_verified(store):
    r = store.save(_rec())
    with pytest.raises(StoreError, match="VERIFIED"):
        store.approve(_approval(r))


# ---------- 실제 레코드 ----------
@pytest.mark.parametrize("term_id", sorted(RECORDS))
def test_records_save_cleanly(store, term_id):
    assert check_evidence(RECORDS[term_id], ROOT) == []
    store.save(RECORDS[term_id])
    assert not store.is_committed(term_id)
