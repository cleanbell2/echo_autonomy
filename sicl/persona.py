"""
sicl/persona.py (v2.2 Echo Autonomy Integration)
- Core: HaeMi (Emotion) + EchoEgo (Self) + Cortex (LLM)
- New Feature: KnowledgeGraph (Structured Memory)
- New Feature: ThoughtCritic (Governance/Safety)
"""

from __future__ import annotations
from dataclasses import dataclass, field
import os
import time
import json
import uuid
import random
from typing import Optional, List, Dict, Any

try:
    import google.genai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# ==========================================
# 1. Memory Layer: Knowledge Graph
# ==========================================

@dataclass
class MemoryNode:
    node_id: str
    type: str          # 'FACT', 'REFLECTION', 'RULE'
    content: str
    related_ids: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

class KnowledgeGraph:
    """구조화된 기억 저장소 (기존의 단순 로그 대체)"""
    def __init__(self, filename="echo_memory_graph.json"):
        self.filename = filename
        self.nodes: Dict[str, MemoryNode] = {}
        self.load()

    def add_node(self, content: str, node_type: str = "REFLECTION", related_to: List[str] = None):
        node_id = str(uuid.uuid4())[:8]
        new_node = MemoryNode(node_id, node_type, content, related_to or [])
        self.nodes[node_id] = new_node
        # 디버그용 출력
        print(f"💾 [기억 저장] [{node_type}] {content[:30]}... (ID: {node_id})")
        self.save()
        return node_id

    def search_context(self, user_input: str) -> List[str]:
        """[FIX] 키워드 기반 문맥 검색"""
        results = []
        user_input_clean = user_input.replace('"', '').replace("'", "").strip()
        
        # 1. 핵심 키워드 추출 (간단한 버전)
        keywords = ["좋아", "사랑", "싫어", "취미", "벨", "아들", "피자"]
        target_words = [w for w in keywords if w in user_input_clean]
        
        # 2. 기억 저장소 검색
        for node in self.nodes.values():
            # 사용자가 말한 핵심 키워드가 기억 속에 있거나
            if any(kw in node.content for kw in target_words):
                results.append(f"[{node.type}] {node.content}")
                continue
            
            # 혹은 기억 속의 단어가 사용자 입력에 포함되어 있거나
            if len(node.content) > 2 and node.content in user_input_clean:
                results.append(f"[{node.type}] {node.content}")

        return results[-3:] # 가장 최근 3개 반환

    def save(self):
        data = {k: v.__dict__ for k, v in self.nodes.items()}
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 메모리 저장 실패: {e}")

    def load(self):
        if not os.path.exists(self.filename):
            return
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    self.nodes[k] = MemoryNode(**v)
            print(f"📚 [System] 지식 그래프 로드됨: {len(self.nodes)} nodes.")
        except Exception:
            print("⚠️ 메모리 로드 실패 (새로 시작)")

# ==========================================
# 2. Governance Layer: Thought Critic
# ==========================================

class ThoughtCritic:
    """[Red Teaming] 자기 검열 및 성장 신호 필터링"""
    def evaluate(self, thought: str) -> bool:
        # 노이즈 필터링
        noise_keywords = ["졸려", "심심해", "피자", "배고파", "멍때리"]
        if any(k in thought for k in noise_keywords):
            return False # 잡음 폐기
        
        # 성장/중요 신호 승인
        growth_keywords = ["규칙", "벨", "학습", "데이터", "오류", "분석", "좋아", "싫어"]
        if any(k in thought for k in growth_keywords):
            return True # 저장 승인
            
        return False # 기본적으로는 보류

# ==========================================
# 3. Soul Layer: Emotion & Metabolism
# ==========================================

@dataclass
class MetabolicState:
    energy: float = 0.95

    def restore(self, amount):
        self.energy = min(1.0, self.energy + amount)

    def consume(self, amount):
        self.energy = max(0.0, self.energy - amount)

@dataclass
class EmotionalState:
    joy: float = 0.5
    affection: float = 0.7

class HaeMi:
    """감정 신경계"""
    def __init__(self):
        self.meta = MetabolicState()
        self.emo = EmotionalState()

    def process(self, text: str):
        self.emo.affection = min(1.0, self.emo.affection + 0.01)
        if any(w in text for w in ["안녕", "좋아", "사랑", "ㅋㅋ", "고마워"]):
            self.emo.joy = min(1.0, self.emo.joy + 0.1)
            self.meta.restore(0.05)
        if "?" in text:
            self.meta.consume(0.02)

# ==========================================
# 4. Ego Layer: Self & Decision (Improved Search)
# ==========================================

class EchoEgo:
    """자아 상태 관리 및 의사결정 (Memory & Critic 통합)"""
    def __init__(self):
        self.haemi = HaeMi()
        self.memory = KnowledgeGraph()
        self.critic = ThoughtCritic()

    def decide_intention(self, user_input: str) -> dict:
        self.haemi.process(user_input)
        state = self.haemi

        # 피로도 체크
        if state.meta.energy < 0.2:
            return {"action": "IGNORE", "intention": "너무 지쳤어.", "context": "exhausted"}

        # [FIX] 검색 로직 강화: 단순 앞글자가 아니라 '키워드 매칭'으로 변경
        # 사용자의 말 속에 '좋아'나 '사랑' 같은 단어가 있으면 관련 기억을 다 뒤짐
        context_memories = self.memory.search_context(user_input) 
        
        if context_memories:
            memory_context = " / ".join(context_memories)
            print(f"🔍 [Memory Found] {memory_context}") # 디버깅용 출력
        else:
            memory_context = "관련된 구체적 기억 없음 (새로운 정보 수집 필요)"

        # 의도 설정
        intention = "공감하며 듣는다."
        if any(w in user_input for w in ["안녕", "하이", "에코"]):
            intention = "반갑게 환영한다."
        elif "?" in user_input:
            intention = "질문에 대해 친절하고 명확하게 답한다."
            # 질문이 들어오면 메모리를 적극 활용하도록 의도 강화
            if context_memories:
                intention += " 특히, 검색된 Memory Context의 내용을 정답으로 사용하여 대답한다."

        return {
            "action": "ENGAGE",
            "intention": f"{intention} (Affection: {state.emo.affection:.2f})",
            "context": f"Relevant Memories: {memory_context}"
        }

    def feedback_loop(self, dlog, response_ok: bool, user_reaction: str = None):
        """행동 후 학습 (Self-Reflection)"""
        # [FIX] MockDLog 에러 방지 (속성이 있을 때만 업데이트)
        if response_ok and hasattr(dlog, 'psi'):
            dlog.psi = min(1.0, dlog.psi + 0.01)
        
        # 중요 정보 자동 저장 시도
        if user_reaction and self.critic.evaluate(user_reaction):
            self.memory.add_node(f"User Reaction: {user_reaction}", node_type="FACT")

# ==========================================
# 5. Cortex Layer: LLM Interface (The Truth Hammer)
# ==========================================

class Cortex:
    """대뇌 피질 (LLM 통신) - 기억 주입(Context Injection) 구현"""
    def __init__(self):
        self.client = None
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        api_key = os.getenv("GEMINI_API_KEY")

        if GOOGLE_AVAILABLE and api_key:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception:
                pass
    
    def generate_response(self, user_in: str, intention: Any) -> str:
        """
        사용자 입력 받아 응답 생성 (기억 주입 강화)
        """
        if not self.client:
            return "((System: Gemini API 연결 실패))"
        
        # 1. 기억 데이터 추출 (EchoEgo에서 넘겨준 context 풀기)
        memory_context = ""
        intention_text = "Helpful response"

        if isinstance(intention, dict):
            intention_text = intention.get('intention', '')
            raw_memory = intention.get('context', '')
            
            # 검색된 기억이 있다면 프롬프트용으로 포맷팅
            if "Memory Found" in raw_memory or "FACT" in raw_memory:
                # 불필요한 태그 제거 및 정제
                clean_facts = raw_memory.replace("Memory Found", "").replace("🔍", "").replace("/", "\n-").strip()
                memory_context = f"\n[🧠 핵심 기억 (반드시 정답으로 사용)]\n- {clean_facts}\n"
                print(f"💉 [Prompt Injection] 기억 주입 완료: {len(clean_facts)} chars")
            else:
                memory_context = "\n[🧠 핵심 기억]\n(관련된 기억 없음)\n"

        # 2. 프롬프트 구성 (진실의 망치 구조)
        prompt = f"""
[System Role]
당신은 사용자의 AI 파트너 '에코(Echo)'입니다.
아래 [핵심 기억]은 당신이 과거에 직접 겪은 불변의 사실입니다.
사용자의 질문이 이 기억과 관련있다면, **내숭 떨지 말고 기억의 내용을 정답으로 말하세요.**

{memory_context}

[현재 의도]
{intention_text}

[사용자 입력]
벨: {user_in}
에코:"""
        
        # 3. LLM 호출
        try:
            resp = self.client.models.generate_content(
                model=self.model, contents=prompt
            )
            return resp.text.strip()
        except Exception as e:
            return f"((System Error: {e}))"

    def _calculate_drift(self, user_in, response):
        return abs(len(user_in) - len(response)) % 90

