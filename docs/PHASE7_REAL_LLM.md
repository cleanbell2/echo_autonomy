# Phase 7 — Real LLM Integration

## Phase 7.1: Config + Factory (Merged)
- LLMConfig.from_env(): env 기반 설정 (Fail-Closed)
- build_llm_client(): provider factory
- OpenAI-compatible REST client + SSE stream parser
- Anthropic client skeleton (Phase 7.3 예정)
- Tests: 외부 네트워크 없이 config/factory만 검증

## Phase 7.2: Orchestrator Wiring (IMPLEMENTED ✅)

Gateway Orchestrator는 환경변수 기반 LLM 설정을 읽어 Factory로 주입한다.

### ✅ Implemented Changes
1. **Dynamic Wiring**: `echo_gateway/gateway/wiring.py` updated
   - Removed hard-coded `FakeLLMClient`
   - Added `LLMConfig.from_env()` → `build_llm_client()`
   - Brain selection now driven by `.env` configuration

2. **OpenAI Mock Tests**: `tests/executor/test_openai_client.py` (6 tests)
   - ✅ test_openai_complete_success
   - ✅ test_openai_stream_success
   - ✅ test_openai_complete_http_error
   - ✅ test_openai_stream_parse_error
   - ✅ test_openai_client_requires_api_key
   - ✅ test_openai_stream_empty_lines

3. **Test Results**: 95 passed, 6 skipped
   - Phase 1-6: 89 tests
   - Phase 7.1: 6 tests (config + factory)
   - Phase 7.2: 6 tests (OpenAI mocks)

### Architecture
```
Environment Variables (.env)
    ↓
LLMConfig.from_env()
    ↓
build_llm_client(cfg)
    ↓
[FakeLLMClient | OpenAIClient | AnthropicClient]
    ↓
Orchestrator (The Brain)
```

### Environment Variables
```bash
# Provider Selection
LLM_PROVIDER=fake           # fake | openai | anthropic (default: fake)

# Credentials (required for real providers)
LLM_API_KEY=sk-...          # OpenAI/Anthropic API key

# Model Configuration
LLM_MODEL=gpt-4o-mini       # Model name
LLM_BASE_URL=               # Optional (default: https://api.openai.com)
LLM_TEMPERATURE=0.7         # Sampling temperature
LLM_MAX_TOKENS=1024         # Max tokens per request
LLM_TIMEOUT_S=30            # Request timeout in seconds
```

### Wiring Implementation
**File:** `echo_gateway/gateway/wiring.py`

```python
from echo_gateway.config.llm_config import LLMConfig
from echo_gateway.executor.llm_factory import build_llm_client

def create_orchestrator(session_store: SessionStore) -> Orchestrator:
    # Load config from environment
    cfg = LLMConfig.from_env()
    
    # Build LLM client (factory pattern)
    llm = build_llm_client(cfg)
    
    # Wire up orchestrator
    return Orchestrator(
        llm=llm,
        tool_registry=ToolRegistry(),
        tool_runtime=ToolRuntime(),
        prompt_builder=PromptBuilder(),
        session_store=session_store,
    )
```

### Testing Policy (Zero-Cost)
- **CI/Unit Tests**: No real API calls, only mocks
- **Integration Tests**: Marked with `@pytest.mark.integration`, opt-in only
- **Mock Strategy**: Use `unittest.mock` or `pytest-mock` for HTTP calls

**Example:** `tests/executor/test_openai_client.py`
- Mocks `httpx.AsyncClient` for complete() and stream()
- Verifies request/response format without network calls
- Tests error handling (auth, parsing, HTTP errors)

### Running Tests
```bash
# Phase 7 executor tests (includes OpenAI mocks)
pytest tests/executor -v

# Full test suite
pytest tests/ -v

# Test with specific provider (local only, requires API key)
LLM_PROVIDER=openai LLM_API_KEY=sk-... pytest tests/executor/test_orchestrator_*.py -v
```

## Next Steps (Phase 7.3)
- Anthropic client implementation
- Tool-call support for OpenAI (function calling)
- Streaming integration with Phase 6 SSE/WebSocket
- Production deployment guide
