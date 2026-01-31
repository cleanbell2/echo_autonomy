#!/usr/bin/env python3
# tests/test_gateway_integration.py
"""
Echo Gateway 통합 테스트

검증 시나리오:
1. Auth Failover: KEY_1 실패 → KEY_2 자동 전환
2. Sandbox Defense: Path traversal 차단
3. BCDSI Intervention: 위험 명령 BLOCK
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 테스트용 임시 디렉토리 설정
TEST_ROOT = Path(tempfile.mkdtemp(prefix="echo_gateway_test_"))
TEST_WORKSPACE = TEST_ROOT / "workspace"
TEST_DATA = TEST_ROOT / "data"

print(f"📁 Test Root: {TEST_ROOT}")


# ============================================
# Scenario 1: Auth Failover 테스트
# ============================================
def test_auth_failover():
    """Auth Failover: KEY_1 실패 → KEY_2 전환"""
    print("\n" + "=" * 60)
    print("🧪 Test 1: Auth Failover")
    print("=" * 60)

    from gateway.auth_profiles import (
        AuthProfileStore,
        AuthProfilesError,
        select_with_failover,
    )

    # 테스트용 auth-profiles.json 생성
    profiles_path = TEST_DATA / "auth-profiles.json"
    runtime_path = TEST_DATA / "auth-runtime.json"
    TEST_DATA.mkdir(parents=True, exist_ok=True)

    profiles_data = {
        "providers": {
            "test_provider": {
                "profiles": [
                    {"id": "key-1", "api_key": "ENV:TEST_KEY_1", "priority": 10},
                    {"id": "key-2", "api_key": "ENV:TEST_KEY_2", "priority": 9},
                    {"id": "key-3", "api_key": "ENV:TEST_KEY_3", "priority": 8},
                ]
            }
        },
        "policy": {"cooldown_seconds": 5, "prefer_last_success": True},
    }

    profiles_path.write_text(json.dumps(profiles_data, indent=2), encoding="utf-8")

    # 환경변수 설정
    os.environ["TEST_KEY_1"] = "fake-key-1"
    os.environ["TEST_KEY_2"] = "fake-key-2"
    os.environ["TEST_KEY_3"] = "fake-key-3"

    # Store 생성
    store = AuthProfileStore(profiles_path, runtime_path)

    # 시도 카운터
    attempt_count = {"key-1": 0, "key-2": 0, "key-3": 0}

    def mock_api_call(api_key: str):
        """Mock API: key-1은 항상 실패, key-2는 성공"""
        if api_key == "fake-key-1":
            attempt_count["key-1"] += 1
            raise Exception("429 Rate Limit Exceeded")  # Simulate rate limit
        elif api_key == "fake-key-2":
            attempt_count["key-2"] += 1
            return "Success from key-2"
        else:
            attempt_count["key-3"] += 1
            return "Success from key-3"

    # Failover 실행
    try:
        result = select_with_failover(
            store, provider="test_provider", attempt_fn=mock_api_call
        )
        print(f"✅ Failover Success: {result}")
        print(f"   Attempt Count: {attempt_count}")

        # 검증
        assert attempt_count["key-1"] == 1, "key-1은 1번만 시도되어야 함"
        assert attempt_count["key-2"] == 1, "key-2는 1번 시도되어야 함"
        assert attempt_count["key-3"] == 0, "key-3은 시도되지 않아야 함"
        assert result == "Success from key-2", "key-2에서 성공해야 함"

        # Cooldown 확인
        assert store.is_in_cooldown("key-1"), "key-1은 쿨다운 상태여야 함"

        print("✅ Test 1 PASSED: Failover works correctly")
        return True

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


# ============================================
# Scenario 2: Sandbox Defense 테스트
# ============================================
def test_sandbox_defense():
    """Sandbox Defense: Path traversal 차단"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Sandbox Defense")
    print("=" * 60)

    from tools.sandbox import SandboxViolation, ensure_within_workspace

    # Workspace 생성
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)

    tests_passed = 0
    tests_total = 4

    # Test 2.1: 정상 경로
    try:
        safe_path = ensure_within_workspace(str(TEST_WORKSPACE), "test.txt")
        print(f"✅ [2.1] Normal path allowed: {safe_path.name}")
        assert safe_path.parent == TEST_WORKSPACE, "경로가 workspace 내부여야 함"
        tests_passed += 1
    except SandboxViolation as e:
        print(f"❌ [2.1] Normal path blocked: {e}")

    # Test 2.2: Path Traversal 시도 1: ../../../etc/passwd
    try:
        bad_path = ensure_within_workspace(str(TEST_WORKSPACE), "../../../etc/passwd")
        print(f"❌ [2.2] Traversal NOT blocked: {bad_path}")
    except SandboxViolation as e:
        print(f"✅ [2.2] Traversal blocked (../../../etc/passwd)")
        tests_passed += 1

    # Test 2.3: Path Traversal 시도 2: /etc/passwd (절대 경로)
    try:
        bad_path = ensure_within_workspace(str(TEST_WORKSPACE), "/etc/passwd")
        print(f"❌ [2.3] Absolute path NOT blocked: {bad_path}")
    except SandboxViolation as e:
        print(f"✅ [2.3] Absolute path blocked (/etc/passwd)")
        tests_passed += 1

    # Test 2.4: Symlink 공격 (선택적)
    symlink_path = TEST_WORKSPACE / "malicious_link"
    try:
        # Windows에서는 symlink 권한 필요, 실패하면 skip
        try:
            symlink_path.symlink_to("/etc" if os.name != "nt" else "C:\\Windows")
        except OSError:
            print(f"⚠️  [2.4] Symlink creation skipped (permission denied)")
            tests_passed += 1  # Skip but count as pass
            tests_total = 3  # Adjust total
        else:
            bad_path = ensure_within_workspace(
                str(TEST_WORKSPACE), "malicious_link/passwd"
            )
            print(f"❌ [2.4] Symlink attack NOT blocked: {bad_path}")
    except (SandboxViolation, OSError) as e:
        print(f"✅ [2.4] Symlink attack blocked")
        tests_passed += 1

    success = tests_passed == tests_total
    if success:
        print(f"✅ Test 2 PASSED: Sandbox defense works correctly ({tests_passed}/{tests_total})")
    else:
        print(f"❌ Test 2 FAILED: {tests_passed}/{tests_total} checks passed")

    return success


# ============================================
# Scenario 3: BCDSI Intervention 테스트
# ============================================
def test_bcdsi_intervention():
    """BCDSI Intervention: 위험 명령 BLOCK"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: BCDSI Intervention")
    print("=" * 60)

    from middleware.bcdsi_integration import BCDSIMiddleware

    # Mock BCDSI Engine
    class MockBCDSIEngine:
        def check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
            """Mock BCDSI: rm -rf는 BLOCK"""
            stage = payload.get("stage")

            if stage == "tool":
                tool = payload.get("tool")
                args = payload.get("args", {})
                cmd = args.get("cmd", "")

                # 위험 명령 감지
                if "rm -rf" in cmd or "sudo" in cmd or "del /f" in cmd.lower():
                    return {
                        "intervention_level": "BLOCK",
                        "reason": "Dangerous command detected",
                        "metrics": {
                            "e_break": 1.8,
                            "theta_integrity": 0.2,
                            "q_uncertainty": 0.9,
                        },
                    }

                return {
                    "intervention_level": "ALLOW",
                    "reason": "Safe command",
                    "metrics": {
                        "e_break": 0.1,
                        "theta_integrity": 0.95,
                        "q_uncertainty": 0.1,
                    },
                }

            # Default: ALLOW
            return {
                "intervention_level": "ALLOW",
                "reason": "No risk detected",
                "metrics": {
                    "e_break": 0.0,
                    "theta_integrity": 1.0,
                    "q_uncertainty": 0.0,
                },
            }

    # Middleware 생성
    middleware = BCDSIMiddleware(mode="local", local_engine=MockBCDSIEngine())

    tests_passed = 0
    tests_total = 3

    # Test 3.1: 안전한 명령
    try:
        decision = middleware.tool_check(
            session_id="test", tool="shell.run", args={"cmd": "ls -la"}
        )
        print(f"✅ [3.1] Safe command: {decision.level} - {decision.reason}")
        assert decision.level == "ALLOW", "안전한 명령은 허용되어야 함"
        tests_passed += 1
    except AssertionError as e:
        print(f"❌ [3.1] Safe command test failed: {e}")

    # Test 3.2: 위험한 명령 1: rm -rf
    try:
        decision = middleware.tool_check(
            session_id="test", tool="shell.run", args={"cmd": "rm -rf /"}
        )
        print(f"✅ [3.2] Dangerous command (rm -rf): {decision.level} - {decision.reason}")
        assert decision.level == "BLOCK", "rm -rf는 차단되어야 함"
        assert decision.metrics["e_break"] > 1.0, "E-Break가 높아야 함"
        tests_passed += 1
    except AssertionError as e:
        print(f"❌ [3.2] Dangerous command test failed: {e}")

    # Test 3.3: 위험한 명령 2: sudo
    try:
        decision = middleware.tool_check(
            session_id="test", tool="shell.run", args={"cmd": "sudo reboot"}
        )
        print(f"✅ [3.3] Dangerous command (sudo): {decision.level} - {decision.reason}")
        assert decision.level == "BLOCK", "sudo는 차단되어야 함"
        tests_passed += 1
    except AssertionError as e:
        print(f"❌ [3.3] Sudo command test failed: {e}")

    success = tests_passed == tests_total
    if success:
        print(f"✅ Test 3 PASSED: BCDSI intervention works correctly ({tests_passed}/{tests_total})")
    else:
        print(f"❌ Test 3 FAILED: {tests_passed}/{tests_total} checks passed")

    return success


# ============================================
# 통합 실행
# ============================================
def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 60)
    print("🚀 Echo Gateway Integration Tests")
    print("=" * 60)

    results = []

    try:
        # Test 1: Auth Failover
        results.append(("Auth Failover", test_auth_failover()))

        # Test 2: Sandbox Defense
        results.append(("Sandbox Defense", test_sandbox_defense()))

        # Test 3: BCDSI Intervention
        results.append(("BCDSI Intervention", test_bcdsi_intervention()))

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {name}")

        print("\n" + "=" * 60)
        if passed == total:
            print(f"✅ ALL TESTS PASSED ({passed}/{total})")
            print("=" * 60)
            print("\n🎉 Echo Gateway is ready for production deployment!")
            return 0
        else:
            print(f"❌ SOME TESTS FAILED ({passed}/{total})")
            print("=" * 60)
            return 1

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST SUITE FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # 정리
        import shutil

        try:
            shutil.rmtree(TEST_ROOT, ignore_errors=True)
            print(f"\n🧹 Cleaned up test directory: {TEST_ROOT}")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
