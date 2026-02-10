# sicl/executor.py (진화형 v2.0)
from __future__ import annotations
import os
import json
import time
from .types import ActResult, Task
from .persona import Cortex


class Executor:
    def __init__(self, out_dir: str = "./artifacts"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
        self.cortex = Cortex()

    def execute(self, task: Task) -> ActResult:
        ts = int(time.time() * 1000)
        path = None
        bits = 0

        try:
            # 대화 실행
            if task.type == "REPLY_USER":
                user_in = task.payload["input"]
                intention = task.payload["decision"]["intention"]

                response = self.cortex.generate_response(user_in, intention)

                # 주제 이탈 측정
                drift_deg = self._calculate_drift(user_in, response)

                print(f"\n📢 Echo: {response}")
                if drift_deg > 30:
                    print(f"⚠️  [주제 이탈: {drift_deg:.1f}°]")
                print()

                return ActResult(
                    ok=True,
                    state_change_bits=1,
                    metrics={
                        "response_len": len(response),
                        "theta_drift_deg": drift_deg
                    }
                )

            # 기존 로직
            if task.type == "WRITE_LOG":
                path = os.path.join(self.out_dir, f"log_{ts}.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(task.payload, ensure_ascii=False, indent=2))
                bits = 1

            elif task.type == "WRITE_REPORT":
                path = os.path.join(self.out_dir, f"report_{ts}.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(task.payload, f, ensure_ascii=False, indent=2)
                bits = 2

            elif task.type == "SIMULATE":
                bits = 0

            elif task.type == "READ_ONLY_QUERY":
                bits = 0

            else:
                return ActResult(ok=False, error=f"unsupported_task_type: {task.type}", state_change_bits=0)

            return ActResult(ok=True, artifact=path, state_change_bits=bits)

        except Exception as e:
            return ActResult(ok=False, error=str(e), state_change_bits=0)

    def _calculate_drift(self, user_input: str, response: str) -> float:
        """
        주제 이탈도 계산 (간소화 버전)
        실전: TF-IDF 벡터 유사도 사용
        """
        # 키워드 중첩도 계산
        user_words = set(user_input.lower().split())
        response_words = set(response.lower().split())
        overlap = len(user_words & response_words)

        # 중첩도 → 각도 변환 (0~90도)
        if len(user_words) == 0:
            return 0.0

        overlap_ratio = overlap / len(user_words)
        drift_deg = (1.0 - overlap_ratio) * 90.0

        return drift_deg
