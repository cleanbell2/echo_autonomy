"""레코드의 근거가 저장소에 실제로 존재하는지 확인한다.

근거의 '진위'가 아니라 '가리키는 대상이 존재하고 기록된 내용과 같은가'만 본다:
파일, 줄 번호, 테스트 함수 이름, 원문 파일의 sha256.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .schema import EvidenceKind, OntologyRecord


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_evidence(record: OntologyRecord, repo_root: Path) -> list[str]:
    problems: list[str] = []
    t = record.term_id
    for ev in record.evidence:
        if ev.kind is EvidenceKind.SOURCE_DOC:
            f = repo_root / ev.ref
            if not f.is_file():
                problems.append(f"{t}: 원문 파일 없음 {ev.ref}")
            elif file_sha256(f) != ev.content_sha256:
                problems.append(f"{t}: 원문 해시 불일치 {ev.ref} (원문이 바뀌었거나 기록이 틀림)")
        elif ev.kind is EvidenceKind.CODE:
            path, _, line = ev.ref.partition(":")
            f = repo_root / path
            if not f.is_file():
                problems.append(f"{t}: 파일 없음 {path}")
                continue
            if line:
                n = len(f.read_text(encoding="utf-8").splitlines())
                if not line.isdigit() or not (1 <= int(line) <= n):
                    problems.append(f"{t}: {path} 줄 {line} 범위 밖 (총 {n}줄)")
        else:  # TEST, EXPERIMENT
            path, _, name = ev.ref.partition("::")
            f = repo_root / path
            if not f.is_file():
                problems.append(f"{t}: 파일 없음 {path}")
            elif name and f"def {name}(" not in f.read_text(encoding="utf-8"):
                problems.append(f"{t}: 함수 없음 {ev.ref}")
    return problems
