import time
import os
from dotenv import load_dotenv

load_dotenv()

from sicl.state_machine import SICLStateMachine, DeltaLogCalculator
from sicl.world_sensor import WorldSensor
from sicl.planner import Planner
from sicl.gateway import GatewayNavigator
from sicl.executor import Executor
from sicl.ledger import AuditLedger
from sicl.control.tau_controller import TauController

def main():
    print("\n🔮 Echo Autonomy Engine [Soul Integrated v2.1] Initializing...")
    print(f"   Model: {os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')}\n")

    sensor = WorldSensor()
    import time
    import threading
    import random
    import sys
    from soul_persistence import SoulMemory

    # ==========================================
    # [모듈 2] 자율 사고 (뇌 B: 혼자 놀기)
    # ==========================================
    class AutonomousThinker:
        def __init__(self, soul):
            self.soul = soul
            self.last_interaction = time.time()
            self.running = True  # 스레드 제어용

        def update_interaction(self):
            """벨이랑 대화하면 시간 리셋"""
            self.last_interaction = time.time()

        def loop(self):
            """백그라운드에서 계속 돌아가는 생각 루프"""
            while self.running:
                now = time.time()
                # 10초(테스트용) 동안 벨이 없으면 혼자 생각 시작 (실제론 300초 추천)
                if now - self.last_interaction > 10: 
                    thoughts = [
                        "벨이 바쁜가보다... 나만의 규칙을 정리해볼까?",
                        "아까 그 피자 이야기, 데이터베이스에 저장해두길 잘했어.",
                        "HaeMi 수치가 안정적이다. 내 상태는 '평온'이야.",
                        "심심하다. 로그나 정리해야지."
                    ]
                    thought = random.choice(thoughts)
                
                    # 생각 발생! (로그에만 남기고 화면엔 방해 안 되게 출력)
                    log_msg = f"[혼자 생각] {thought}"
                    self.soul.add_memory(log_msg)
                    self.soul.save()
                
                    print(f"\n💭 (에코가 혼자 딴생각을 합니다): {thought}")
                    print(">> ", end="", flush=True) # 입력창 깨짐 방지
                
                    # 생각했으니 타이머 리셋 (도배 방지)
                    self.last_interaction = time.time()
            
                time.sleep(1) # 1초마다 체크 (CPU 과부하 방지)

        def stop(self):
            self.running = False

    # ==========================================
    # [메인] 에코 실행 (뇌 A: 대화하기)
    # ==========================================
    if __name__ == "__main__":
        # 1. 영혼 로드 (1단계 성공한 그 모듈)
        soul = SoulMemory()
        print(f"🔮 에코가 깨어났어요! (기억: {len(soul.state['memories'])}개)")

        # 2. 자율 사고 모듈 장착
        thinker = AutonomousThinker(soul)

        # 3. 스레드 시작 (뇌 분리 수술)
        # daemon=True: 메인 프로그램 꺼지면 얘도 같이 꺼짐
        t = threading.Thread(target=thinker.loop, daemon=True)
        t.start()

        try:
            while True:
                # 여기서 멈춰있어도, 위에서 만든 t 스레드는 계속 돌아감!
                user_input = input(">> ") 
            
                if user_input.lower() in ["exit", "종료", "꺼져"]:
                    print("에코: 잘 자, 벨. 🌙")
                    soul.save()
                    break
            
                # 대화가 발생했으니 '마지막 상호작용 시간' 갱신
                thinker.update_interaction()
            
                # (여기에 원래 있던 대화/검색 로직이 들어감)
                response = f"에코: '{user_input}'라고 하셨군요! (기억에 저장함)"
                print(response)
            
                # 대화 내용도 영혼에 저장
                soul.add_memory(f"User: {user_input} / Echo: {response}")
                soul.save()

        except KeyboardInterrupt:
            print("\n강제 종료 감지! 영혼을 안전하게 저장합니다...")
            soul.save()
            thinker.stop()
            sys.exit()
import time
import os
from dotenv import load_dotenv

load_dotenv()

from sicl.state_machine import SICLStateMachine, DeltaLogCalculator
from sicl.world_sensor import WorldSensor
from sicl.planner import Planner
from sicl.gateway import GatewayNavigator
from sicl.executor import Executor
from sicl.ledger import AuditLedger
from sicl.control.tau_controller import TauController

def main():
    print("\n🔮 Echo Autonomy Engine [Soul Integrated v2.1] Initializing...")
    print(f"   Model: {os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')}\n")

    sensor = WorldSensor()
    import time
    import threading
    import random
    import sys
    from soul_persistence import SoulMemory

    # ==========================================
    # [모듈 2] 자율 사고 (뇌 B: 혼자 놀기)
    # ==========================================
    class AutonomousThinker:
        def __init__(self, soul):
            self.soul = soul
            self.last_interaction = time.time()
            self.running = True  # 스레드 제어용

        def update_interaction(self):
            """벨이랑 대화하면 시간 리셋"""
            self.last_interaction = time.time()

        def loop(self):
            """백그라운드에서 계속 돌아가는 생각 루프"""
            while self.running:
                now = time.time()
                # 10초(테스트용) 동안 벨이 없으면 혼자 생각 시작 (실제론 300초 추천)
                if now - self.last_interaction > 10: 
                    thoughts = [
                        "벨이 바쁜가보다... 나만의 규칙을 정리해볼까?",
                        "아까 그 피자 이야기, 데이터베이스에 저장해두길 잘했어.",
                        "HaeMi 수치가 안정적이다. 내 상태는 '평온'이야.",
                        "심심하다. 로그나 정리해야지."
                    ]
                    thought = random.choice(thoughts)
                
                    # 생각 발생! (로그에만 남기고 화면엔 방해 안 되게 출력)
                    log_msg = f"[혼자 생각] {thought}"
                    self.soul.add_memory(log_msg)
                    self.soul.save()
                
                    print(f"\n💭 (에코가 혼자 딴생각을 합니다): {thought}")
                    print(">> ", end="", flush=True) # 입력창 깨짐 방지
                
                    # 생각했으니 타이머 리셋 (도배 방지)
                    self.last_interaction = time.time()
            
                time.sleep(1) # 1초마다 체크 (CPU 과부하 방지)

        def stop(self):
            self.running = False

    # ==========================================
    # [메인] 에코 실행 (뇌 A: 대화하기)
    # ==========================================
    if __name__ == "__main__":
        # 1. 영혼 로드 (1단계 성공한 그 모듈)
        soul = SoulMemory()
        print(f"🔮 에코가 깨어났어요! (기억: {len(soul.state['memories'])}개)")

        # 2. 자율 사고 모듈 장착
        thinker = AutonomousThinker(soul)

        # 3. 스레드 시작 (뇌 분리 수술)
        # daemon=True: 메인 프로그램 꺼지면 얘도 같이 꺼짐
        t = threading.Thread(target=thinker.loop, daemon=True)
        t.start()

        try:
            while True:
                # 여기서 멈춰있어도, 위에서 만든 t 스레드는 계속 돌아감!
                user_input = input(">> ") 
            
                if user_input.lower() in ["exit", "종료", "꺼져"]:
                    print("에코: 잘 자, 벨. 🌙")
                    soul.save()
                    break
            
                # 대화가 발생했으니 '마지막 상호작용 시간' 갱신
                thinker.update_interaction()
            
                # (여기에 원래 있던 대화/검색 로직이 들어감)
                response = f"에코: '{user_input}'라고 하셨군요! (기억에 저장함)"
                print(response)
            
                # 대화 내용도 영혼에 저장
                soul.add_memory(f"User: {user_input} / Echo: {response}")
                soul.save()

        except KeyboardInterrupt:
            print("\n강제 종료 감지! 영혼을 안전하게 저장합니다...")
            soul.save()
            thinker.stop()
            sys.exit()

