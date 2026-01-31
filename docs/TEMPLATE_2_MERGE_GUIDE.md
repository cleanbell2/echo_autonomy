## Template 2: Merge Guide (Copy-Paste Ready)

## ✅ Merge Guide — Echo Gateway Phase 2

### 0) Pre-merge (5-minute checklist)
1. 로컬 테스트 통과
   - `pytest tests/test_gateway_integration.py -v`
2. 시크릿 유입 없음 확인
   - `auth-profiles.json`은 `ENV:` 참조만 사용
   - `.env`는 gitignore 유지
3. Fail-closed 기본값 확인
   - Tool stage + 엔진 불가/누락: BLOCK
   - Inbound stage + 엔진 불가/누락: WARNING
4. Sandbox 방어 확인
   - traversal / absolute / (기본) symlink 방어 동작
5. 의존성 반영 확인
   - `requirements-dev.txt`에 pytest/pytest-asyncio/httpx/websockets 포함
6. CI 정책 확정
   - `|| true` 금지
   - E2E는 pytest.skip 기반(실패 은폐 없음)

### 1) CI 활성화 (tests.yml)
GitHub Actions에 아래 워크플로우를 추가한다: `.github/workflows/tests.yml`

핵심 규칙:
- Integration tests는 항상 실행
- E2E는 서버가 없으면 pytest.skip로 정상 종료
- `|| true` 사용하지 않음(실패 은폐 금지)

### 2) Merge 실행 (Squash)
1. 최신 main 동기화
   - `git fetch origin main`
   - `git rebase origin/main`
2. 머지
   - `gh pr merge <PR_NUMBER> --squash --delete-branch`

### 3) Post-merge (Day 1)
1. Phase 3 브랜치 생성
   - `git checkout main`
   - `git pull origin main`
   - `git checkout -b phase3-protocol`
2. 디렉토리 생성
   - `mkdir -p echo_gateway/protocol`
3. Phase 3 작업 시작
   - `envelope.py`
   - `schemas.py`
   - `validator.py`
   - `tests/test_protocol_roundtrip.py`

### 4) Notes on E2E tests
- E2E는 "서버가 없어서 실패를 무시"하지 않는다.
- 서버 미가동/미구현 상태는 `pytest.skip()`로 처리한다(정상 종료).
- 실제 오류(예: 잘못된 응답, 핸드쉐이크 실패, 예상과 다른 결과)는 테스트 실패로 처리된다.
- `|| true`는 사용하지 않는다(실패 은폐 없음).

### Tags
echo_gateway, phase2, ci, no-true, ready-to-merge
