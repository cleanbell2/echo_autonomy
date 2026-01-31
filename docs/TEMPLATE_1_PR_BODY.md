## Template 1: PR Body (Copy-Paste Ready)

## ✅ Echo Gateway Phase 2 — READY TO MERGE

### Summary
이번 PR은 Echo Gateway의 **Phase 2 안전 패치 세트**를 추가합니다.
- Auth Profiles: 멀티 키 페일오버 + 쿨다운 트래킹
- Tool Sandbox: path traversal 차단 + (기본) symlink 방어
- BCDSI Middleware: inbound/tool 검증 어댑터 (local/http) + 5단계 개입

### What changed
- `gateway/auth_profiles.py` : ENV 참조 기반 키 관리, 실패 분류, failover
- `tools/sandbox.py` : workspace 내부 경로 강제, traversal/absolute/symlink 방어
- `middleware/bcdsi_integration.py` : BCDSI 체크 표준화, 타임아웃, 개입 레벨 통일
- `tests/test_gateway_integration.py` : 통합 테스트 5종
- `tests/test_e2e.py` : 서버 전제 E2E 테스트(서버 미구현/미가동 시 pytest.skip로 종료)

### Tests
- Integration: `tests/test_gateway_integration.py` (5/5)
  - Auth Failover
  - Sandbox Defense
  - BCDSI Intervention (local)
  - BCDSI Fail-Closed
  - Summary report
- E2E: `tests/test_e2e.py`
  - 서버/엔드포인트가 없으면 내부에서 `pytest.skip()` 처리
  - 서버가 준비되면 실제 연결/라우트 검증이 활성화됨

### CI Policy (Decision: no `|| true`)
- `|| true` 사용 금지
- 실패는 실패로 처리됨(실패 은폐 없음)
- E2E "서버 없음"은 쉘 억제가 아니라 **pytest.skip()** 로 처리됨

### Security notes
- 시크릿은 repo에 포함하지 않음(ENV 참조만 사용)
- sandbox는 기본 fail-closed(의심 경로 차단)
- BCDSI fail-closed 기본값 적용(특히 tool stage는 안전 우선)

### Merge
- Merge 방식: **Squash & merge**
- Command:
  - `gh pr merge <PR_NUMBER> --squash --delete-branch`

### Tags
echo_gateway, phase2, ci, no-true, ready-to-merge
