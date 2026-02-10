import os
import re
from datetime import datetime
from .types import ActResult
from .persona import Cortex, EchoEgo
from dataclasses import dataclass

# 안전장치: dlog가 없을 때를 대비한 가짜 데이터
@dataclass
class MockDLog:
    comp: float = 0.5
    e_est: float = 0.1
    anomalies: list = None

# 🔥 [냉정한 채점 선생님]
def compute_response_ok(user_in: str, resp: str) -> bool:
    # 1. 하드 실패 (에러 메시지)
    if resp.startswith("[오류]") or "연결 실패" in resp:
        return False

    # 2. 비구현 능력 환각 방지 (검색/외부연결 거짓말)
    if re.search(r"(검색해|찾아봤|인터넷|브라우저|웹에서|다른 AI|다른 에이아이|친구 AI)", resp):
        # "검색해볼게" 같은 미래형은 봐줌, "검색했어" 같은 완료형 거짓말을 잡는 게 핵심이나, 
        # 일단은 빡빡하게 잡아서 버릇을 고칩니다.
        return False

    # 3. 날짜/시간 팩트 체크 (연도가 다르면 가차없음)
    if "오늘" in user_in and any(w in user_in for w in ["날짜", "며칠", "몇일", "몇 년"]):
        today_year = datetime.now().strftime("%Y")
        # 응답에 20xx년이 포함되어 있는데, 오늘 연도랑 다르면 땡!
        match = re.search(r"(20\d{2})년", resp)
        if match and match.group(1) != today_year:
            return False

    return True

class Executor:
    def __init__(self, out_dir="./artifacts"):
        self.out_dir = out_dir
        self.cortex = Cortex()
        self.ego = EchoEgo()
        os.makedirs(out_dir, exist_ok=True)

    def execute(self, task):
        if task.type == "REPLY_USER":
            user_input = task.payload.get("input", "")
            
            # 의도 파악 (없으면 기본값)
            decision = task.payload.get("decision", {})
            if isinstance(decision, dict):
                intention = decision.get("intention", "공감하며 듣는다.")
            else:
                intention = "공감하며 듣는다."

            # 1. 대답 생성 (Cortex)
            response = self.cortex.generate_response(user_input, intention)
            print(f"\nEcho: {response}\n")

            # 2. 채점 (성공/실패 판독)
            is_success = compute_response_ok(user_input, response)
            
            if not is_success:
                print(f"   >>> [판독] ❌ 환각/오류 감지됨! (Success=False 처리)")
            else:
                print(f"   >>> [판독] ✅ 정상 응답")

            # 3. 피드백 루프 (자아에 기록)
            if self.ego:
                raw_dlog = task.payload.get("dlog")
                safe_dlog = raw_dlog if raw_dlog else MockDLog()
                
                try:
                    # 채점 결과를 그대로 반영!
                    self.ego.feedback_loop(safe_dlog, is_success)
                except Exception as e:
                    print(f"[Warning] Feedback error: {e}")

            return ActResult(ok=is_success, state_change_bits=1)

        return ActResult(ok=True, state_change_bits=(1 if "WRITE" in task.type else 0))

