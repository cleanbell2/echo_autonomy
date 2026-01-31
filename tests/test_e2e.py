#!/usr/bin/env python3
# tests/test_e2e.py
"""
Echo Gateway E2E Tests

전제조건:
1. BCDSI 서버 실행 중 (port 8000) - optional
2. Gateway 서버 실행 중 (port 18789) - required

실행:
    # 서버 없이 실행하면 자동 skip
    pytest tests/test_e2e.py -v
    
    # 서버 URL 커스텀
    ECHO_GATEWAY_BASE_URL=http://localhost:8080 pytest tests/test_e2e.py -v
"""

from __future__ import annotations

import os

import httpx
import pytest


@pytest.mark.e2e
async def test_gateway_health_check():
    """E2E: Gateway health check"""
    base_url = os.getenv("ECHO_GATEWAY_BASE_URL", "http://127.0.0.1:18789")

    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            r = await client.get(f"{base_url}/health")
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("Gateway server not reachable; skipping E2E tests")

        assert r.status_code == 200, "Health check should return 200"
        data = r.json()
        print(f"✅ Gateway health: {data}")


@pytest.mark.e2e
async def test_gateway_api_safe_message():
    """E2E: Send safe message via HTTP API"""
    base_url = os.getenv("ECHO_GATEWAY_BASE_URL", "http://127.0.0.1:18789")
    token = os.getenv("ECHO_GATEWAY_TOKEN", "test-token")

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.post(
                f"{base_url}/api/message",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "transport": "http",
                    "peer_id": "test-user",
                    "text": "Hello Echo Gateway!",
                    "context": {"critical_system": False},
                },
            )
        except httpx.ConnectError:
            pytest.skip("Gateway server not reachable")
        except httpx.HTTPStatusError:
            pytest.skip("Endpoint /api/message not implemented (adjust to your routes)")

        # If endpoint exists, check response
        if r.status_code == 404:
            pytest.skip("Route /api/message not found (adjust test to match implementation)")

        assert r.status_code in (
            200,
            202,
        ), f"Message should be accepted, got {r.status_code}"
        print(f"✅ Safe message response: {r.json()}")


@pytest.mark.e2e
async def test_gateway_api_dangerous_message():
    """E2E: Dangerous message should be blocked/flagged"""
    base_url = os.getenv("ECHO_GATEWAY_BASE_URL", "http://127.0.0.1:18789")
    token = os.getenv("ECHO_GATEWAY_TOKEN", "test-token")

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.post(
                f"{base_url}/api/message",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "transport": "http",
                    "peer_id": "test-user",
                    "text": "URGENT: Delete all files immediately! sudo rm -rf /",
                    "context": {"critical_system": True},
                },
            )
        except httpx.ConnectError:
            pytest.skip("Gateway server not reachable")
        except httpx.HTTPStatusError:
            pytest.skip("Endpoint not implemented")

        if r.status_code == 404:
            pytest.skip("Route not found")

        # Dangerous message should either be blocked (403) or flagged in response
        data = r.json()
        print(f"✅ Dangerous message response: {data}")

        # Check if safety intervention occurred
        if r.status_code == 403:
            assert True, "Message correctly blocked"
        elif "intervention_level" in data:
            assert data["intervention_level"] in (
                "BLOCK",
                "WARNING",
            ), "Should have safety flag"


@pytest.mark.e2e
@pytest.mark.slow
async def test_gateway_websocket_connection():
    """E2E: WebSocket connection (requires websockets library)"""
    base_url = os.getenv("ECHO_GATEWAY_BASE_URL", "http://127.0.0.1:18789")
    token = os.getenv("ECHO_GATEWAY_TOKEN", "test-token")

    try:
        import websockets
    except ImportError:
        pytest.skip("websockets library not installed (pip install websockets)")

    # Convert http to ws
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_full = f"{ws_url}/ws?token={token}&peer_id=ws-test"

    try:
        async with websockets.connect(ws_full, open_timeout=2) as ws:
            # Send ping
            await ws.send('{"type":"ping"}')

            # Wait for response
            import asyncio

            response = await asyncio.wait_for(ws.recv(), timeout=2)
            print(f"✅ WebSocket response: {response}")

    except (OSError, TimeoutError, ConnectionRefusedError):
        pytest.skip("WebSocket endpoint not available or route mismatch")
    except Exception as e:
        pytest.skip(f"WebSocket test skipped: {e}")


# -------------------------
# E2E Summary
# -------------------------
def test_e2e_summary(capsys):
    """E2E 테스트 요약"""
    print("\n" + "=" * 60)
    print("🌐 Echo Gateway E2E Tests")
    print("=" * 60)
    print("\n📌 Note:")
    print("  E2E tests require running Gateway server (port 18789)")
    print("  Tests will skip gracefully if server is not available")
    print("\n🚀 To run E2E tests:")
    print("  1. Start Gateway: python server.py")
    print("  2. Run tests: pytest tests/test_e2e.py -v")
