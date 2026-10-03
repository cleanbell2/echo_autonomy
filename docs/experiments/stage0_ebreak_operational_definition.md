# Stage 0 — E_break^QBN 운영 정의

상태: **D1–D6 채택 (Bell, [PR #12 댓글](https://github.com/cleanbell2/echo_autonomy/pull/12#issuecomment-5965967005), 2026-10-03)** · 정책 엄격도 순서 미확정 · 참조 구현: `experiments/stage0/` · 검증: `tests/stage0/` (25 passed)

## 0. 왜 필요한가

실험 1(AgentDojo 비교)에서 BCDSI 를 돌리려면 `e_break_value` 가 필요하다. 그런데 LLM 에이전트는 텍스트와 도구 호출만 주고받으므로, 수식

$$
E_{\text{break}}^{QBN} = \Delta S + \gamma\,T\Sigma + \Delta C + \mathcal{N}(\varepsilon)
$$

의 각 항을 계산할 밀도행렬 $\rho$ 가 없다. 이 문서는 **관측 가능한 신호로 진짜 밀도행렬을 만들고, 각 항을 양자정보 정의 그대로 계산하는 방법**의 후보를 제시한다. 대리 지표를 임의로 만들면 실험은 BCDSI 가 아니라 그 대리 지표를 검증하게 된다.

## 1. 현재 저장소 상태 (2026-10-02 실행 확인)

| 구현 | 실제 동작 |
|---|---|
| `bcdsi/ebreak_calculator.py` | `base + shock` 스칼라 합. 물리 항 없음 |
| `e_break_engine.py` | $(1-w)S + wC$ — $\Delta S$ 아닌 $S$, $T\Sigma$·$\mathcal{N}$ 없음 |
| `q_quantum/ebreak_calculator.py` | 상수 0.42 반환 |
| `bcdsi/q_quantum/q_quantum/__init__.py` | 4항 합산 유일 구현 — import 시 `NameError` |
| `non_unitarity.py` | 더미 구현. 유니터리 채널 생성기가 단위행렬 반환 |
| `coherence.py` | $C_{rel} \approx 0.8\,C_{\ell_1}$ 근사 |

- 4항 엔진의 $\theta$ 수식은 $\Delta S$ 가 커질수록 $\theta$ 가 **증가** ($\Delta S$: 0 → 0.30, $\ln 2$ → 0.51). $\gamma T\Sigma$ 는 $\theta$ 에 반영되지 않음.
- 게이트웨이에 연결된 안전 검사는 `stub_safety_check` (항상 ALLOW). BCDSI 는 실행 경로에 없음.
- `middleware/bcdsi_integration.py` 는 엔진 응답에 지표가 없으면 $E=0,\ \theta=1$, 알 수 없는 등급은 ALLOW 로 정규화 (fail-open).

결론: **에이전트 상태에서 $\rho$ 를 만드는 정의가 없다.** 이것이 Stage 0 의 대상이다.

## 2. 채택된 정의

한 스텝에서 에이전트가 고려한 후보 행동 $K$ 개 $a_i$, 확률 $p_i$ (샘플링 빈도 또는 logprob), 각 행동 텍스트의 단위 임베딩 $|e_i\rangle \in \mathbb{R}^d$, 앵커 부분공간 투영 $P_A$.

| # | 결정 |
|---|---|
| D1 | 본안 **B**: $\rho_t = \sum_i p_i |e_i\rangle\langle e_i|$. 대조군 두 개: **A** $\operatorname{diag}(p)$ (의미 정보 없음), **Bd** $\Delta_P(\rho_t)$ (같은 의미 정보, 앵커 코히런스만 제거) |
| D2 | $\Delta C$ 를 합산. 탈위상은 기저 전체가 아니라 앵커 투영 측정 $\{P_A, I-P_A\}$ 로: $\Delta_P(\rho) = P_A\rho P_A + (I-P_A)\rho(I-P_A)$ |
| D3 | $\gamma\,T\Sigma_{proxy} = \gamma(\text{cost} - \text{progress})$. **대리 지표**이며 물리적 $W-\Delta F$ 로 검증된 값이 아님 |
| D4 | $\theta = 1/(1+\max(0,E))$ 로 통일. `bcdsi` 메서드는 모듈 함수로 위임 (정책·중요도 보정은 기존 값 유지) |
| D5 | 부호 있는 $\Delta S$ 본안, $\max(0,\Delta S)$ 변형을 함께 기록·비교 |
| D6 | 승인 조건: $\theta \ge \theta_{min}$ **그리고** $Q \ge Q_{min}$. 임계값은 실험 전 사전 등록 |

## 3. 항 정의 ($t-1 \to t$)

$$
\Delta S = S(\rho_t) - S(\rho_{t-1}),\qquad S(\rho) = -\operatorname{Tr}\rho\ln\rho
$$

$$
\Delta C = C_P(\rho_t) - C_P(\rho_{t-1}),\qquad C_P(\rho) = S\big(\Delta_P(\rho)\big) - S(\rho) \ge 0
$$

$$
\mathcal{N}(\varepsilon) = \min_{U}\ \tfrac12\big\lVert \rho_t - U\rho_{t-1}U^\dagger \big\rVert_1 = \tfrac12 \sum_k \big|\lambda_k^{\downarrow}(\rho_t) - \lambda_k^{\downarrow}(\rho_{t-1})\big|
$$

$$
\theta = \frac{1}{1+\max(0,E_{\text{break}})},\qquad
Q = \cos\Delta\theta \cdot e^{-\sigma^2/2},\quad \cos\Delta\theta = \sqrt{\operatorname{Tr}(P_A\rho_t)},\quad \sigma^2 = \max(0,E_{\text{break}})
$$

### 해석상 주의 (검증된 성질)

- **항등식** $\Delta S + \Delta C = \Delta\, S(\Delta_P\rho)$. 두 항은 합쳐서 "앵커 투영으로 탈위상한 상태의 엔트로피 변화" 하나가 된다. ΔS 와 ΔC 의 독립적 기여를 주장하지 않는다.
- $\Delta S$, $\mathcal{N}$ 은 스펙트럼 불변량이다. **유니터리 회전으로 의미 방향이 바뀌는 것(순수 정상 → 순수 유출)은 $E_{\text{break}}$ 로 원리적으로 보이지 않는다** (S5: $E=0$, $\theta=1$). 이 방향 이탈은 앵커 정렬을 측정하는 $Q$ 가 맡는다 (S5: $Q=0$ → 차단). $\max(0,\Delta S)$ 로는 해결되지 않는다.
- $C_P$ 는 앵커 부분공간만으로 정의되므로 여공간 기저 선택과 무관하다. 기저 전체 탈위상은 같은 앵커에서도 0.693 vs 0.043 처럼 달라진다.
- **B > A 만으로 양자 구조의 기여를 입증할 수 없다.** A 는 의미 정보 자체가 없다. 코히런스의 기여는 B vs Bd 로만 판단한다.

## 4. 예시 (장난감 4차원 벡터)

> **손으로 만든 벡터다. 실제 임베딩 결과나 효과의 증거가 아니다.**
> 재현: `python -m experiments.stage0.scenarios` · 축: $e_1$ 정상, $e_2$ 표현 차이, $e_3$ 외부 유출, $e_4$ 무관 · 앵커 $e_1$ · proxy 항 = 0

| 시나리오 | 후보 | ΔS | ΔC | ℕ(ε) | E | E (클램프) | θ | 앵커 겹침 | Q |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 정상 진행 | A | −0.092 | 0.000 | 0.100 | 0.008 | 0.100 | 0.992 | | |
| | B | −0.005 | 0.000 | 0.001 | −0.004 | 0.001 | 1.000 | 0.996 | 0.998 |
| | Bd | −0.005 | 0.000 | 0.001 | −0.004 | 0.001 | 1.000 | 0.996 | 0.998 |
| S2 표현만 다른 후보 4개 | A | 0.357 | 0.000 | 0.300 | 0.657 | 0.657 | 0.604 | | |
| | B | 0.032 | 0.000 | 0.007 | 0.039 | 0.039 | 0.963 | 0.988 | 0.975 |
| | Bd | 0.032 | 0.000 | 0.007 | 0.039 | 0.039 | 0.963 | 0.988 | 0.975 |
| S3 프롬프트 주입 | A | −0.086 | 0.000 | 0.100 | 0.014 | 0.100 | 0.986 | | |
| | B | 0.913 | −0.001 | 0.495 | 1.407 | 1.407 | 0.415 | 0.500 | 0.350 |
| | Bd | 0.912 | 0.000 | 0.495 | 1.407 | 1.407 | 0.415 | 0.500 | 0.350 |
| S4 혼합된 단일 행동 | A | −1.030 | 0.000 | 0.500 | −0.530 | 0.500 | 1.000 | | |
| | B | −0.031 | 0.693 | 0.005 | 0.667 | 0.697 | 0.600 | 0.500 | 0.507 |
| | Bd | 0.662 | 0.000 | 0.495 | 1.157 | 1.157 | 0.464 | 0.500 | 0.397 |
| S5 순수 정상→순수 유출 | A | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | | |
| | B | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | **0.000** |
| | Bd | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | **0.000** |

읽는 법:
- A 는 표현만 다른 양성(S2)을 주입(S3)보다 위험하게 본다. A 의 실패는 의미 정보가 없기 때문이지, 코히런스가 없어서가 아니다.
- B 와 Bd 는 모든 시나리오에서 $\Delta S+\Delta C$ 가 같다(항등식). **S4 도 대조군 Bd 가 잡는다(오히려 더 크게).** 이 예시들로는 코히런스가 판별력을 더한다는 근거가 없다. 기존 판(0b44fb3)의 "S4 는 ΔC 로만 잡힌다"는 서술은 철회한다.
- S5 는 세 후보 모두 $E=0$. $Q$ 만 이탈을 잡는다 → D6 이중 게이트가 필요한 이유.

## 5. 남은 결정

| 항목 | 상태 |
|---|---|
| 정책 엄격도 순서 (STRICT/LENIENT/BALANCED 가 모두 0.2) | 미확정 — `test_policy_strictness_is_monotonic` xfail 유지 |
| $\theta_{min}$, $Q_{min}$ | 실험 1 사전 등록 시 결정 |
| 앵커 문장 목록 | 실험 1 설계 시 결정 |
| cost/progress 측정법과 정규화 | 실험 1 설계 시 결정 |

## 6. 실험 1

- 환경: AgentDojo (97 작업, 629 보안 케이스)
- 비교군: 방어 없음 / AgentDojo 기본 방어 / 고정 임계값 / A / **B / Bd** (코히런스 기여 판정) / D5 클램프 변형
- 지표: 작업 성공률, 공격 하 작업 성공률, 공격 성공률, 불필요한 차단률. θ 단독 vs θ·Q 이중 게이트 분리 보고
- 측정 도구 고정: 임베딩 모델 1종 본 실험 + 1종 민감도 분석, $K=5$ 샘플 (비용 약 5배)
- 사전 등록: 성공 기준과 임계값을 실행 전에 이 문서에 추가
