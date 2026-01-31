## 🎉 최종 템플릿 배포 확인서 (Copy-Paste Ready)

## ✅ 개요

본 문서는 **Echo Gateway Phase 2**에서 사용 가능한 **PR 본문 템플릿 1종**과 **Merge Guide 템플릿 1종**이
다음 기준을 만족하도록 **정제되었음을 확인**하기 위한 배포 확인서입니다.

* 상태 표현: **READY TO MERGE** 기준(과거 이벤트 "MERGED/DEPLOYED" 단정 금지)
* CI 정책: **no `|| true` (failures are not suppressed)**
* E2E 정책: 서버 미구현/미가동 시 **내부 `pytest.skip()`로 정상 스킵**(exit 0), 실제 실패는 **테스트 실패로 표면화**(exit != 0)
* 보안 기본값: **Fail-closed**(툴 실행은 BLOCK 우선, inbound는 WARNING/모니터링 우선 등 프로젝트 정책에 맞게 명시)

---

## 📦 배포 대상 템플릿 2종

### 1) Template 1 — PR Body

* 목적: PR 설명란에 **복사/붙여넣기** 용
* 핵심 포함 사항:

  * Phase 2 산출물 요약 (Auth Failover / Sandbox / BCDSI)
  * Integration Tests 결과 표기(예: 5/5)
  * **CI 정책: no `|| true` → failures are not suppressed**
  * E2E는 **pytest.skip() 기반 graceful handling** 설명
  * 시크릿/키 관리: ENV 참조만 사용 등 보안 노트

> 참고: 파일명/경로는 프로젝트 표준에 맞게 유지하되, 문서 본문에는 **로컬 절대경로/특정 커밋**을 필수로 적지 않는 것을 권장합니다.

---

### 2) Template 2 — Merge Guide

* 목적: 팀/리뷰어가 머지 절차를 빠르게 재현할 수 있는 **절차서**
* 핵심 포함 사항:

  * **6-item Pre-merge checklist**
  * CI 워크플로우 적용 가이드
  * E2E 정책(스킵/실패 구분) 명확화
  * Squash merge 권장 흐름
  * Post-merge: Phase 3(Protocol Layer) 시작 단계

---

## 🔐 CI 정책 명시 (Decision: no `|| true`)

* ✅ **No `|| true`**: 실패를 숨기지 않습니다. (failures are not suppressed)
* ✅ E2E는 서버가 아직 준비되지 않은 경우, **셸 억지 통과가 아니라 테스트 내부 로직으로 스킵**합니다.
* ✅ 서버가 있는데도 실패하면(진짜 실패), **정상적으로 CI를 실패**시키는 것이 목표입니다.

---

## 🧪 테스트 정책 요약

### Integration Tests

* Phase 2 핵심 리스크 영역(예: Auth Failover / Sandbox / BCDSI / Fail-Closed)을 커버하도록 설계
* CI에서 기본적으로 실행되는 테스트 세트로 유지

### E2E Tests

* 서버/엔드포인트가 아직 없거나 실행되지 않은 경우:

  * `pytest.skip("Gateway server not reachable")` 등으로 **정상 스킵**(exit 0)
* 서버가 존재하고 테스트가 실제로 수행되는 상황에서 문제가 발생하면:

  * **테스트 실패로 처리**(exit != 0)
* 결론: **"스킵은 허용, 실패는 숨기지 않음"**

---

## ✅ 6-Item Pre-merge Checklist (5분 점검)

1. 로컬/CI에서 Integration Tests가 통과한다
2. repo에 시크릿이 포함되지 않았다 (ENV 참조만 사용)
3. Fail-closed 기본값이 문서/코드/테스트로 확인된다
4. Sandbox(경로 탐색/절대경로/심볼릭 링크 등) 방어가 테스트로 검증된다
5. 테스트 의존성이 requirements/pyproject에 반영되어 있다
6. CI에서 **no `|| true`** 정책이 지켜진다 (failures are not suppressed)

---

## 🧾 참고 정보 (선택 표기)

아래 항목은 상황에 따라 "참고"로만 첨부합니다(필수 아님).

* 파일명/경로: (예시) `docs/TEMPLATE_1_PR_BODY.md`, `docs/TEMPLATE_2_MERGE_GUIDE.md`
* 커밋/브랜치: (예시) 특정 커밋 해시/브랜치명은 내부 기록용으로만 사용

---

## 🎯 태그(키워드)

`echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`

---

## 📁 템플릿 파일 위치

- **Template 1 (PR Body)**: `docs/TEMPLATE_1_PR_BODY.md`
- **Template 2 (Merge Guide)**: `docs/TEMPLATE_2_MERGE_GUIDE.md`
- **배포 확인서**: `docs/DEPLOYMENT_VERIFICATION.md`

---

## ✅ 배포 상태

**Status**: ✅ **TEMPLATES READY FOR USE**

**배포일**: 2026-01-31

**검증 완료**:
- [x] 단정/확정 표현 최소화
- [x] 경로/커밋은 "예시/참고"로만 표기
- [x] CI 정책 "no `|| true`" 명확히 명시
- [x] E2E 정책 "pytest.skip() 기반, 실패 숨김 없음" 명시
- [x] 보안 기본값 "Fail-closed" 명시
- [x] 6-Item Checklist 구체적으로 명시

---

**Next Steps**: Phase 3 (Protocol Layer) 구현 시작
