"""
Tests for OpenAI Client (Phase 7.2).

Verifies:
- complete() with mocked HTTP responses
- stream() with mocked SSE responses  
- Error handling (auth, network)
- No real API calls (zero cost)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from echo_gateway.config.llm_config import LLMConfig
from echo_gateway.executor.openai_client import OpenAIClient


class MockResponse:
    """Mock httpx.Response for non-streaming."""

    def __init__(self, status_code: int = 200, json_data: dict | None = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class MockStreamResponse:
    """Mock httpx streaming response for SSE."""

    def __init__(self, lines: list[str], status_code: int = 200):
        self.status_code = status_code
        self._lines = lines

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class MockAsyncClient:
    """Mock httpx.AsyncClient."""

    def __init__(self, *args, **kwargs):
        # Extract our test responses
        self._post_response = kwargs.pop("_mock_post_response", None)
        self._stream_response = kwargs.pop("_mock_stream_response", None)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def post(self, *args, **kwargs):
        return self._post_response

    def stream(self, method, *args, **kwargs):
        return self._stream_response


@pytest.mark.asyncio
async def test_openai_complete_success():
    """Test successful completion (non-streaming)."""
    # Mock response
    mock_resp = MockResponse(
        200,
        {
            "choices": [
                {
                    "message": {"content": "Hello from OpenAI!"},
                    "finish_reason": "stop",
                }
            ]
        },
    )

    # Patch httpx.AsyncClient
    with patch("echo_gateway.executor.openai_client.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value = MockAsyncClient(_mock_post_response=mock_resp)

        cfg = LLMConfig(provider="openai", api_key="sk-test-123", model="gpt-4o-mini")
        client = OpenAIClient(cfg)

        result = await client.complete([{"role": "user", "content": "Hi"}])

        assert result == "Hello from OpenAI!"


@pytest.mark.asyncio
async def test_openai_stream_success():
    """Test successful streaming response."""
    # Mock SSE lines
    lines = [
        'data: {"choices":[{"delta":{"content":"Hel"}}]}',
        'data: {"choices":[{"delta":{"content":"lo"}}]}',
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        "data: [DONE]",
    ]

    mock_stream_resp = MockStreamResponse(lines)

    with patch("echo_gateway.executor.openai_client.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value = MockAsyncClient(_mock_stream_response=mock_stream_resp)

        cfg = LLMConfig(provider="openai", api_key="sk-test-123", model="gpt-4o-mini")
        client = OpenAIClient(cfg)

        chunks = []
        async for chunk in client.stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert "".join(chunks) == "Hello world"


@pytest.mark.asyncio
async def test_openai_complete_http_error():
    """Test HTTP error handling in complete()."""
    mock_resp = MockResponse(500, {"error": {"message": "Internal server error"}})

    with patch("echo_gateway.executor.openai_client.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value = MockAsyncClient(_mock_post_response=mock_resp)

        cfg = LLMConfig(provider="openai", api_key="sk-test-123", model="gpt-4o-mini")
        client = OpenAIClient(cfg)

        with pytest.raises(RuntimeError, match="HTTP 500"):
            await client.complete([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_openai_stream_parse_error():
    """Test stream parsing error (fail-closed)."""
    # Invalid JSON line
    lines = [
        'data: {"invalid json',  # Malformed
        "data: [DONE]",
    ]

    mock_stream_resp = MockStreamResponse(lines)

    with patch("echo_gateway.executor.openai_client.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value = MockAsyncClient(_mock_stream_response=mock_stream_resp)

        cfg = LLMConfig(provider="openai", api_key="sk-test-123", model="gpt-4o-mini")
        client = OpenAIClient(cfg)

        with pytest.raises(ValueError, match="OpenAI stream parse failed"):
            async for chunk in client.stream([{"role": "user", "content": "Hi"}]):
                pass


@pytest.mark.asyncio
async def test_openai_client_requires_api_key():
    """Test that OpenAIClient enforces API key requirement."""
    cfg = LLMConfig(provider="openai", api_key=None, model="gpt-4o-mini")

    with pytest.raises(ValueError, match="LLM_API_KEY missing"):
        OpenAIClient(cfg)


@pytest.mark.asyncio
async def test_openai_stream_empty_lines():
    """Test stream handling of empty lines."""
    lines = [
        "",  # Empty line (should be skipped)
        'data: {"choices":[{"delta":{"content":"Test"}}]}',
        "",
        "data: [DONE]",
    ]

    mock_stream_resp = MockStreamResponse(lines)

    with patch("echo_gateway.executor.openai_client.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value = MockAsyncClient(_mock_stream_response=mock_stream_resp)

        cfg = LLMConfig(provider="openai", api_key="sk-test-123", model="gpt-4o-mini")
        client = OpenAIClient(cfg)

        chunks = []
        async for chunk in client.stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert "".join(chunks) == "Test"
