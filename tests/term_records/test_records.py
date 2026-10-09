from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from ontology import REGISTRY, check_evidence
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
CODE = Evidence(kind=K.CODE, ref="sicl/types.py:36", commit="abc")


def test_default_is_proposed_and_unapproved():
    r = OntologyRecord(term_id="T", scope="s", claim="c", next_check=NC)
    assert r.definition_status is D.PROPOSED
    assert r.implementation_status is I.NOT_IMPLEMENTED
    assert r.bell_approved is False


def test_unverified_record_requires_next_check():
    with pytest.raises(ValidationError, match="next_check"):
        OntologyRecord(term_id="T", scope="s", claim="c")


def test_verified_requires_source_or_code():
    with pytest.raises(ValidationError, match="VERIFIED"):
        OntologyRecord(term_id="T", scope="s", claim="c", definition_status=D.VERIFIED)


def test_implemented_requires_passing_test():
    xfail = Evidence(kind=K.TEST, ref="t.py::test_a", commit="abc", result=CheckResult.XFAIL)
    with pytest.raises(ValidationError, match="IMPLEMENTED"):
        OntologyRecord(term_id="T", scope="s", claim="c", evidence=(CODE, xfail),
                       definition_status=D.VERIFIED, implementation_status=I.IMPLEMENTED)


def test_approval_requires_verified_definition():
    with pytest.raises(ValidationError, match="승인"):
        OntologyRecord(term_id="T", scope="s", claim="c", next_check=NC, bell_approved=True)


def test_code_evidence_requires_commit():
    with pytest.raises(ValidationError, match="커밋"):
        Evidence(kind=K.CODE, ref="sicl/types.py:36")


def test_registry_has_no_approvals_yet():
    assert all(not r.bell_approved for r in REGISTRY.values())


@pytest.mark.parametrize("term_id", sorted(REGISTRY))
def test_registry_evidence_points_to_existing_code(term_id):
    assert check_evidence(REGISTRY[term_id], ROOT) == []
