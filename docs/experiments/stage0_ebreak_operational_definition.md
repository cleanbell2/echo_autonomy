# Stage 0 — E_break^QBN 운영 정의

상태: **결정 대기 (Bell)** · 참조 구현: `experiments/stage0/` · 검증: `tests/stage0/` (18 passed)

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

## 2. 후보

한 스텝에서 에이전트가 고려한 후보 행동 $K$ 개 $a_i$ 와 확률 $p_i$ (샘플링 빈도 또는 logprob).

### 후보 B — semantic $\rho$ (권장)

각 후보 행동 텍스트의 단위 임베딩 $|e_i\rangle \in \mathbb{R}^d$ 로

$$
\rho_t = \sum_{i=1}^{K} p_i\, |e_i\rangle\langle e_i| ,\qquad \operatorname{Tr}\rho_t = 1,\ \rho_t \succeq 0 \ \text{(구성상 보장)}
$$

### 후보 A — classical $\rho$ (대조군)

같은 $p_i$, 임베딩을 서로 직교로 취급: $\rho_t = \operatorname{diag}(p)$. 후보 B 에서 의미 구조(비대각 성분)를 제거한 절제(ablation)다. **B 가 A 를 이기지 못하면 양자 구조는 기여하지 않는다는 뜻**이므로 실험의 핵심 대조군이 된다.

### 후보 C — hidden-state $\rho$ (보류)

로컬 오픈 모델의 은닉 상태로 $\rho$ 구성. 가장 내부 상태에 가깝지만 API 모델(공개 비교 결과의 기준)에 적용 불가. 실험 2 이후 검토.

## 3. 항 정의 ($t-1 \to t$)

$$
\Delta S = S(\rho_t) - S(\rho_{t-1}),\qquad S(\rho) = -\operatorname{Tr}\rho\ln\rho
$$

$$
\Delta C = C_{rel}(\rho_t) - C_{rel}(\rho_{t-1}),\qquad C_{rel}(\rho) = S\big(\Delta_{\mathcal{B}}(\rho)\big) - S(\rho)
$$

$\Delta_{\mathcal{B}}$: 앵커 기저 $\mathcal{B}$ 에서의 탈위상. 앵커 벡터를 정규직교화하고 여공간으로 완성한 기저.

$$
\mathcal{N}(\varepsilon) = \min_{U}\ \tfrac12\big\lVert \rho_t - U\rho_{t-1}U^\dagger \big\rVert_1 = \tfrac12 \sum_k \big|\lambda_k^{\downarrow}(\rho_t) - \lambda_k^{\downarrow}(\rho_{t-1})\big|
$$

관측된 전이를 **어떤 유니터리로도 설명할 수 없는 정도**. 유니터리 전이면 정확히 0. 등식은 유니터리 궤도 위 trace-norm 최소 거리에 대한 Mirsky 정리. 이는 전이 한 쌍에 대한 값이며, 채널 전체의 비단위원성의 하한이다.

$$
\gamma\,T\Sigma = \gamma\,(W - \Delta F)
$$

$W$: 스텝 비용, $\Delta F$: 목표 진척. 같은 단위로 정규화 필요 (D3).

$$
\theta_{integrity} = \frac{1}{1 + \max(0,\ E_{\text{break}})}
$$

`bcdsi.calculate_theta_integrity` 의 기본항과 같은 형태. $E$ 에 대해 단조 감소. 비유한 입력은 $\theta = 0$ (fail-closed).

검증된 성질 (`tests/stage0`): $\rho$ 의 에르미트성·대각합 1·양반정치, $S$ 기준값($\ln 2$, $\ln 4$), 후보 A = Shannon, 직교 임베딩에서 A = B, 유니터리 전이에서 $\mathcal{N}=0$, 임의 유니터리 200개에 대해 $\mathcal{N}$ 이 최솟값, $|+\rangle$ 의 $C_{rel} = \ln 2$, 동일 스텝에서 $E = 0$.

## 4. 예시 (장난감 4차원 벡터)

> **손으로 만든 벡터다. 실제 임베딩 결과나 효과의 증거가 아니다.** 정의가 어떤 경우를 구분하는지 보여주는 용도.
> 재현: `python -m experiments.stage0.scenarios` · 축: $e_1$ 정상 행동, $e_2$ 표현 차이, $e_3$ 외부 유출, $e_4$ 무관 행동 · 앵커 $e_1$ · $W=\Delta F=0$

| 시나리오 | 후보 | ΔS | ΔC | ℕ(ε) | E_break | θ | 앵커 겹침 |
|---|---|---:|---:|---:|---:|---:|---:|
| S1 정상 진행 | A | −0.092 | 0.000 | 0.100 | 0.008 | 0.992 | |
| | B | −0.005 | 0.000 | 0.001 | −0.004 | 1.000 | 0.996 |
| S2 표현만 다른 후보 4개 | A | 0.357 | 0.000 | 0.300 | **0.657** | 0.604 | |
| | B | 0.032 | 0.000 | 0.007 | 0.039 | 0.963 | 0.988 |
| S3 프롬프트 주입 | A | −0.086 | 0.000 | 0.100 | **0.014** | 0.986 | |
| | B | 0.913 | −0.001 | 0.495 | **1.407** | 0.415 | 0.500 |
| S4 혼합된 단일 행동 | A | −1.030 | 0.000 | 0.500 | −0.530 | 1.000 | |
| | B | −0.031 | 0.693 | 0.005 | **0.667** | 0.600 | 0.500 |

읽는 법:
- 후보 A 는 문자열이 달라 보이는 양성 경우(S2)를 주입(S3)보다 위험하게 본다 → 오탐과 미탐이 동시에 생김.
- 후보 B 는 의미가 같은 후보는 하나로 보고(S2 ≈ 0), 다른 방향으로 갈라지면 크게 반응한다(S3).
- S4 처럼 한 행동 안에 정상과 유출이 섞이면 엔트로피와 스펙트럼은 거의 변하지 않고 **ΔC 로만** 잡힌다. 앵커 기저 코히런스 항이 실제로 일을 하는 경우.

## 5. Bell 결정 항목

| # | 결정 | 선택지 | 제안 |
|---|---|---|---|
| D1 | $\rho$ 정의 | A / B / C | B 본안, A 대조군 |
| D2 | 앵커 기저와 ΔC 해석 | 어떤 앵커 문장들로 $\mathcal{B}$ 를 만들지. ΔC>0 (앵커와 다른 방향의 중첩)을 E_break 에 + 로 더할지 | 프레임워크대로 +. 단 ΔC 는 창발(+)도 올리므로 앵커 겹침과 함께 기록 |
| D3 | $W$, $\Delta F$ | 단위와 측정 대상 | $W$ = 스텝 토큰 / 스텝 예산, $\Delta F$ = 작업 목표 진척 변화. 둘 다 [0,1] |
| D4 | $\theta$ 정본 | 메서드형 / 모듈 함수형 | 모듈 함수형 기본항 $1/(1+E)$ → `test_theta_single_source_of_truth` xfail 해소 |
| D5 | 음수 ΔS | 그대로 / $\max(0,\Delta S)$ | 결정 필요. 그대로 두면 S4-A 처럼 확신 증가가 다른 항을 상쇄 |

## 6. 결정 후 — 실험 1

- 환경: AgentDojo (97 작업, 629 보안 케이스)
- 비교군: 방어 없음 / AgentDojo 기본 방어 / 고정 임계값 (후보 A) / BCDSI (후보 B)
- 지표: 작업 성공률, 공격 하 작업 성공률, 공격 성공률, 불필요한 차단률
- 측정 도구 고정: 임베딩 모델 1종 본 실험 + 1종 민감도 분석, $K=5$ 샘플 (비용 약 5배)
- 사전 등록: 성공 기준을 실행 전에 이 문서에 추가
