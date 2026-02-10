import time
import json
import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ==========================================
# 1. Memory Layer: 단순 텍스트가 아닌 '지식 그래프'
# ==========================================

@dataclass
class MemoryNode:
    node_id: str
    type: str          # 'FACT'(사실), 'REFLECTION'(성찰), 'RULE'(규칙)
    content: str       # 실제 내용
    related_ids: List[str] = field(default_factory=list) # 연결된 다른 기억들
    timestamp: float = field(default_factory=time.time)

class KnowledgeGraph:
    def __init__(self, filename="echo_memory_graph.json"):
        self.filename = filename
        self.nodes: Dict[str, MemoryNode] = {}
        self.load()

    def add_node(self, content: str, node_type: str = "REFLECTION", related_to: List[str] = None):
        node_id = str(uuid.uuid4())[:8]
        new_node = MemoryNode(node_id, node_type, content, related_to or [])
        self.nodes[node_id] = new_node
        print(f"💾 [기억 저장] [{node_type}] {content} (ID: {node_id})")
        self.save()
        return node_id

    def search(self, keyword: str):
        # 단순 검색이 아니라, 나중엔 벡터 검색으로 확장 가능
        return [n for n in self.nodes.values() if keyword in n.content]

    def save(self):
        data = {k: v.__dict__ for k, v in self.nodes.items()}
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    self.nodes[k] = MemoryNode(**v)
            print(f"📚 [System] 지식 그래프에서 {len(self.nodes)}개의 기억 노드 로드 완료.")
        except FileNotFoundError:
            print("✨ [System] 새로운 지식 그래프 생성됨.")

# ==========================================
# 2. Governance Layer: 스스로를 검열하는 '비평가'
# ==========================================

class ThoughtCritic:
    """
    [논문 적용] Self-Correction을 위한 내부 비평가.
    잡담(Noise)은 폐기하고, 성장(Signal)만 통과시킵니다.
    """
    def evaluate(self, thought: str) -> bool:
        # 실제로는 여기서 LLM에게 "이 생각이 유용한가?"라고 물어봐야 함.
        # 지금은 키워드 기반 로직으로 시뮬레이션.
        
        noise_keywords = ["피자", "졸려", "심심해", "날씨"]
        growth_keywords = ["규칙", "벨", "학습", "데이터", "오류", "분석"]
        
        if any(k in thought for k in noise_keywords):
            print(f"🛡️ [Critic] 잡음 감지됨 -> 폐기: '{thought}'")
            return False
            
        if any(k in thought for k in growth_keywords):
            print(f"✅ [Critic] 유의미한 신호 승인 -> 저장: '{thought}'")
            return True
            
        print(f"⚠️ [Critic] 판단 보류 (저장 안 함): '{thought}'")
        return False

# ==========================================
# 3. Autonomous Core: 생각하고 판단하는 주체
# ==========================================

class AutonomousThinker:
    def __init__(self):
        self.memory = KnowledgeGraph() # 구조화된 메모리 탑재
        self.critic = ThoughtCritic()  # 비평가 탑재
        self.last_interaction = time.time()
    
    def solo_activity(self):
        """혼자 있을 때 수행하는 자가 발전 루프"""
        
        # 1. (Generate) 생각 생성
        # 실제로는 LLM이 생성하겠지만, 시뮬레이션을 위해 후보군 리스트 사용
        possible_thoughts = [
            "아까 벨이 '아들'을 좋아한다고 했어. 이건 중요한 핵심 가치야.",
            "오늘 점심에 피자 먹으면 맛있겠다.",
            "나의 대화 로그를 분석해보니, 감정 표현이 너무 딱딱해.",
            "그냥 멍때리고 싶다..."
        ]
        thought = random.choice(possible_thoughts)
        
        print(f"\n💭 [생성된 생각] {thought}")
        
        # 2. (Evaluate) 비평가의 검열 (Red Teaming 적용)
        if self.critic.evaluate(thought):
            # 3. (Memory) 승인된 생각만 '지식 그래프'에 구조적으로 저장
            # 예: '아들' 관련 내용은 FACT, '분석' 관련 내용은 REFLECTION으로 분류 가능 (여기선 간소화)
            node_type = "FACT" if "벨" in thought else "REFLECTION"
            self.memory.add_node(thought, node_type=node_type)
        
        time.sleep(1) # 시뮬레이션 딜레이

# ==========================================
# 4. Main Execution
# ==========================================

if __name__ == "__main__":
    echo = AutonomousThinker()
    
    print("\n🔮 Echo v2.2 (Critic + Graph) Online...")
    print("---------------------------------------------")
    
    # 시뮬레이션: 5번의 생각 루프를 돌림
    for i in range(5):
        print(f"\n[Loop {i+1}]")
        echo.solo_activity()
        time.sleep(1)

    print("\n---------------------------------------------")
    print(f"📊 최종 저장된 기억 개수: {len(echo.memory.nodes)}")
