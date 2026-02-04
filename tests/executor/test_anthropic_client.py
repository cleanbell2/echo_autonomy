"""
Tests for AnthropicClient adapter.

Focus: Message format translation (system prompt extraction) and streaming.
Strategy: Mock anthropic.AsyncAnthropic to avoid API calls.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from echo_gateway.config.llm_config import LLMConfig
from echo_gateway.executor.anthropic_client import AnthropicClient


@pytest.fixture
def fake_config():
    """Create test config with fake Anthropic credentials"""
    return LLMConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20240620",
        api_key="sk-ant-test-key",
        temperature=0.7,
        max_tokens=2048,
        request_timeout_s=30
    )


@pytest.fixture
def mock_anthropic_response():
    """Mock non-streaming Anthropic response"""
    mock_resp = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "Hello from Claude"
    mock_resp.content = [mock_content]
    mock_resp.stop_reason = "end_turn"
    return mock_resp


@pytest.mark.asyncio
async def test_anthropic_system_prompt_extraction(fake_config, mock_anthropic_response):
    """
    Test: System prompt is extracted from messages and passed as separate parameter.
    
    OpenAI format: [{"role": "system", "content": "..."}, ...]
    Anthropic format: system="...", messages=[...]
    """
    with patch('echo_gateway.executor.anthropic_client.AsyncAnthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create = AsyncMock(return_value=mock_anthropic_response)
        
        client = AnthropicClient(fake_config)
        
        messages = [
            {"role": "system", "content": "You are Echo, a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        
        await client.complete(messages=messages)
        
        # Verify system prompt was extracted
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "You are Echo, a helpful assistant."
        
        # Verify system message was removed from messages list
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"
        assert call_kwargs["messages"][0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_anthropic_complete_success(fake_config, mock_anthropic_response):
    """Test successful non-streaming completion"""
    with patch('echo_gateway.executor.anthropic_client.AsyncAnthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create = AsyncMock(return_value=mock_anthropic_response)
        
        client = AnthropicClient(fake_config)
        
        result = await client.complete(messages=[{"role": "user", "content": "Hi"}])
        
        # Verify unified response format
        assert result["content"] == "Hello from Claude"
        assert result["finish_reason"] == "end_turn"
        assert result["tool_calls"] is None


@pytest.mark.asyncio
async def test_anthropic_complete_no_system_prompt(fake_config, mock_anthropic_response):
    """Test completion without system prompt (should not crash)"""
    with patch('echo_gateway.executor.anthropic_client.AsyncAnthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create = AsyncMock(return_value=mock_anthropic_response)
        
        client = AnthropicClient(fake_config)
        
        messages = [{"role": "user", "content": "Hello"}]
        await client.complete(messages=messages)
        
        call_kwargs = mock_client.messages.create.call_args.kwargs
        
        # System should not be in kwargs if no system message
        assert "system" not in call_kwargs or call_kwargs["system"] is None


@pytest.mark.asyncio
async def test_anthropic_auth_error(fake_config):
    """Test authentication error handling (fail-closed)"""
    from anthropic import AuthenticationError
    
    with patch('echo_gateway.executor.anthropic_client.AsyncAnthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        mock_client.messages.create = AsyncMock(
            side_effect=AuthenticationError(
                message="Invalid API key",
                body=None,
                response=mock_response
            )
        )
        
        client = AnthropicClient(fake_config)
        
        with pytest.raises(ValueError, match="Invalid Anthropic API Key"):
            await client.complete(messages=[{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_anthropic_rate_limit_error(fake_config):
    """Test rate limit error handling"""
    from anthropic import RateLimitError
    
    with patch('echo_gateway.executor.anthropic_client.AsyncAnthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_response = MagicMock()
        mock_response.status_code = 429
        
        mock_client.messages.create = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                body=None,
                response=mock_response
            )
        )
        
        client = AnthropicClient(fake_config)
        
        with pytest.raises(RuntimeError, match="Anthropic Rate Limit Exceeded"):
            await client.complete(messages=[{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_anthropic_streaming_event_translation(fake_config):
    """
    Test streaming event translation from Anthropic format to unified format.
    
    Anthropic events: content_block_delta, message_delta
    Unified format: {"content": str, "tool_calls": None, "finish_reason": str}
    """
    with patch('echo_gateway.executor.anthropic_client.AsyncAnthropic') as MockAnthropic:
        mock_client = MockAnthropic.return_value
        
        # Mock streaming events
        class MockStreamEvent:
            def __init__(self, event_type, delta_data):
                self.type = event_type
                self.delta = MagicMock()
                if event_type == "content_block_delta":
                    self.delta.text = delta_data
                elif event_type == "message_delta":
                    self.delta.stop_reason = delta_data
        
        # Create mock stream context manager
        class MockStream:
            def __init__(self):
                self.events = [
                    MockStreamEvent("content_block_delta", "Hello "),
                    MockStreamEvent("content_block_delta", "Claude!"),
                    MockStreamEvent("message_delta", "end_turn")
                ]
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
            
            async def __aiter__(self):
                for event in self.events:
                    yield event
        
        mock_client.messages.stream = MagicMock(return_value=MockStream())
        
        client = AnthropicClient(fake_config)
        
        # Collect streaming events
        chunks = []
        async for chunk in client.stream(messages=[{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        
        # Verify event translation
        assert len(chunks) == 3
        
        # First delta
        assert chunks[0]["content"] == "Hello "
        assert chunks[0]["tool_calls"] is None
        assert chunks[0]["finish_reason"] is None
        
        # Second delta
        assert chunks[1]["content"] == "Claude!"
        
        # Final event with finish reason
        assert chunks[2]["content"] == ""
        assert chunks[2]["finish_reason"] == "end_turn"


@pytest.mark.asyncio
async def test_anthropic_client_requires_api_key():
    """Test fail-closed: missing API key raises error"""
    config = LLMConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20240620",
        api_key=None  # Missing key
    )
    
    with pytest.raises(ValueError, match="Anthropic API key required"):
        AnthropicClient(config)
