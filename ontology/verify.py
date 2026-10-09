"""레코드의 근거가 저장소에 실제로 존재하는지 확인하는 런타임 점검.

스키마(ontology.schema)와 분리되어 있다. 근거의 '진위'가 아니라
'가리키는 대상이 존재하는가'만 본다: 파일, 줄 번호, 테스트 함수 이름.
"""
from __future__ import annotations

from pathlib import Path

from .schema import EvidenceKind, OntologyRecord


def check_evidence(record: OntologyRecord, repo_root: Path) -> list[str]:
    problems: list[str] = []
    for ev in record.evidence:
        if ev.kind is EvidenceKind.CODE:
            path, _, line = ev.ref.partition(":")
            f = repo_root / path
            if not f.is_file():
                problems.append(f"{record.term_id}: 파일 없음 {path}")
                continue
            if line:
                n = len(f.read_text(encoding="utf-8").splitlines())
                if not (1 <= int(line) <= n):
                    problems.append(f"{record.term_id}: {path} 줄 {line} 범위 밖 (총 {n}줄)")
        elif ev.kind is EvidenceKind.TEST:
            path, _, name = ev.ref.partition("::")
            f = repo_root / path
            if not f.is_file():
                problems.append(f"{record.term_id}: 테스트 파일 없음 {path}")
            elif name and f"def {name}(" not in f.read_text(encoding="utf-8"):
                problems.append(f"{record.term_id}: 테스트 함수 없음 {ev.ref}")
    return problems
