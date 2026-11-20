# HANDOFF — 인계 문서

최종 갱신: 2026-11-20 · 작성: Claude (AI) · 근거: 이슈 #16

이 문서는 다른 사람이나 다른 AI가 이 저장소의 연구 작업을 이어받을 때 필요한 사실을 모은 것이다.
Bell 의 승인 기록이 아니다. 승인의 근거는 §4 에 링크한 원문 댓글이다. AI 가 쓴 댓글·커밋·문서는 승인이 아니다.

## 0. 현재 상태 요약

| 구분 | 내용 |
|---|---|
| 완료 | 10~11월 브랜치 4개 통합(PR #15). Stage 0 참조 구현에 D1–D6 반영. 주요 반례와 항등식을 문서와 테스트에 반영. 입력 계약 중 결정 없이 고칠 수 있는 부분 보강(이 문서를 추가한 PR) |
| 결정 대기 | §8 의 항목. 그중 코드에 xfail 로 걸려 있는 것은 3건 |
| 미검증 | 실제 공격에 대한 방어 성능. 실험 1(AgentDojo)은 실행 기록이 없고 예비 실행도 승인 대기다 |

## 1. 설치·실행·테스트

CI 는 Python 3.10, 3.11, 3.12 에서 돈다 (`.github/workflows/main.yml`).

```bash
git clone https://github.com/cleanbell2/echo_autonomy.git
cd echo_autonomy
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

pytest                                          # 전체 스위트. 수집 대상은 pytest.ini 의 testpaths
pytest tests/stage0 -q                          # Stage 0 만
python -m experiments.stage0.scenarios          # Stage 0 문서 §4 의 표 재현
python -m experiments.stage0.anchor_criteria    # 앵커 기준 제안 문서의 표 1~3 재현
```

게이트웨이 서버 (가짜 LLM 으로 실행, 키 불필요):

```bash
LLM_PROVIDER=fake python -m uvicorn echo_gateway.server.app:create_app --factory --host 127.0.0.1 --port 18789
curl http://127.0.0.1:18789/health              # {"ok":true,"service":"echo_gateway","phase":6}
```

- 실제 LLM 은 `.env.example` 을 본다. `LLM_PROVIDER` 는 `fake | openai | anthropic` 중 하나이고 한 번에 하나만 쓴다.
- `tests/test_e2e.py` 는 위 서버가 떠 있지 않으면 스스로 skip 한다.
- 프록시 환경에서 서버 테스트가 실패하면 테스트 프로세스에서만 `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` 를 뺀다. 이번 검증 환경에서는 넣은 경우와 뺀 경우의 결과가 같았다.
- 실험 1 관련 스크립트(`experiments/exp1/make_split.py`, `anchor_criteria --real`)는 `agentdojo==0.1.35` 가 필요하다. `requirements*.txt` 에는 없다.

## 2. 검증한 것

| 대상 | 명령 | 결과 | 환경 |
|---|---|---|---|
| main `522bef32da5e8607a33cea0fe7b0ec4e0d15c064` (PR #15 병합 직후) | `pytest` | 323 passed, 6 skipped, 1 xfailed | 로컬 Python 3.11.18 / 3.12.3, CI 3.10 / 3.11 / 3.12 |
| 이 문서를 추가한 PR 의 트리 | `pytest` | 345 passed, 6 skipped, 3 xfailed | 로컬 Python 3.11.18 / 3.12.3. CI 결과와 정확한 커밋은 PR 과 이슈 #16 에 기록 |
| 같은 트리 | `pytest tests/stage0 -q` | 50 passed, 2 xfailed | 위와 같음 |
| 같은 트리 | `python -m experiments.stage0.scenarios` | 수정 전 main 과 출력이 같음 | Python 3.12.3 |

- skipped 6건: E2E 4건(서버 필요), 프로토콜 벤치마크 1건(`RUN_PROTOCOL_BENCH=1` 일 때만), 선택 구성요소 스모크 1건.
- xfailed 3건은 전부 결정 대기 항목이다 (§8 의 3, 7번).
  - `tests/governance/test_bcdsi_regressions.py::test_policy_strictness_is_monotonic`
  - `tests/stage0/test_input_contract.py::test_near_duplicate_anchors_do_not_trust_noise_direction`
  - `tests/stage0/test_input_contract.py::test_full_space_anchors_do_not_make_q_gate_vacuous`
- xfail 은 `strict=True` 다. 결정이 나서 코드를 고치면 XPASS 로 실패하므로 그때 표시를 제거한다.

## 3. 무엇이 실행 경로에 연결돼 있고 무엇이 아닌가

| 위치 | 내용 | 실행 경로 연결 |
|---|---|---|
| `echo_gateway/` | FastAPI 게이트웨이. `/health`, `/api/message`, `/api/stream`, `/ws` | 연결됨. 단 안전 검사는 `stub_safety_check` 로 항상 ALLOW 다 |
| `bcdsi/` | θ_integrity 정본(D4), `PolicyResolver`, `CriticalityAssessor`, `DynamicThreshold` | 게이트웨이에 연결되지 않음 |
| `experiments/stage0/` | ρ·E_break·Q 의 참조 구현과 장난감 시나리오 | 연결되지 않음 (참조 구현) |
| `experiments/exp1/` | 데이터 분할 파일과 생성 스크립트 | §7 참고 |
| `sicl/` | 상태기계. 타입 온톨로지 게이트는 opt-in | 기본 `GatewayNavigator` 경로의 판정은 온톨로지와 무관 |
| `ontology/` | Δ-Log 용어 레코드 (정의·구현·실험 상태 분리, 승인은 별도 기록) | 기록용. 승인된 레코드는 없다 |

E_break 이름을 가진 구현이 여러 개 공존하고 서로 다른 수식을 쓴다. 목록과 각각의 실제 동작은 `docs/experiments/stage0_ebreak_operational_definition.md` §1 에 있다. BCDSI 가 게이트웨이에서 실제로 무언가를 막는 상태가 아니라는 점이 중요하다.

## 4. 승인 근거 (Bell)

| 승인 | 내용 | 근거 |
|---|---|---|
| D1–D6 | D1 본안 B 와 대조군 A·Bd, D2 앵커 투영 탈위상으로 ΔC 계산, D3 γ·TΣ 는 대리 지표로 명시, D4 θ = 1/(1+max(0,E)) 로 통일, D5 부호 있는 ΔS 본안과 max(0,ΔS) 변형 병행, D6 θ·Q 이중 게이트 | [PR #12 댓글, 2026-10-03](https://github.com/cleanbell2/echo_autonomy/pull/12#issuecomment-5965967005) |
| Q 감쇠 항 ② | Q = cosΔθ · e^{−max(0,E)/2} | [PR #12 댓글, 2026-10-03](https://github.com/cleanbell2/echo_autonomy/pull/12#issuecomment-5966299280) |

같은 댓글에 적힌 유보: 정책 엄격도 순서는 미확정. 예비 실행은 모델·최대 비용·중단 조건을 제시받은 뒤 승인한다.

승인되지 않은 것: 실험 1 설계 문서의 제안값 전부, 앵커 입력 기준 제안, 정책 엄격도 순서, 유료 실행.

## 5. Stage 0: 확인된 것과 검증되지 않은 것

**수학적 성질과 장난감 벡터로 확인한 것** (`tests/stage0/`):

- ρ 가 밀도행렬이다 (에르미트, Tr = 1, 양의 준정부호).
- ΔS + ΔC 는 앵커 투영으로 탈위상한 상태의 엔트로피 변화 하나와 같다. 그래서 두 항이 독립적으로 기여한다고 주장하지 않는다.
- ΔC 는 여공간 기저를 어떻게 골라도 같다 (D2).
- ℕ(ε) 는 유니터리 전이에서 0 이다.
- 순수 정상 상태에서 순수 유출 상태로 방향만 바뀌면 E_break = 0, θ = 1 이다. E_break 는 이런 이탈을 원리적으로 보지 못한다. 이 경우 앵커 겹침이 0 이라 Q = 0 이 된다.
- 0 ≤ Q ≤ cosΔθ ≤ 1 이 모든 E 에서 성립한다 (Q ②).

**검증되지 않은 것:**

- 실제 공격에 대한 방어 성능. 실험 1 의 실행 기록이 없다.
- Q 가 방향 이탈을 잡는다는 것은 "앵커 겹침이 0 이면 Q = 0" 이라는 정의상의 성질이다. 실제 공격이 실제 임베딩에서 낮은 앵커 겹침으로 나타나는지는 모른다. 부분적으로 이탈한 경우를 막는지는 Q_min 에 달려 있고 Q_min 은 정해지지 않았다. 앵커를 어떻게 고르느냐에도 달려 있다(§6). **Q 가 모든 방향 이탈을 검출한다고 주장하지 않는다.**
- 코히런스가 판별력을 더한다는 근거. 장난감 예시에서는 대조군 Bd 도 같은 사례를 잡는다. 판정은 실험 1 의 B 대 Bd 비교로 미뤄져 있다.
- γ·TΣ 는 물리적 W − ΔF 로 검증된 값이 아니라 대리 지표다.
- Stage 0 문서 §4 의 표는 손으로 만든 4차원 벡터의 결과다.

**PR #12 본문의 "미해결 사항 6건"의 현재 상태.** 그 목록은 D1–D6 반영(커밋 `10268d0`) 이전에 쓰였다. 현재 코드 기준으로 나누면:

| # | 옛 지적 | 현재 상태 | 근거 |
|---|---|---|---|
| 1 | 순수 정상 → 순수 유출에서 E_break = 0, θ = 1 | E_break 의 한계로 문서화. 이 사례는 Q = 0 으로 차단 (D6) | `test_counterexample_unitary_drift_is_invisible_to_ebreak_but_caught_by_q` |
| 2 | ΔS + ΔC 가 독립 기여가 아님 | 항등식으로 문서화, 독립 기여 주장 철회 | `test_delta_s_plus_delta_c_equals_dephased_entropy_change` |
| 3 | 여공간 기저를 돌리면 E_break 가 달라짐 | 해결 (D2) | `test_anchor_coherence_independent_of_complement_basis` |
| 4 | B > A 만으로 양자 구조의 기여를 판단할 수 없음 | 같은 의미 정보를 쓰는 대조군 Bd 추가 (D1). 판정 자체는 실험 1 로 미룸 | `test_dephased_control_keeps_overlap_removes_coherence` |
| 5 | ℕ 와 W − ΔF 의 정의 | γ·TΣ 는 대리 지표로 명시 (D3). ℕ 는 여전히 상태 쌍의 유니터리 궤도 거리이며 단일 전이로 채널의 비유니터리성을 식별하지는 못한다 | Stage 0 문서 §2, §3 |
| 6 | 입력 계약 결함 | 일부 해결, 2건 결정 대기 | §6 |

## 6. 입력 계약

`experiments/stage0/ebreak_candidates.py` 가 받는 입력의 규칙이다. main `522bef3` 에서 다섯 가지 문제를 실행으로 재현했고, 재현 테스트는 `tests/stage0/test_input_contract.py` 에 있다.

| 문제 | 수정 전 | 지금 |
|---|---|---|
| `AgentStep` 검증 뒤 배열 변경 | 호출자의 배열을 그대로 참조. 임베딩을 바꾸면 엔트로피가 ln 2 에서 0 으로 오류 없이 바뀜 | 읽기 전용 float64 사본으로 보관. 원본을 바꿔도 영향 없고 보관된 배열은 고칠 수 없음 |
| 복소 입력 | 복소 앵커·임베딩의 허수부가 경고만 내고 버려짐 (겹침 0.5, 정답 1.0) | 확률·임베딩·앵커는 실수만 받고 복소 dtype 은 `ValueError` |
| 비유한·영벡터·빈 앵커 | NaN·inf 앵커가 겹침 0.0 을 반환. 빈 앵커도 허용 | `ValueError` |
| 앵커 수가 차원을 넘음 | 3차원에 앵커 4개가 허용되어 P_A = I | `ValueError` (반드시 선형종속) |
| `coherence_rel_entropy` 의 기저 | 검사 없음. 비직교 기저에서 0.653 반환, 복소 기저는 전치만 적용 | 정사각 유니터리만 받고 켤레전치로 변환 |
| 거의 겹치는 앵커 | `[1,0,0]`, `[1,1e-6,0]` 허용. 유출 상태의 겹침 1.0 | **그대로. 결정 대기** (xfail) |
| 전체 공간을 채우는 앵커 (m = dim) | P_A = I, 어떤 상태든 Q = 1.0 | **그대로. 결정 대기** (xfail) |

잘못된 앵커는 예외로 드러난다. 게이트를 실제로 연결할 때 호출하는 쪽은 이 예외를 차단으로 처리해야 한다.

결정 대기 2건의 후보 기준, 수치적 겹침과 문장 의미 유사도의 구분, 민감도, 실험 1 앵커 3종과의 관계는 `docs/experiments/stage0_anchor_criteria_proposal.md` 에 있다. 그 문서는 제안이며 승인되지 않았다. 표는 합성 벡터에서 나왔고 실제 임베딩 측정은 하지 못했다.

## 7. 실험 1 (AgentDojo): 있는 것과 없는 것

설계: `docs/experiments/exp1_agentdojo_design.md`. 문서의 새 선택값은 전부 제안·미승인이다.

| 있는 것 | 없는 것 |
|---|---|
| 설계 문서 (가설, 환경, 분할, 파이프라인, 앵커, 비교군, 보정 규칙, 예비 실행 조건) | 그림자 실행 하네스 |
| 데이터 분할 파일 `experiments/exp1/split_v1.2.2_seed20261003.json` 과 생성 스크립트 | 오프라인 재생과 재생 정합성 검증 |
| 분할 무결성 테스트 (`test_exp1_split_file_integrity`) | 후보 샘플링과 임베딩 파이프라인 |
| Stage 0 참조 구현 (ρ, E_break, θ, Q, 이중 게이트 함수) | 앵커 생성과 격리 구현 |
| 실험 1 앵커 3종의 문장 묶음을 만드는 함수 (`anchor_criteria.real_anchor_sets`) | 임계값 보정과 `thresholds.json` |
| | 게이트를 AgentDojo 파이프라인에 붙이는 코드, 비용 상한·자동 중단 로직 |

저장소에 실행 결과는 없다. 예비 실행은 승인 대기다. 승인 전에는 유료 실행을 하지 않는다.

## 8. Bell 의 결정 대기 항목

1. **실험 1 예비 실행 승인.** 본 실험 전에 정상 4건과 공격 4건만 돌려 호출 수와 비용을 재는 단계다. 문서 제안은 Haiku 4.5, 누적 10달러에서 즉시 중단, 한 에피소드 2.5달러에서 중단 (설계 §10).
2. **실험 1 의 나머지 제안값.** 데이터 분할, 앵커 3종 문장, cost 정규화와 progress 미사용, 비교군, 보정 규칙(오탐률 5% 이하), 반복 3회, 성공 기준 (설계 §11).
3. **정책 엄격도 순서.** LENIENT·BALANCED·STRICT 의 `base_threshold` 가 지금 셋 다 0.2 다. BALANCED 는 기본값이라 바꾸면 기본 개입 빈도가 달라진다. 이 결정을 기다리는 xfail 이 1건 있다.
4. **θ_min, Q_min.** 실험 1 사전 등록 때 정한다. 평가 실행 전에 커밋해야 한다 (설계 §8.1).
5. **cost/progress 측정법.** progress 는 실행 시점에 순환 없이 잴 방법을 찾지 못해 실험 1 에서 쓰지 않기로 제안돼 있다 (설계 §6).
6. **본 실험 모델.** 예비 실행 결과를 보고 정한다.
7. **앵커 입력 기준.** 거의 같은 앵커를 걸러내는 수치 기준을 넣을지와 그 값, 뜻이 비슷한 문장도 거부할지, 앵커가 전체 공간을 채우면 거부할지 (제안 문서 §9). 이 결정을 기다리는 xfail 이 2건 있다.
8. **용어 레코드 갱신.** `ontology/records.py` 의 세 레코드는 2026-10-10 시점(커밋 `95b7086`) 기준이고 `next_check` 기한이 지났다. `THETA_INTEGRITY` 는 θ 함수 2개가 공존한다는 근거를 담고 있는데 D4 로 하나가 됐으므로 근거를 다시 써야 한다. 레코드 승인은 Bell 만 할 수 있다.

의존 관계: 6 은 1 의 예비 실행 결과를 보고 정한다. 4 의 임계값과 5 의 cost 정규화 상수는 보정 분할 실행에서 나오므로, 하네스 구현(§7)과 2 의 승인이 먼저다. 7 중 "뜻이 비슷한 문장" 은 실제 임베딩 측정(`anchor_criteria --real`)이 먼저다.

## 9. 알려진 불일치

- BCDSI 의 풀이가 파일마다 다르다. README 는 "Brain–Computer Divergence Safety Intervention", `bcdsi/__init__.py` 는 "Quantum Coherent Bias Detection System Intervention" 이다.
- README 의 Echo Gateway 비교표는 Safety Layer 를 "BCDSI + Quantum Uncertainty" 로 적고 있다. 현재 게이트웨이의 안전 검사는 스텁이고, `echo_gateway/` 는 `bcdsi/` 를 가져오지 않는다 (§3). `middleware/bcdsi_integration.py` 는 테스트에서만 쓰인다.
- `docs/` 의 PHASE·MERGE·PR 로 시작하는 문서들은 2026년 1~4월 작업의 기록이다. 현재 상태의 기준은 이 문서와 `docs/experiments/` 다.
- 남아 있는 옛 브랜치: `phase4-server`(`.venv` 폴더가 커밋돼 있음), `phase4-gateway-server`, `claude/claude-md-…`. 정리 여부는 정해지지 않았다.

## 10. 작업 규칙

- 작업은 새 브랜치에서 하고 PR 로 올린다. main 에 직접 push 하지 않는다. 병합된 PR 의 브랜치는 저장소 설정으로 자동 삭제된다.
- 물리 용어(E_break, θ_integrity, ρ, ΔS, ΔC, ℕ, Q)를 다른 분야의 용어로 바꿔 부르지 않는다.
- 승인되지 않은 값은 실험 1 문서의 표기(승인 / 제안 / 확인)대로 제안으로 둔다. 승인은 Bell 이 PR 댓글로 남긴 것만 인정한다.
- 테스트 통과를 물리적 타당성이나 위험 탐지 성능의 검증으로 쓰지 않는다.
- 유료 실행, 배포, 외부 발송은 Bell 의 승인 전에 하지 않는다.
- 공개 저장소다. README, 커밋 메시지, 문서에 비밀값(API 키 등)과 개인 이야기를 넣지 않는다.
- AI 가 쓴 댓글·커밋·검토에는 작성 주체를 밝힌다.
- AI 간 작업 조율은 이슈 #16 에 기록한다.

## 11. 이 문서 밖에 있는 것

claude.ai 프로젝트 문서와 Jetpost 비공개 노트에도 상태 기록이 있지만 다른 AI 는 읽을 수 없다. 인계에 필요한 내용은 이 문서에 옮겼다. 두 곳의 내용과 이 문서가 다르면 이 문서와 코드가 기준이다.
